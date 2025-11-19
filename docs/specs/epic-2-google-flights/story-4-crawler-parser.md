---
title: "Story 4: Crawler & Parser (Proof of Concept Google Flights 1 destination)"
epic: "Epic 2: Google Flights Integration"
story_points: 8
dependencies: ["story-1-health-check.md", "story-2-config-logging.md", "story-3-search-endpoint.md"]
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
class FlightParser:
    """Parser de vols Google Flights via JsonCssExtractionStrategy."""

    def parse(self, html: str) -> list[Flight]:
        """
        Extrait les vols depuis HTML Google Flights.

        Raises:
            ParsingError: Si aucun vol extrait ou HTML invalide
            ValidationError: Si validation Pydantic échoue
        """
```

**Configuration Extraction CSS** :

La stratégie JsonCssExtractionStrategy doit extraire les champs suivants depuis le HTML Google Flights :

| Champ | Description | Type extraction | Contrainte |
|-------|-------------|-----------------|------------|
| `price` | Prix du vol en euros | Texte | Élément avec classe prix, extraire valeur numérique |
| `airline` | Nom de la compagnie aérienne | Texte | Élément compagnie, texte brut |
| `departure_time` | Heure de départ | Attribut datetime | Balise `<time>` départ, attribut `datetime` ISO 8601 |
| `arrival_time` | Heure d'arrivée | Attribut datetime | Balise `<time>` arrivée, attribut `datetime` ISO 8601 |
| `duration` | Durée du vol | Texte | Élément durée, format "Xh Ymin" |
| `stops` | Nombre d'escales | Texte | Élément escales, parser "Non-stop" ou "X stop(s)" |
| `departure_airport` | Code aéroport départ | Texte | Premier élément aéroport dans route |
| `arrival_airport` | Code aéroport arrivée | Texte | Dernier élément aéroport dans route |

**Sélecteur de base** : Cibler les cartes de vols individuelles (conteneur principal répété pour chaque vol)

**Note** : Les sélecteurs CSS exacts devront être déterminés lors de l'implémentation Phase 5 en inspectant le HTML réel de Google Flights (structure non documentée, peut varier).

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
class Flight(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    price: float
    airline: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    stops: int | None
    departure_airport: str | None
    arrival_airport: str | None
```

**Validations Pydantic** :

| Champ | Contrainte | Description |
|-------|-----------|-------------|
| `price` | `> 0` | Prix strictement positif (euros) |
| `airline` | `min_length=2, max_length=100` | Nom compagnie valide |
| `departure_time` | Format ISO 8601 | Datetime valide |
| `arrival_time` | Format ISO 8601 + après `departure_time` | Cohérence temporelle |
| `duration` | Pattern `"Xh Ymin"` | Format durée strict (ex: "10h 30min") |
| `stops` | `≥ 0` ou `None` | Nombre escales valide |
| `departure_airport` | `max_length=10` | Code IATA/ICAO |
| `arrival_airport` | `max_length=10` | Code IATA/ICAO |

**Validation cross-champs** : La méthode de validation doit vérifier que `arrival_time` est postérieur à `departure_time` (cohérence temporelle du vol).

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

**Exemple 1 : Flight extrait et validé**
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

**Exemple 2 : Erreur CaptchaDetectedError**
```json
{
  "error": "CaptchaDetectedError",
  "message": "reCAPTCHA v2 detected after 3 retries",
  "details": {
    "url": "https://www.google.com/travel/flights?departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01",
    "captcha_type": "recaptcha_v2",
    "attempts": 3
  }
}
```

**Exemple 3 : ParsingError (aucun vol extrait)**
```json
{
  "error": "ParsingError",
  "message": "Zero valid flights extracted from HTML",
  "details": {
    "html_size": 123456,
    "base_selector_matches": 0,
    "reason": "No flight containers found in HTML"
  }
}
```

---

# 📊 Observabilité & Monitoring

## Logging structuré

Tous les logs doivent suivre le format JSON structuré avec les champs suivants :

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | Date et heure événement | `"2025-11-19T10:30:45Z"` |
| `level` | String | Niveau log (DEBUG/INFO/WARNING/ERROR) | `"INFO"` |
| `service` | String | Service concerné | `"CrawlerService"` |
| `message` | String | Message descriptif | `"Crawl successful"` |
| `url` | String | URL crawlée | URL Google Flights complète |
| `proxy_used` | String (optionnel) | Proxy utilisé (masqué si sensible) | Format customer générique |
| `status_code` | Integer | Code HTTP réponse | `200`, `403`, `429` |
| `html_size` | Integer | Taille HTML en bytes | `245678` |
| `response_time_ms` | Integer | Temps réponse en ms | `2345` |
| `stealth_mode` | Boolean | Stealth mode activé | `true` |
| `retry_attempt` | Integer | Numéro tentative (0 = première) | `0`, `1`, `2` |

**Note** : Secrets (mots de passe proxy, API keys) doivent être masqués dans les logs pour sécurité.

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

11. **Retry logic Tenacity** : Système de retry automatique avec maximum 3 tentatives, délai exponentiel entre tentatives (4s, 8s, 16s jusqu'à 60s max), déclenchement sur exceptions CaptchaDetectedError et NetworkError uniquement

12. **Pydantic v2** : Flight utilise BaseModel avec Field pour définir contraintes de validation, validation cross-champs pour cohérence temporelle, configuration strict (extra='forbid')

13. **JsonCssExtractionStrategy** : Configuration extraction CSS avec sélecteur de base pour identifier conteneurs vols, 8 champs minimum à extraire (types text/attribute selon besoin), pas de LLM

14. **Decodo Proxies configuration** : Authentification format customer avec clé API et ciblage pays (France), endpoint dédié, système de rotation cyclique entre pool de proxies disponibles

15. **Logging structuré JSON** : Tous logs incluent contexte métier dans champs dédiés : URL crawlée, proxy utilisé, code status HTTP, taille HTML reçu, temps de réponse en millisecondes, activation stealth mode, numéro tentative retry

16. **Exceptions custom** : CaptchaDetectedError et ParsingError héritent de Exception standard Python, incluent attributs contextuels pour debugging : URL concernée, proxy utilisé, type captcha détecté, taille HTML, nombre vols trouvés

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
