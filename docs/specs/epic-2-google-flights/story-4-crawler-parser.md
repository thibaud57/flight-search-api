---
title: "Story 4: Crawler & Parser (Proof of Concept Google Flights 1 destination)"
epic: "Epic 2: Google Flights Integration"
story_points: 8
dependencies: ["epic-1/story-1", "epic-1/story-2", "epic-1/story-3"]
date: "2025-19-11"
keywords: ["crawler", "parser", "crawl4ai", "google-flights", "scraping", "stealth-mode", "jsoncssstrategy", "captcha-detection", "pydantic", "proof-of-concept"]
scope: ["specs"]
technologies: ["crawl4ai", "playwright", "pydantic"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Proof of Concept technique** : Valider la faisabilité du scraping Google Flights pour une destination unique avant d'implémenter la logique multi-destinations complexe
- **Dérisquage early** : Identifier les blocages Google (captchas, rate limiting, anti-bot) dès la Story 4 plutôt qu'aux stories 5 et 6 (économie temps développement)
- **Foundation scraping** : Établir les patterns réutilisables (CrawlerService + FlightParser) pour toutes les stories suivantes (5, 6, 7)
- **Validation stack technique** : Prouver que Crawl4AI + JsonCssExtractionStrategy suffisent pour extraire des données structurées sans LLM (POC dev local)

## Contraintes métier

- **Anti-détection Google Flights** : Google utilise Cloudflare/DataDome pour détecter et bloquer les bots (stealth mode Crawl4AI activé, proxies ajoutés Story 5)
- **Captcha detection MVP** : Phase MVP = détection uniquement (logging), pas de résolution automatique (rotation proxies Story 5, retry Story 7, 2Captcha Phase 7 optionnel si taux blocage >5%)
- **Bandwidth Google Flights** : Minimiser nombre de requêtes et taille HTML téléchargé pour éviter rate limiting (POC = tests dev local limités)
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
- **Temps réponse crawl** : ≤10 secondes par URL Google Flights (P95 percentile, POC dev local)
- **Taux captcha détecté** : ≤5% de requêtes bloquées par reCAPTCHA/hCaptcha (target MVP)
- **Taux parsing réussi** : ≥95% de HTML valides parsés avec succès (minimum 5 vols extraits par recherche)
- **Qualité extraction** : 100% des champs obligatoires (price, airline, departure_time, arrival_time, duration) présents et valides selon schéma Pydantic
- **Coverage tests** : ≥80% sur CrawlerService et FlightParser (unitaires + intégration)

---

# 📋 Spécifications Techniques

## 1. CrawlerService

**Rôle** : Orchestrer le crawling Google Flights avec Crawl4AI, gérer session capture, browser fingerprinting, stealth mode, proxy rotation (Story 5) et détection captchas.

**Interface** :
```python
@dataclass
class CrawlResult:
    """Resultat d'un crawl."""

    success: bool
    html: str
    status_code: int | None = None


class CrawlerService:
    """Service de crawling Google Flights avec stealth mode et proxy rotation."""

    def __init__(self, proxy_service: ProxyService | None = None):
        """Initialise service avec ProxyService optionnel (Story 5)."""

    async def get_google_session(
        self,
        url: str = "https://www.google.com/travel/flights",
        *,
        use_proxy: bool = True,
    ) -> None:
        """
        Capture session Google (headers + cookies) via Crawl4AI avec persistence.

        Capte cookies Google légitimes et accepte automatiquement popup RGPD.
        Les cookies sont réutilisés dans crawl_google_flights().
        """

    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True
    ) -> CrawlResult:
        """
        Crawl une URL Google Flights avec proxy rotation et browser fingerprinting.

        Raises:
            CaptchaDetectedError: Si captcha détecté
            NetworkError: Si erreur réseau ou timeout
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `url` | `str` | URL Google Flights complète avec paramètres query | Format `https://www.google.com/travel/flights?...` |
| `use_proxy` | `bool` | Activer proxy rotation (Story 5) | Default `True`, requiert ProxyService injecté |

**Comportement** :

### Méthode get_google_session()

**Nouvelle méthode (non spécifiée POC initial)** : Capture session Google avant crawls pour améliorer taux succès.

- **Session capture nominale** :
  1. Obtient proxy depuis ProxyService si `use_proxy=True`
  2. Construit BrowserConfig avec base configuration (headers Chrome, stealth args)
  3. Initialise AsyncWebCrawler avec hooks Playwright
  4. Configure hooks :
     - `after_goto` : Auto-click popup RGPD "Tout accepter" (wait_for_selector 1s)
     - `before_return_html` : Capture cookies via `context.cookies()`
  5. Execute `crawler.arun()` sur URL Google Flights (timeout 50s)
  6. Stocke cookies capturés pour réutilisation future
  7. Logger cookies_captured count

- **Edge cases** :
  - **Popup RGPD absent** : Timeout wait_for_selector 1s → Log WARNING, continue sans click
  - **Timeout session capture** : 50s global timeout → Lève `NetworkError`
  - **Status 403/429** : Lève `NetworkError` avec status_code

### Méthode crawl_google_flights()

- **Crawl nominal avec fingerprinting** :
  1. Obtient proxy depuis ProxyService si `use_proxy=True` (rotation automatique)
  2. Construit BrowserConfig avec fingerprint complet :
     - Headers statiques Chrome 142 (27 headers incluant Client Hints sec-ch-ua)
     - Cookies capturés depuis get_google_session()
     - Proxy config si activé
     - Viewport 1920×1080
  3. Initialise AsyncWebCrawler avec BrowserConfig
  4. Configure CrawlerRunConfig :
     - `wait_for="css:.pIav2d"` (attendre cartes vols)
     - `page_timeout` : Configurable via Settings (30s)
     - `delay_before_return_html` : Configurable via Settings (2s)
  5. Exécute `crawler.arun(url)` avec timeout global 50s
  6. Vérifie status code 200 et absence de captcha dans HTML
  7. Retourne CrawlResult avec `success=True`, `html`, `status_code`

- **Edge cases** :
  - **Captcha détecté** : Si HTML contient patterns reCAPTCHA/hCaptcha → Lève `CaptchaDetectedError` avec URL et type captcha
  - **Status code 403/429** : Rate limiting Google → Lève `NetworkError` avec status code
  - **Timeout réseau** : Si `arun()` timeout après 50s → Lève `NetworkError` avec status_code=None
  - **Proxy désactivé** : Si `use_proxy=False` ou ProxyService=None → BrowserConfig sans proxy (mode direct)

- **Erreurs levées** :
  - `CaptchaDetectedError` : Hérité de `Exception`, contient `url`, `captcha_type` (recaptcha/hcaptcha)
  - `NetworkError` : Hérité de `Exception`, contient `url`, `status_code`

- **Logging structuré** :
  - INFO : Début crawl avec URL, proxy_host, proxy_country
  - INFO : Crawl successful avec status_code, html_size, response_time_ms, proxy_host
  - WARNING : Captcha detected avec captcha_type
  - ERROR : Crawl failed avec status_code, proxy_host

### Browser Fingerprinting (utils/browser_fingerprint.py)

**Nouveau module (non spécifié POC initial)** : Anti-détection avancé.

- **Headers statiques Chrome 142** :
  - 27 headers HTTP éprouvés incluant :
    - Client Hints complets : `sec-ch-ua`, `sec-ch-ua-mobile`, `sec-ch-ua-platform`
    - Accept headers : `text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8`
    - User-Agent : Chrome 142.0.6367.62 Windows NT 10.0
    - Referer, Origin, Accept-Language, Accept-Encoding

- **Stealth args Chromium** :
  - `--disable-blink-features=AutomationControlled` (masque automation)
  - `--disable-webrtc` (évite IP leak)
  - `--disable-dev-shm-usage` (stabilité Docker)
  - `--no-sandbox` (si nécessaire environnement)

- **Viewport** : 1920×1080 (résolution courante desktop)

### Hooks Playwright

**Nouveaux hooks (non spécifiés POC initial)** :

| Hook | Trigger | Rôle | Implémentation |
|------|---------|------|----------------|
| `_after_goto_hook` | Après navigation page | Auto-click popup RGPD | Attente sélecteur 1s → Click button acceptation |
| `_extract_cookies_hook` | Avant return HTML | Capture cookies session | Extraction via contexte navigateur → Stockage interne |

**Justification hooks** :
- Popup RGPD bloque scraping si non accepté → Auto-click améliore taux succès
- Cookies Google légitimes réduisent détection bot → Session persistence

### Timeouts Configurables

**Nouveaux settings (non spécifiés POC initial)** :

| Setting | Default | Description | Changement vs POC |
|---------|---------|-------------|-------------------|
| `crawl_global_timeout_s` | 50s | Timeout total asyncio.wait_for | POC = 10s fixe |
| `crawl_page_timeout_ms` | 30000ms | Timeout page load Playwright | POC = non configuré |
| `crawl_delay_s` | 2s | Délai avant return HTML | POC = non configuré |

**Justification** : Timeouts POC 10s trop court pour pages lourdes Google Flights (HTML ~200-500KB + JS loading)

---

## 2. FlightParser

**Rôle** : Extraire les données structurées de vols depuis le HTML Google Flights via JsonCssExtractionStrategy + parsing aria-label avec regex (sans LLM), valider avec Pydantic, et retourner une liste de modèles GoogleFlightDTO.

**Interface** :
```python
class FlightParser:
    """Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

    def parse(self, html: str) -> list[GoogleFlightDTO]:
        """
        Extrait les vols depuis HTML Google Flights.

        Raises:
            ParsingError: Si aucun vol extrait ou HTML invalide
            ValidationError: Si validation Pydantic échoue
        """
```

**Stratégie d'extraction (aria-label + regex)** :

**Approche actuelle** : Au lieu d'extraire 8 champs CSS séparés, l'extraction se fait en 2 étapes :

1. **Étape 1 - JsonCssExtractionStrategy** : Extraction d'un seul champ `aria-label` par carte de vol
   - Sélecteur base : `li.pIav2d` (conteneur de chaque vol)
   - Champ extrait : attribut `aria-label` du `div[aria-label]` enfant

2. **Étape 2 - Regex patterns** : Parsing de l'aria-label avec 8 regex pour extraire les champs

**Configuration JsonCssExtractionStrategy** :

| Propriété | Valeur | Description |
|-----------|--------|-------------|
| `name` | "Google Flights Results" | Nom du schéma d'extraction |
| `baseSelector` | `li.pIav2d` | Sélecteur CSS des cartes vols individuelles |
| **Field 1** | | **Extraction aria-label** |
| `name` | "aria_label" | Nom du champ extrait |
| `selector` | `div[aria-label]` | Sélecteur CSS de l'élément contenant aria-label |
| `type` | "attribute" | Type d'extraction (attribut HTML) |
| `attribute` | "aria-label" | Nom de l'attribut HTML à extraire |

**Regex patterns pour parsing aria-label** :

| Champ | Pattern regex | Exemple match | Notes |
|-------|--------------|---------------|-------|
| `price` | `(\d+(?:\s?\d+)*)\s*euros` | "1270 euros" → 1270.0 | Gère espaces dans nombres (1 270 euros) |
| `airline` | `avec\s+([^.,]+)` | "avec ANA" → "ANA" | Extrait compagnie après "avec" |
| `departure_time` | `Départ.*?(\d{1,2}:\d{2})` | "Départ... 10:30" → "10:30" | Format HH:MM |
| `arrival_time` | `arrivée.*?(\d{1,2}:\d{2})` | "arrivée... 14:45" → "14:45" | Format HH:MM |
| `duration` | `Durée totale\s*:\s*(.+?)(?:\.|$)` | "Durée totale : 13 h 40 min" → "13 h 40 min" | Texte libre après "Durée totale" |
| `stops` | `(\d+)\s*escales?` | "1 escale" → 1 | Parsing "Vol direct" → 0 (cas spécial) |
| `departure_airport` | `Départ de ([^à]+) à` | "Départ de Paris à" → "Paris" | Nom aéroport complet |
| `arrival_airport` | `arrivée à ([^à]+) à` | "arrivée à Tokyo à" → "Tokyo" | Nom aéroport complet |

**Exemple aria-label réel Google Flights** :

```
"À partir de 1270 euros. Départ de Paris à 10:30, arrivée à Tokyo à 14:45.
Durée totale : 13 h 40 min. 1 escale avec ANA."
```

**Parsing flow complet** :

1. JsonCssExtractionStrategy extrait `aria_label` pour chaque carte vol
2. Pour chaque aria-label :
   - Appliquer 8 regex patterns pour extraire champs
   - Si champs obligatoires manquants (price, airline, departure_time, arrival_time) → Skip vol
   - Construire GoogleFlightDTO avec champs extraits
   - Valider automatiquement via Pydantic
3. Retourner liste GoogleFlightDTO validés

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `html` | `str` | HTML brut Google Flights | Non vide, min_length > 1000 caractères |
| **Retour** | `list[GoogleFlightDTO]` | Liste vols extraits et validés | Minimum 1 vol, maximum 50 vols |

**Comportement** :

- **Extraction nominale** :
  1. Instancie JsonCssExtractionStrategy avec FLIGHT_SCHEMA ci-dessus
  2. Applique stratégie sur HTML : `extraction_strategy.extract(url="", html_content=html)`
  3. Pour chaque résultat brut contenant `aria_label` :
     - Parse aria_label avec 8 regex patterns
     - Construit GoogleFlightDTO si champs obligatoires présents
  4. Retourne liste de GoogleFlightDTO validés

- **Edge cases** :
  - **Aria-label absent** : Si `aria_label` vide ou None → Skip vol (log WARNING) et continue parsing vols suivants
  - **Champs manquants** : Si price/airline/departure_time/arrival_time absents dans aria-label → Skip vol (log WARNING)
  - **Prix invalide** : Si regex prix ne matche pas ou conversion float échoue → Skip vol
  - **HTML malformed** : Si baseSelector `li.pIav2d` ne matche aucun élément → Lève `ParsingError("No flights found in HTML")`
  - **Liste vide après parsing** : Si aucun vol valide extrait → Lève `ParsingError("Zero valid flights extracted")`

- **Validation Pydantic** : Voir section 3 (GoogleFlightDTO)

- **Erreurs levées** :
  - `ParsingError` : Hérité de `Exception`, contient `html_size`, `flights_found`
  - `ValidationError` : Pydantic standard, contient détails champs invalides

**Justification approche aria-label** :
- ✅ **Plus robuste** : aria-label = texte stable pour accessibilité, sélecteurs CSS Google changent fréquemment
- ✅ **Maintenance** : 1 sélecteur base + 8 regex patterns vs 8 sélecteurs CSS fragiles
- ⚠️ **Limitation** : Dépend format texte français (`euros`, `avec`, `Départ`), pas multilingue (nécessiterait adaptation regex par langue)

---

## 3. Modèle GoogleFlightDTO (Pydantic)

**Rôle** : Représenter un vol extrait avec validation automatique des types et contraintes métier.

**Interface** :
```python
class GoogleFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    price: Annotated[float, Field(gt=0)]
    airline: Annotated[str, Field(min_length=2, max_length=100)]
    departure_time: str
    arrival_time: str
    duration: str
    stops: Annotated[int | None, Field(ge=0)] = None
    departure_airport: Annotated[str | None, Field(max_length=200)] = None
    arrival_airport: Annotated[str | None, Field(max_length=200)] = None
```

**Validations Pydantic** :

| Champ | Contrainte | Description |
|-------|-----------|-------------|
| `price` | `> 0` | Prix strictement positif (euros) |
| `airline` | `min_length=2, max_length=100` | Nom compagnie valide |
| `departure_time` | Format `HH:MM` | Heure locale format simple (ex: "10:30") |
| `arrival_time` | Format `HH:MM` | Heure locale format simple (ex: "14:45") |
| `duration` | Texte libre | Format durée variable (ex: "10h 30min", "13 h 40 min") |
| `stops` | `≥ 0` ou `None` | Nombre escales valide |
| `departure_airport` | `max_length=200` | Nom aéroport complet ou code (ex: "Paris Charles de Gaulle" ou "CDG") |
| `arrival_airport` | `max_length=200` | Nom aéroport complet ou code (ex: "Tokyo Narita" ou "NRT") |

**Notes importantes** :
- **Types modifiés** : `departure_time` et `arrival_time` sont des `str` (format HH:MM) et non `datetime` car Google Flights retourne uniquement les heures locales sans date ni timezone complètes dans l'aria-label
- **Airport max_length relaxé** : Passé de 10 à 200 caractères pour supporter les noms complets d'aéroports (ex: "Paris Charles de Gaulle") en plus des codes IATA/ICAO
- **Pas de validation cross-champs** : Impossible de valider `arrival_time > departure_time` car les heures sont au format HH:MM sans date (un vol de 23:00 à 02:00 traverse minuit)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CrawlerService (13 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_get_google_session_success` | Session capture réussie | URL Google Flights | Cookies capturés stockés pour réutilisation, logs INFO cookies_captured | Vérifie méthode get_google_session() |
| 2 | `test_get_google_session_auto_click_consent` | Auto-click popup RGPD | Mock page avec button "Tout accepter" | Button cliqué automatiquement, sleep 1s, logs INFO | Vérifie hook _after_goto_hook |
| 3 | `test_get_google_session_no_consent_popup` | Popup RGPD absent | Mock page sans button consent | Timeout 1s, log WARNING, continue sans click, pas d'exception | Vérifie robustesse edge case popup absent |
| 4 | `test_crawl_success_with_fingerprint` | Crawl réussi avec fingerprinting complet | URL Google Flights | `result.success == True`, `result.html` non vide, BrowserConfig avec 27 headers + cookies | Vérifie comportement nominal avec fingerprint |
| 5 | `test_crawl_recaptcha_detection` | HTML contient reCAPTCHA | Mock HTML avec pattern `g-recaptcha` | Lève `CaptchaDetectedError`, `captcha_type="recaptcha"` | Vérifie détection pattern reCAPTCHA |
| 6 | `test_crawl_hcaptcha_detection` | HTML contient hCaptcha | Mock HTML avec pattern `h-captcha` | Lève `CaptchaDetectedError`, `captcha_type="hcaptcha"` | Vérifie détection pattern hCaptcha |
| 7 | `test_crawl_network_timeout` | Timeout réseau AsyncWebCrawler | Mock `arun()` timeout après 50s | Lève `NetworkError`, `status_code=None` | Vérifie gestion timeout (50s configuré) |
| 8 | `test_crawl_status_403` | Status code 403 (rate limiting) | Mock response status 403 | Lève `NetworkError`, `status_code=403` | Vérifie levée erreur sur 403 |
| 9 | `test_crawl_status_429` | Status code 429 (rate limiting) | Mock response status 429 | Lève `NetworkError`, `status_code=429` | Vérifie levée erreur sur 429 |
| 10 | `test_crawl_with_proxy_rotation` | Crawl avec proxy activé | `use_proxy=True`, ProxyService mocké | `proxy_service.get_next_proxy()` appelé, BrowserConfig avec proxy_config | Vérifie intégration ProxyService (Story 5) |
| 11 | `test_crawl_without_proxy` | Crawl sans proxy | `use_proxy=False` | BrowserConfig sans proxy_config, logs proxy_host="no_proxy" | Vérifie mode direct sans proxy |
| 12 | `test_crawl_timeouts_configurable` | Timeouts configurables via Settings | Settings avec custom timeouts | CrawlerRunConfig.page_timeout depuis settings, asyncio.wait_for timeout depuis settings | Vérifie settings.crawler.crawl_*_timeout |
| 13 | `test_crawl_structured_logging` | Logging structuré avec contexte | Crawl avec URL + proxy | Logs contiennent `url`, `status_code`, `html_size`, `response_time_ms`, `proxy_host`, `proxy_country` | Vérifie qualité logging JSON |

### FlightParser (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_parse_valid_html_multiple_flights` | HTML valide avec 10 vols aria-label | Mock HTML avec 10 `li.pIav2d` contenant aria-label valides | `len(flights) == 10`, tous GoogleFlightDTO valides | Vérifie extraction nominale aria-label |
| 2 | `test_parse_aria_label_all_fields_present` | Aria-label avec tous champs | Aria-label complet : "À partir de 1270 euros... avec ANA..." | `flight.price == 1270.0`, tous champs extraits (airline, times, duration, stops, airports) | Vérifie parsing regex complet |
| 3 | `test_parse_price_with_spaces` | Prix avec espaces | Aria-label avec "1 270 euros" (espace séparateur) | `flight.price == 1270.0` (espace supprimé) | Vérifie regex price gère espaces |
| 4 | `test_parse_missing_price` | Aria-label sans prix | Aria-label avec airline mais sans pattern "euros" | Vol skippé, log WARNING, retour None | Vérifie robustesse champ obligatoire manquant |
| 5 | `test_parse_invalid_price_format` | Prix non numérique | Aria-label avec "N/A euros" (conversion float impossible) | Vol skippé, log WARNING, retour None | Vérifie validation format prix après extraction |
| 6 | `test_parse_missing_airline` | Aria-label sans compagnie | Aria-label avec price mais sans pattern "avec" | Vol skippé, log WARNING, retour None | Vérifie robustesse champ obligatoire manquant |
| 7 | `test_parse_missing_departure_time` | Horaires manquants | Aria-label sans pattern "Départ... HH:MM" | Vol skippé (champs obligatoires absents), retour None | Vérifie validation champs obligatoires |
| 8 | `test_parse_no_flights_found` | HTML sans `li.pIav2d` | HTML Google Flights vide ou malformed (aucun baseSelector match) | Lève `ParsingError("No flights found in HTML")` | Vérifie gestion HTML invalide |
| 9 | `test_parse_stops_vol_direct` | Vol direct | Aria-label avec "Vol direct" (texte français) | `flight.stops == 0` (cas spécial détecté) | Vérifie parsing "Vol direct" → int 0 |
| 10 | `test_parse_stops_multiple_escales` | Vol avec escales | Aria-label avec "2 escales" ou "1 escale" | `flight.stops == 2` ou `1` (regex capture nombre) | Vérifie extraction nombre escales depuis regex |

**Total tests unitaires** : 13 (CrawlerService) + 10 (FlightParser) = **23 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_crawl_and_parse_success` | Mock AsyncWebCrawler avec HTML Google Flights valide (10 vols) | Crawl URL → Parse HTML | `len(flights) == 10`, tous Flight validés Pydantic, pas d'exception |
| 2 | `test_integration_crawl_success_parse_zero_flights` | Mock AsyncWebCrawler avec HTML Google Flights vide (aucun `.pIav2d`) | Crawl URL → Parse HTML vide | Lève `ParsingError("Zero valid flights extracted")`, crawl success mais parsing fail |

**Total tests intégration** : 2 tests

---

**TOTAL TESTS** : 23 unitaires + 2 intégration = **25 tests**

---

## Exemples JSON

**Exemple 1 : GoogleFlightDTO extrait et validé**
```json
{
  "price": 1270.0,
  "airline": "ANA",
  "departure_time": "10:30",
  "arrival_time": "14:45",
  "duration": "13 h 40 min",
  "stops": 1,
  "departure_airport": "Paris",
  "arrival_airport": "Tokyo"
}
```

**Note** : `departure_time` et `arrival_time` sont des `str` format HH:MM (heures locales sans date), pas `datetime` ISO 8601. Airports sont noms complets (max 200 car) ou codes IATA.

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
| `status_code` | Integer | Code HTTP réponse | `200`, `403`, `429` |
| `html_size` | Integer | Taille HTML en bytes | `245678` |
| `response_time_ms` | Integer | Temps réponse en ms | `2345` |
| `stealth_mode` | Boolean | Stealth mode activé | `true` |

**Note** : Logs POC dev local (pas de proxy, pas de retry, stealth mode actif).

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Crawl Google Flights 1 destination réussi** : CrawlerService crawle avec succès une URL Google Flights aller-simple (Paris→Tokyo) et retourne CrawlResult avec HTML valide (status 200, ≥100KB HTML)

2. **Stealth mode actif** : BrowserConfig configuré avec `enable_stealth=True`, vérifié dans logs structurés (champ `stealth_mode: true`)

3. **Captcha détecté et loggé** : Si reCAPTCHA/hCaptcha présent dans HTML → CaptchaDetectedError levée avec `captcha_type` loggé en WARNING

4. **Parsing extrait minimum 5 vols** : FlightParser parse HTML Google Flights et retourne liste ≥5 Flight validés Pydantic (champs obligatoires présents)

5. **Format Flight valide** : Chaque Flight contient `price > 0`, `airline` (2-100 caractères), `departure_time` et `arrival_time` (datetime ISO 8601), `duration` (format "Xh Ymin"), `stops` (int ≥0 ou None)

6. **Gestion champs manquants** : Si prix/compagnie/horaires absents → vol skippé avec log WARNING, parsing continue pour vols suivants (pas d'exception bloquante)

7. **Erreurs explicites** : CaptchaDetectedError et ParsingError levées avec messages descriptifs et contexte (URL, HTML size)

## Critères techniques

8. **Type hints PEP 695** : Toutes signatures CrawlerService, FlightParser, Flight annotées avec type hints modernes (`list[Flight]`, `str | None`, `async def`)

9. **Async/Await cohérent** : CrawlerService.crawl_google_flights async, utilise `async with AsyncWebCrawler`, `await crawler.arun()`, pas de blocking IO

10. **Pydantic v2** : Flight utilise BaseModel avec Field pour définir contraintes de validation, validation cross-champs pour cohérence temporelle, configuration strict (extra='forbid')

11. **JsonCssExtractionStrategy** : Configuration extraction CSS avec sélecteur de base pour identifier conteneurs vols, 8 champs minimum à extraire (types text/attribute selon besoin), pas de LLM

12. **Logging structuré JSON** : Tous logs incluent contexte métier dans champs dédiés : URL crawlée, code status HTTP, taille HTML reçu, temps de réponse en millisecondes, activation stealth mode

13. **Exceptions custom** : CaptchaDetectedError et ParsingError héritent de Exception standard Python, incluent attributs contextuels pour debugging : URL concernée, type captcha détecté, taille HTML, nombre vols trouvés

## Critères qualité

14. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de CrawlerService et FlightParser (pytest-cov)

15. **21 tests passent** : 17 tests unitaires (7 CrawlerService + 10 FlightParser) + 4 tests intégration tous verts (pytest -v)

16. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

17. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

18. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler configurés

19. **Docstrings 1 ligne** : CrawlerService et FlightParser avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

20. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON (pas d'implémentation complète de méthodes)

21. **Commits conventional** : Story 4 committée avec message `docs(specs): add story 4 specifications` conforme Conventional Commits

---

**💡 Note** : Cette story est un Proof of Concept (8 story points). Les 21 critères couvrent faisabilité technique (crawl + parsing 1 destination), robustesse (captcha detection, error handling), qualité (coverage, types, tests), et foundation réutilisable pour stories 5-7 (proxies, multi-city, retry logic production).
