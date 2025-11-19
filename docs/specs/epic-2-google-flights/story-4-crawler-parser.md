---
title: "Story 4: Crawler & Parser (Proof of Concept Google Flights 1 destination)"
epic: "Epic 2: Google Flights Integration"
story_points: 8
dependencies: ["story-1", "story-2", "story-3"]
date: "2025-11-19"
keywords: ["crawler", "parser", "crawl4ai", "google-flights", "scraping", "stealth-mode", "decodo-proxies", "jsoncssstrategy", "captcha-detection", "pydantic", "proof-of-concept"]
scope: ["specs"]
technologies: ["crawl4ai", "playwright", "pydantic", "decodo", "tenacity"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Proof of Concept technique** : Valider la faisabilité du scraping Google Flights pour une destination unique avant d'implémenter la logique multi-destinations complexe
- **Dérisquage early** : Identifier les blocages Google (captchas, rate limiting, anti-bot) dès la Story 4 plutôt qu'à la Story 5-6 (économie temps développement)
- **Foundation scraping** : Établir les patterns réutilisables (CrawlerService + FlightParser) pour toutes les stories suivantes (5, 6, 7)
- **Validation stack technique** : Prouver que Crawl4AI + Decodo Proxies + JsonCssExtractionStrategy suffisent pour extraire des données structurées sans LLM

## Contraintes métier

- **Anti-détection Google Flights** : Google utilise Cloudflare/DataDome pour détecter et bloquer les bots (nécessite stealth mode + proxies résidentiels Decodo)
- **Captcha detection MVP** : Phase MVP = détection uniquement (logging + retry avec rotation IP), pas de résolution automatique (2Captcha réservé Phase 7 optionnelle si taux blocage >5%)
- **Bandwidth Decodo limité** : Proxies résidentiels facturés au GB ($2.60-3.50/GB selon volume), minimiser le nombre de requêtes et taille HTML téléchargé
- **Pas de Database** : Résultats en mémoire uniquement (pas de persistence), focus sur extraction et transformation données
- **Structure HTML Google Flights non documentée** : Sélecteurs CSS peuvent changer sans préavis, nécessite monitoring et robustesse parsing

## Valeur business

- ✅ **Validation technique early** : Confirme faisabilité scraping Google Flights avant investissement stories multi-destinations (désengagement rapide si bloqué)
- ✅ **Feedback qualité données** : Valide que les champs extraits (prix, compagnie, horaires, durée, escales) sont suffisants et correctement formatés pour ranking futur
- ✅ **Foundation services réutilisables** : CrawlerService et FlightParser deviennent les building blocks des stories 5-6 (gain vélocité 30-40%)
- ✅ **Métriques observables** : Établit baseline de performance (taux succès crawl, temps réponse, taux captcha détecté) pour optimisation continue
- ✅ **Réduction risque budget** : Valide coûts bandwidth Decodo réels vs estimations avant scaling multi-destinations

## Métriques succès

- **Taux succès crawl** : ≥85% de requêtes Google Flights retournent HTML valide (status 200, pas de captcha)
- **Temps réponse crawl** : ≤10 secondes par URL Google Flights (P95 percentile, incluant retry logic)
- **Taux captcha détecté** : ≤5% de requêtes bloquées par reCAPTCHA/hCaptcha (target MVP)
- **Taux parsing réussi** : ≥95% de HTML valides parsés avec succès (minimum 5 vols extraits par recherche)
- **Qualité extraction** : 100% des champs obligatoires (price, airline, departure_time, arrival_time, duration) présents et valides selon schéma Pydantic
- **Coverage tests** : ≥80% sur CrawlerService et FlightParser (unitaires + intégration)

---

# 📋 Spécifications Techniques

## 1. CrawlerService

**Rôle** : Orchestrer le crawling Google Flights avec Crawl4AI, gérer le stealth mode, la rotation de proxies Decodo, et la détection de captchas avec retry logic.

**Interface** :
```python
from typing import Dict, Any
from crawl4ai import CrawlResult

class CrawlerService:
    """Service de crawling Google Flights avec stealth mode et proxy rotation."""

    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True,
        max_retries: int = 3
    ) -> CrawlResult:
        """
        Crawl une URL Google Flights avec retry logic et captcha detection.

        Raises:
            CaptchaDetectedError: Si captcha détecté après max_retries
            NetworkError: Si erreur réseau persistante après max_retries
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `url` | `str` | URL Google Flights complète avec paramètres query | Format `https://www.google.com/travel/flights?...` |
| `use_proxy` | `bool` | Active rotation proxies Decodo | Default `True`, `False` pour dev local |
| `max_retries` | `int` | Nombre maximum de tentatives avec rotation IP | Default `3`, range `1-5` |

**Comportement** :

- **Crawl nominal** :
  1. Initialise AsyncWebCrawler avec BrowserConfig (stealth mode, proxy Decodo si `use_proxy=True`)
  2. Exécute `crawler.arun(url)` avec timeout 10s
  3. Vérifie status code 200 et absence de captcha dans HTML
  4. Retourne CrawlResult avec `html`, `cleaned_html`, `success=True`

- **Edge cases** :
  - **Captcha détecté** : Si HTML contient patterns reCAPTCHA/hCaptcha → Lève `CaptchaDetectedError` avec URL et proxy utilisé
  - **Status code 403/429** : Rate limiting Google → Retry avec rotation proxy et exponential backoff (4s, 8s, 16s)
  - **Timeout réseau** : Si `arun()` timeout après 10s → Retry avec nouveau proxy
  - **Max retries dépassé** : Lève `NetworkError` avec détails des tentatives échouées

- **Erreurs levées** :
  - `CaptchaDetectedError` : Hérité de `Exception`, contient `url`, `proxy_used`, `captcha_type` (recaptcha_v2/v3/hcaptcha)
  - `NetworkError` : Hérité de `Exception`, contient `url`, `status_code`, `attempts`

- **Logging structuré** :
  - INFO : Début crawl avec URL et proxy utilisé
  - WARNING : Captcha détecté (tentative N/max_retries) + rotation proxy
  - ERROR : Max retries atteint, crawl échoué
  - DEBUG : HTML size, temps réponse, status code

---

## 2. FlightParser

**Rôle** : Extraire les données structurées de vols depuis le HTML Google Flights via JsonCssExtractionStrategy (sans LLM), valider avec Pydantic, et retourner une liste de modèles Flight.

**Interface** :
```python
from typing import List
from app.models.response import Flight

class FlightParser:
    """Parser de vols Google Flights via JsonCssExtractionStrategy."""

    def parse(self, html: str) -> List[Flight]:
        """
        Extrait les vols depuis HTML Google Flights.

        Raises:
            ParsingError: Si aucun vol extrait ou HTML invalide
            ValidationError: Si validation Pydantic échoue
        """
```

**Schema CSS Extraction** :

```json
{
  "name": "Google Flights Extractor",
  "baseSelector": ".pIav2d",
  "fields": [
    {
      "name": "price",
      "selector": ".FpEdX span:first-child",
      "type": "text"
    },
    {
      "name": "airline",
      "selector": ".sSHqwe",
      "type": "text"
    },
    {
      "name": "departure_time",
      "selector": ".vmXl time",
      "type": "attribute",
      "attribute": "datetime"
    },
    {
      "name": "arrival_time",
      "selector": ".XWcVob time",
      "type": "attribute",
      "attribute": "datetime"
    },
    {
      "name": "duration",
      "selector": ".gvkrdb",
      "type": "text"
    },
    {
      "name": "stops",
      "selector": ".BbR8Ec .ogfYpf",
      "type": "text"
    },
    {
      "name": "departure_airport",
      "selector": ".G2WY5c .sSHqwe:first-child",
      "type": "text"
    },
    {
      "name": "arrival_airport",
      "selector": ".G2WY5c .sSHqwe:last-child",
      "type": "text"
    }
  ]
}
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `html` | `str` | HTML brut Google Flights | Non vide, min_length > 1000 caractères |
| **Retour** | `List[Flight]` | Liste vols extraits et validés | Minimum 1 vol, maximum 50 vols |

**Comportement** :

- **Extraction nominale** :
  1. Instancie JsonCssExtractionStrategy avec schema CSS ci-dessus
  2. Applique stratégie sur HTML avec `extraction_strategy.extract(html)`
  3. Transforme chaque élément extrait en modèle Flight via Pydantic
  4. Valide automatiquement champs obligatoires (price, airline, departure_time, arrival_time)
  5. Retourne liste de Flight validés

- **Edge cases** :
  - **Champs manquants** : Si prix/compagnie/horaires absents dans HTML → Skip vol (log WARNING) et continue parsing vols suivants
  - **Prix invalide** : Si prix contient caractères non numériques (ex: "N/A") → Skip vol
  - **HTML malformed** : Si baseSelector `.pIav2d` ne matche aucun élément → Lève `ParsingError("No flights found in HTML")`
  - **Liste vide après parsing** : Si aucun vol valide extrait → Lève `ParsingError("Zero valid flights extracted")`

- **Validation Pydantic** :
  - `price` : `float`, valeur > 0
  - `airline` : `str`, min_length=2, max_length=100
  - `departure_time` : `datetime`, format ISO 8601 strict
  - `arrival_time` : `datetime`, format ISO 8601, après departure_time
  - `duration` : `str`, format "Xh Ymin" (ex: "10h 30min")
  - `stops` : `int | None`, valeur ≥0, None si "Non-stop"

- **Erreurs levées** :
  - `ParsingError` : Hérité de `Exception`, contient `html_size`, `flights_found`
  - `ValidationError` : Pydantic standard, contient détails champs invalides

---

## 3. Modèle Flight (Pydantic)

**Rôle** : Représenter un vol extrait avec validation automatique des types et contraintes métier.

**Interface** :
```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class Flight(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    price: float = Field(..., gt=0, description="Prix en euros")
    airline: str = Field(..., min_length=2, max_length=100)
    departure_time: datetime
    arrival_time: datetime
    duration: str = Field(..., pattern=r"^\d+h \d+min$")
    stops: int | None = Field(None, ge=0)
    departure_airport: str | None = Field(None, max_length=10)
    arrival_airport: str | None = Field(None, max_length=10)

    @field_validator('arrival_time', mode='after')
    @classmethod
    def arrival_after_departure(cls, v: datetime, info) -> datetime:
        """Valide que arrival_time > departure_time."""
```

**Validations** :
- `field_validator` : Vérifie cohérence temporelle (arrival_time après departure_time)
- `pattern` : Format durée strict "Xh Ymin" via regex
- `gt=0` : Prix strictement positif

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CrawlerService (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_crawl_success_without_proxy` | Crawl réussi sans proxy (dev mode) | `url="https://google.com/travel/flights?..."`, `use_proxy=False` | `result.success == True`, `result.html` non vide | Vérifie comportement nominal sans proxy |
| 2 | `test_crawl_success_with_proxy` | Crawl réussi avec proxy Decodo | `url=URL_GOOGLE_FLIGHTS`, `use_proxy=True` | `result.success == True`, proxy utilisé loggé | Vérifie configuration proxy Decodo |
| 3 | `test_crawl_recaptcha_v2_detection` | HTML contient reCAPTCHA v2 | Mock HTML avec `<div class="g-recaptcha">` | Lève `CaptchaDetectedError`, `captcha_type="recaptcha_v2"` | Vérifie détection pattern reCAPTCHA |
| 4 | `test_crawl_hcaptcha_detection` | HTML contient hCaptcha | Mock HTML avec `<div class="h-captcha">` | Lève `CaptchaDetectedError`, `captcha_type="hcaptcha"` | Vérifie détection pattern hCaptcha |
| 5 | `test_crawl_retry_on_captcha` | Captcha détecté, retry avec rotation proxy | 1ère tentative captcha, 2ème succès | `result.success == True`, 2 proxies différents utilisés | Vérifie retry logic avec rotation IP |
| 6 | `test_crawl_max_retries_exceeded` | Max retries atteint, tous captcha | 3 tentatives, toutes avec captcha | Lève `CaptchaDetectedError` final | Vérifie abandon après max_retries |
| 7 | `test_crawl_network_timeout` | Timeout réseau AsyncWebCrawler | Mock `arun()` timeout après 10s | Lève `NetworkError`, `status_code=None` | Vérifie gestion timeout |
| 8 | `test_crawl_status_403_retry` | Status code 403 (rate limiting) | Mock response status 403 | Retry avec exponential backoff 4s, 8s, 16s | Vérifie retry logic sur 403 |
| 9 | `test_crawl_stealth_mode_enabled` | BrowserConfig avec stealth mode actif | `enable_stealth=True` dans config | `result.success == True`, stealth mode loggé | Vérifie activation stealth mode |
| 10 | `test_crawl_structured_logging` | Logging structuré avec contexte | Crawl avec URL et proxy | Logs contiennent `url`, `proxy_used`, `status_code`, `html_size` | Vérifie qualité logging JSON |

### FlightParser (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_parse_valid_html_multiple_flights` | HTML valide avec 10 vols | Mock HTML avec 10 `.pIav2d` valides | `len(flights) == 10`, tous Flight valides | Vérifie extraction nominale |
| 2 | `test_parse_flight_all_fields_present` | Vol avec tous champs renseignés | HTML avec price, airline, times, duration, stops, airports | `flight.price > 0`, tous champs non None | Vérifie mapping complet champs |
| 3 | `test_parse_missing_price` | Vol sans prix | HTML avec airline mais sans `.FpEdX` | Vol skippé, log WARNING | Vérifie robustesse champ obligatoire manquant |
| 4 | `test_parse_invalid_price_format` | Prix non numérique | HTML avec price="N/A" | Vol skippé, log WARNING | Vérifie validation format prix |
| 5 | `test_parse_missing_airline` | Vol sans compagnie | HTML avec price mais sans `.sSHqwe` | Vol skippé, log WARNING | Vérifie robustesse champ obligatoire manquant |
| 6 | `test_parse_invalid_datetime_format` | Horaire invalide | HTML avec `datetime="invalid"` | Lève `ValidationError` Pydantic | Vérifie validation datetime strict |
| 7 | `test_parse_arrival_before_departure` | arrival_time < departure_time | HTML avec horaires incohérents | Lève `ValidationError` via `field_validator` | Vérifie validation cohérence temporelle |
| 8 | `test_parse_no_flights_found` | HTML sans `.pIav2d` | HTML Google Flights vide ou malformed | Lève `ParsingError("No flights found")` | Vérifie gestion HTML invalide |
| 9 | `test_parse_stops_nonstop` | Vol direct | HTML avec "Non-stop" | `flight.stops == 0` | Vérifie parsing "Non-stop" → int 0 |
| 10 | `test_parse_stops_multiple` | Vol avec escales | HTML avec "2 stops" | `flight.stops == 2` | Vérifie extraction nombre escales |

**Total tests unitaires** : 10 + 10 = 20 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_crawl_and_parse_success` | Mock AsyncWebCrawler avec HTML Google Flights valide (10 vols) | Crawl URL → Parse HTML | `len(flights) == 10`, tous Flight validés Pydantic, pas d'exception |
| 2 | `test_integration_crawl_captcha_retry_parse_success` | Mock AsyncWebCrawler : 1ère tentative captcha, 2ème HTML valide | Crawl avec retry → Parse HTML 2ème tentative | `len(flights) >= 5`, 2 proxies utilisés, logs WARNING captcha puis SUCCESS |
| 3 | `test_integration_crawl_max_retries_no_parse` | Mock AsyncWebCrawler : toutes tentatives retournent captcha | Crawl avec max_retries=3 | Lève `CaptchaDetectedError`, aucun parsing tenté, 3 proxies différents utilisés |
| 4 | `test_integration_crawl_success_parse_zero_flights` | Mock AsyncWebCrawler avec HTML Google Flights vide (aucun `.pIav2d`) | Crawl URL → Parse HTML vide | Lève `ParsingError("Zero valid flights extracted")`, crawl success mais parsing fail |

**Total tests intégration** : 4 tests

---

**TOTAL TESTS** : 20 unitaires + 4 intégration = **24 tests**

---

## Exemples JSON

**Exemple 1 : HTML Google Flights valide (extrait)**
```json
{
  "html_snippet": "<div class='pIav2d'><div class='FpEdX'><span>1250 €</span></div><div class='sSHqwe'>Air France</div><div class='vmXl'><time datetime='2025-06-01T10:30:00'>10:30</time></div><div class='XWcVob'><time datetime='2025-06-01T14:45:00'>14:45</time></div><div class='gvkrdb'>10h 15min</div><div class='BbR8Ec'><div class='ogfYpf'>1 stop</div></div></div>",
  "description": "HTML d'un vol Air France Paris-Tokyo avec 1 escale"
}
```

**Exemple 2 : Flight extrait et validé**
```json
{
  "price": 1250.0,
  "airline": "Air France",
  "departure_time": "2025-06-01T10:30:00Z",
  "arrival_time": "2025-06-01T14:45:00Z",
  "duration": "10h 15min",
  "stops": 1,
  "departure_airport": "CDG",
  "arrival_airport": "NRT"
}
```

**Exemple 3 : Erreur CaptchaDetectedError**
```json
{
  "error": "CaptchaDetectedError",
  "message": "reCAPTCHA v2 detected after 3 retries",
  "details": {
    "url": "https://www.google.com/travel/flights?departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01",
    "proxy_used": "customer-abc123-country-fr:password @ gate.decodo.com:7000",
    "captcha_type": "recaptcha_v2",
    "attempts": 3,
    "proxies_tried": ["proxy1", "proxy2", "proxy3"]
  }
}
```

**Exemple 4 : Log structuré crawl success**
```json
{
  "timestamp": "2025-11-19T10:30:45Z",
  "level": "INFO",
  "service": "CrawlerService",
  "message": "Crawl successful",
  "context": {
    "url": "https://www.google.com/travel/flights?departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01",
    "proxy_used": "customer-abc123-country-fr:password @ gate.decodo.com:7000",
    "status_code": 200,
    "html_size": 245678,
    "response_time_ms": 2345,
    "stealth_mode": true,
    "retry_attempt": 0
  }
}
```

**Exemple 5 : ParsingError (aucun vol extrait)**
```json
{
  "error": "ParsingError",
  "message": "Zero valid flights extracted from HTML",
  "details": {
    "html_size": 123456,
    "base_selector_matches": 0,
    "reason": "No .pIav2d elements found in HTML"
  }
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Crawl Google Flights 1 destination réussi** : CrawlerService crawle avec succès une URL Google Flights aller-simple (Paris→Tokyo) et retourne CrawlResult avec HTML valide (status 200, ≥100KB HTML)

2. **Stealth mode actif** : BrowserConfig configuré avec `enable_stealth=True`, vérifié dans logs structurés (champ `stealth_mode: true`)

3. **Captcha détecté et loggé** : Si reCAPTCHA/hCaptcha présent dans HTML → CaptchaDetectedError levée avec `captcha_type` et `proxy_used` loggés en WARNING

4. **Retry logic avec rotation IP** : En cas de captcha/403/timeout → retry avec exponential backoff (4s, 8s, 16s) et rotation proxies Decodo (3 proxies différents utilisés max)

5. **Parsing extrait minimum 5 vols** : FlightParser parse HTML Google Flights et retourne liste ≥5 Flight validés Pydantic (champs obligatoires présents)

6. **Format Flight valide** : Chaque Flight contient `price > 0`, `airline` (2-100 caractères), `departure_time` et `arrival_time` (datetime ISO 8601), `duration` (format "Xh Ymin"), `stops` (int ≥0 ou None)

7. **Gestion champs manquants** : Si prix/compagnie/horaires absents → vol skippé avec log WARNING, parsing continue pour vols suivants (pas d'exception bloquante)

8. **Erreurs explicites** : CaptchaDetectedError et ParsingError levées avec messages descriptifs et contexte (URL, proxy, HTML size, attempts)

## Critères techniques

9. **Type hints PEP 695** : Toutes signatures CrawlerService, FlightParser, Flight annotées avec type hints modernes (`list[Flight]`, `str | None`, `async def`)

10. **Async/Await cohérent** : CrawlerService.crawl_google_flights async, utilise `async with AsyncWebCrawler`, `await crawler.arun()`, pas de blocking IO

11. **Retry logic Tenacity** : Décorateur `@retry` configuré avec `stop_after_attempt(3)`, `wait_exponential(multiplier=2, min=4, max=60)`, `retry_if_exception_type(CaptchaDetectedError | NetworkError)`

12. **Pydantic v2** : Flight utilise `BaseModel`, `Field(...)` avec contraintes, `field_validator` pour validation cross-champs, `model_config` avec `ConfigDict(frozen=False, extra='forbid')`

13. **JsonCssExtractionStrategy** : Schema CSS défini avec `baseSelector`, `fields` (8 champs minimum), types `text`/`attribute`, pas de LLM

14. **Decodo Proxies configuration** : Format auth `customer-{api_key}-country-fr:password`, endpoint `gate.decodo.com:7000`, rotation cyclique avec `itertools.cycle(proxy_pool)`

15. **Logging structuré JSON** : Tous logs avec `extra={}` contenant contexte métier (`url`, `proxy_used`, `status_code`, `html_size`, `response_time_ms`, `stealth_mode`, `retry_attempt`)

16. **Exceptions custom** : CaptchaDetectedError et ParsingError héritent de Exception, contiennent attributs contextuels (`url`, `proxy_used`, `captcha_type`, `html_size`, `flights_found`)

## Critères qualité

17. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de CrawlerService et FlightParser (pytest-cov)

18. **24 tests passent** : 20 tests unitaires (10 CrawlerService + 10 FlightParser) + 4 tests intégration tous verts (pytest -v)

19. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

20. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

21. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler configurés

22. **Docstrings 1 ligne** : CrawlerService et FlightParser avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

23. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON (pas d'implémentation complète de méthodes)

24. **Commits conventional** : Story 4 committée avec message `docs(specs): add story 4 specifications` conforme Conventional Commits

---

**💡 Note** : Cette story est un Proof of Concept (8 story points). Les 24 critères couvrent faisabilité technique (crawl + parsing 1 destination), robustesse (captcha detection, retry logic), qualité (coverage, types, tests), et foundation réutilisable pour stories 5-6 (multi-destinations, search orchestration).
