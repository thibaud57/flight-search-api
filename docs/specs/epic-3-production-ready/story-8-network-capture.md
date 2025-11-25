---
title: "Story 8: Network Capture pour Multi-City Complet"
epic: "Epic 3: Production Ready"
story_points: 8
dependencies: ["epic-2/story-6", "epic-3/story-7"]
date: "2025-23-11"
keywords: ["network-capture", "crawl4ai", "xhr-interception", "api-response", "multi-segment", "json-parsing", "complete-data", "google-flights-api", "resource-blocking", "bandwidth-optimization", "playwright-hooks"]
scope: ["specs"]
technologies: ["Crawl4AI", "asyncio", "Python", "Pydantic v2", "JSON", "Playwright"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Données complètes multi-city** : Utilisateurs recherchant vols multi-city 3 segments (ex: Paris→Tokyo→Kyoto→Paris) attendent voir détails complets des 3 vols (horaires, compagnies, escales) pas seulement segment 1
- **Visibilité itinéraire complet** : Planification voyage nécessite connaître durée totale réelle trajet (sum des 3 durées segments) et escales totales (sum des 3 stops) pour comparaison intelligente entre combinaisons dates
- **Best flight vraiment complet** : Sélection "meilleure option" doit inclure TOUS les segments de l'itinéraire (Paris→Tokyo + Tokyo→Kyoto + Kyoto→Paris) avec leur prix total combiné, pas juste première étape
- **Parity Google Flights UI** : L'interface Google Flights affiche 3 vols distincts par combinaison, notre API doit retourner mêmes informations détaillées pour expérience utilisateur cohérente

## Contraintes métier

- **Limitation CSS extraction actuelle** : `JsonCssExtractionStrategy` de Crawl4AI parse uniquement HTML DOM visible, or Google Flights charge résultats via API calls JavaScript → seulement premier vol visible statiquement dans HTML, segments 2-3 chargés dynamiquement
- **API Google Flights non documentée** : Responses API internes Google Flights format JSON propriétaire non stable (peut changer), nécessite parsing résilient avec fallback si structure change
- **Coûts bandwidth optimisables** : Network capture n'augmente pas consommation bandwidth Decodo, et permet blocage ressources non essentielles (images, fonts, gstatic.com) pour réduction ~40-60% bandwidth via hooks Playwright
- **Compatibilité Crawl4AI 0.7.7+** : Feature `capture_network_requests` disponible depuis Crawl4AI 0.7.7, nécessite configuration `CrawlerRunConfig` avec `capture_network_requests=True`
- **Performance parsing JSON** : Parsing JSON API responses plus rapide que CSS selectors (~10-20ms vs ~50-100ms per page) mais nécessite identifier correct API endpoint parmi tous network events capturés

## Valeur business

- **Données 3x plus complètes** : Passer de 1 segment capturé (CSS extraction) à 3 segments complets (network capture) = 300% augmentation richesse données pour même coût crawl
- **Ranking multi-segment intelligent** : Possibilité futurs critères ranking avancés (durée totale trajet réel = sum 3 segments, nombre escales total, time window optimal entre connexions) impossible avec données partielles CSS
- **Foundation scalabilité itinéraires** : Architecture network capture généralisable pour 2-5 segments (pas hardcodé 3), réutilisable pour MVP évolutions (recherche 4-5 segments, aller-retour simple 2 segments)
- **Différenciation compétitive renforcée** : Retour API structuré avec `flights: [segment1, segment2, segment3]` complet = valeur ajoutée vs agrégateurs grand public retournant seulement prix total sans détails segments

## Métriques succès

- **Taux capture complète** : 100% des combinaisons multi-city retournent `len(flights) == len(segment_dates)` (validation: 3 segments dates → 3 flights data)
- **Zéro perte données** : Comparaison avant/après migration CSS→Network : 0% perte informations (price, airline, times identiques) + gain 200% données nouvelles (segments 2-3 ajoutés)
- **Taux succès parsing JSON** : ≥95% responses API Google Flights parsées avec succès (structure JSON stable identifiée malgré API non documentée)
- **Performance parsing** : Médiane temps parsing JSON <20ms par response (vs ~80ms CSS selectors), gain performance 4x sur parsing seul
- **Coverage tests** : ≥80% sur NetworkResponseFilter, FlightParser JSON parsing, ResourceBlockingHook, intégration CrawlerService network capture
- **Réduction bandwidth** : Blocage ressources non essentielles réduit consommation Decodo ~40-60% par crawl (mesurable via dashboard Decodo avant/après)

---

# 📋 Spécifications Techniques

## 1. CrawlerService (Modification Network Capture)

**Rôle** : Activer capture réseau Crawl4AI pour intercepter API calls Google Flights au lieu de parser HTML avec CSS selectors.

**Interface** :
```python
class CrawlerService:
    """Service crawling Google Flights avec network capture."""

    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True
    ) -> CrawlResult:
        """
        Crawl URL Google Flights avec capture réseau activée.

        Returns:
            CrawlResult avec network_requests capturés (liste events API)
        """
```

**Modifications Configuration** :

| Paramètre CrawlerRunConfig | Valeur Actuelle (CSS) | Nouvelle Valeur (Network) | Justification |
|----------------------------|----------------------|--------------------------|---------------|
| `extraction_strategy` | `JsonCssExtractionStrategy` | ❌ Retiré (pas utilisé) | Network capture remplace extraction CSS |
| `capture_network_requests` | `False` (défaut) | ✅ `True` | Active interception requêtes réseau |
| `wait_until` | `"domcontentloaded"` | ✅ `"networkidle"` | Attendre fin API calls avant retour (2s timeout après dernière requête réseau) |
| `delay_before_return_html` | `1.0` secondes | ✅ `2.0` secondes | Laisser temps API Google Flights compléter (responses XHR peuvent arriver après DOM ready) |

**Comportement Network Capture** :

**Étape 1 : Configuration crawler avec network capture**
1. Créer `CrawlerRunConfig` avec `capture_network_requests=True`, `wait_until="networkidle"`, `delay_before_return_html=2.0`
2. Configurer proxy_config si `use_proxy=True` (inchangé Story 5)
3. Configurer browser_config avec stealth mode (fingerprint randomization Story 6)

**Étape 2 : Crawl page Google Flights**
1. Appeler `crawler.arun(url, config=config)` (async context manager)
2. Playwright charge page, exécute JavaScript Google Flights
3. Crawl4AI intercepte automatiquement toutes requêtes réseau (XHR, Fetch, WebSocket)
4. Attendre `networkidle` (2s sans nouvelle requête) puis delay additionnel 2s

**Étape 3 : Récupération network events**
1. Accéder `result.network_requests` (liste événements capturés par Crawl4AI)
2. Si `result.network_requests` vide → Logger WARNING, fallback parsing HTML classique (dégradation gracieuse)
3. Retourner `CrawlResult` avec `network_requests` rempli

**Edge cases** :
- **Aucun network event capturé** : Peut arriver si Google Flights change architecture (pas d'API call XHR), fallback HTML parsing
- **Timeout networkidle dépassé** : Si API calls infinies (bug Google), timeout max 10s puis retour forcé (éviter hang)
- **Captcha détecté** : Vérification captcha inchangée (inspect HTML), si captcha → lève `CaptchaDetectedError` (retry Story 7)

**Erreurs levées** :
- `CaptchaDetectedError` : Si captcha détecté dans HTML ou network responses
- `NetworkError` : Si timeout crawler ou erreur Playwright

**Logging structuré** :
- INFO : Début crawl avec network capture enabled
- DEBUG : Nombre network events capturés après crawl
- WARNING : Aucun network event capturé (fallback HTML)

---

## 2. NetworkResponseFilter

**Rôle** : Filtrer liste brute network events capturés pour identifier spécifiquement les API responses Google Flights contenant données vols multi-city.

**Interface** :
```python
class NetworkResponseFilter:
    """Filtre network events pour identifier API responses Google Flights."""

    def filter_flight_api_responses(
        self,
        network_events: list[dict]
    ) -> list[dict]:
        """
        Filtre network events pour garder seulement API responses vols.

        Returns:
            Liste responses API Google Flights avec status 200 et JSON body
        """
```

**Critères Filtrage** :

| Critère | Condition | Justification |
|---------|-----------|---------------|
| **Event type** | `event.get("event_type") == "response"` | Exclure events "request" et "request_failed" (pas de data response) |
| **Status code** | `event.get("status") == 200` | Seules responses succès contiennent données vols valides |
| **Resource type** | `event.get("resource_type") in ["xhr", "fetch"]` | API calls Google Flights utilisent XHR ou Fetch API (pas "document", "script", "image") |
| **URL pattern** | `"google.com" in event.get("url", "")` | Exclure 3rd-party APIs (analytics, ads), garder seulement Google Flights API |
| **Response body présent** | `"response_data" in event or "body" in event` | Vérifier event contient payload JSON exploitable |

**Comportement Filtrage** :

**Étape 1 : Filtrage initial par type event**
1. Itérer sur `network_events` liste
2. Garder seulement events avec `event_type == "response"` (exclure 50% events typiquement)

**Étape 2 : Filtrage status + resource type**
3. Parmi responses, garder `status == 200` (exclure 404, 500, redirects 3xx)
4. Garder `resource_type in ["xhr", "fetch"]` (exclure images, CSS, scripts)

**Étape 3 : Filtrage URL pattern**
5. Vérifier URL contient `"google.com"` (domaine Google Flights)
6. Optionnel : Pattern matching `/travel/flights` ou `/rpc/` dans URL path (endpoints API typiques)

**Étape 4 : Validation response body**
7. Vérifier clé `"response_data"` ou `"body"` présente dans event dict
8. Si body vide ou None → exclure event

**Étape 5 : Déduplication**
9. Retourner liste filtrée unique (éviter duplicates si même API call capturé 2x)

**Edge cases** :
- **Multiples API endpoints** : Google Flights peut appeler plusieurs APIs (`/search`, `/filters`, `/metadata`), garder tous endpoints puis parser chacun
- **URL encodée base64** : URLs peuvent contenir params encodés, pattern matching flexible nécessaire
- **Aucune response matching** : Si 0 responses après filtrage → Logger WARNING, retourner liste vide (caller gère fallback)

**Erreurs levées** :
- Aucune exception levée (méthode pure filtrage, retourne liste vide si aucun match)

**Logging structuré** :
- DEBUG : Nombre events input vs output filtrage (ex: 250 events → 3 API responses Google Flights)
- WARNING : Aucune API response trouvée après filtrage

---

## 3. FlightParser (Modification JSON Parsing)

**Rôle** : Parser JSON API responses Google Flights multi-city pour extraire TOUS les segments vols (3 flights pour 3 segments) au lieu de parser HTML CSS.

**Interface** :
```python
class FlightParser:
    """Parser Google Flights data depuis network API responses JSON."""

    def parse_api_responses(
        self,
        api_responses: list[dict]
    ) -> tuple[float, list[GoogleFlightDTO]]:
        """
        Parse JSON API responses pour extraire tous segments vols.

        Returns:
            Tuple (total_price, flights) avec prix total itinéraire + liste GoogleFlightDTO (1 DTO par segment)
        """
```

**Modifications Parsing** :

| Aspect | Méthode Actuelle (CSS) | Nouvelle Méthode (JSON API) | Changement |
|--------|------------------------|----------------------------|------------|
| **Input** | HTML string | Liste dicts JSON (network responses) | Type input change complètement |
| **Extraction price** | CSS selector `.BVAVmf .YMlIz .FpEdX span` | JSON path `data.flights[i].price.total` | Accès direct clé JSON vs selector fragile |
| **Extraction airline** | CSS selector `.sSHqwe span` | JSON path `data.flights[i].segments[0].carrier.name` | Données structurées JSON vs text parsing |
| **Extraction times** | CSS selector parsing text "10:30 – 14:45" | JSON path `data.flights[i].segments[0].departure_time` | Format ISO 8601 direct vs parsing manuel |
| **Segments multiples** | ❌ Impossible (HTML affiche 1 segment) | ✅ Itération `data.flights[i]` pour i=0,1,2 | Architecture JSON permet accès N segments |

**Structure JSON API Google Flights** (format observé empiriquement, non documenté officiel) :

```json
{
  "data": {
    "flights": [
      {
        "id": "flight_combination_1",
        "price": {
          "total": 1250.0,
          "currency": "EUR"
        },
        "segments": [
          {
            "segment_index": 0,
            "departure": {
              "airport": "CDG",
              "city": "Paris",
              "time": "2025-06-01T10:30:00Z"
            },
            "arrival": {
              "airport": "NRT",
              "city": "Tokyo",
              "time": "2025-06-02T06:45:00Z"
            },
            "carrier": {
              "name": "Air France",
              "code": "AF"
            },
            "duration_minutes": 765,
            "stops": 0
          },
          {
            "segment_index": 1,
            "departure": {...},
            "arrival": {...},
            "carrier": {...},
            "duration_minutes": 240,
            "stops": 1
          },
          {
            "segment_index": 2,
            "departure": {...},
            "arrival": {...},
            "carrier": {...},
            "duration_minutes": 765,
            "stops": 0
          }
        ]
      }
    ]
  }
}
```

**Comportement Parsing JSON** :

**Étape 1 : Identification response correcte**
1. Itérer sur `api_responses` filtrées
2. Pour chaque response, extraire body JSON : `json.loads(response.get("response_data") or response.get("body"))`
3. Vérifier présence clés attendues : `data.flights` (structure valide Google Flights)
4. Si multiple responses matchent → prendre première avec `len(data.flights) > 0`

**Étape 2 : Extraction best flight combination et prix total**
5. Accéder `data.flights[0]` (Google Flights trie options par prix croissant, best flight = index 0)
6. Extraire `flight_combination.price.total` → stocker comme `total_price` (prix total itinéraire complet, sera ajouté au niveau racine FlightCombinationResult)

**Étape 3 : Itération segments multi-city**
7. Itérer sur `flight_combination.segments` (liste 3 segments pour 3-city)
8. Pour chaque segment `i` :
   - Extraire `departure.time`, `arrival.time` (format ISO 8601 → convertir "HH:MM" display format)
   - Extraire `carrier.name` (airline)
   - Extraire `duration_minutes` → convertir "Xh XXmin" format
   - Extraire `stops` (nombre escales)
   - Extraire `departure.city` et `arrival.city` (ou `airport` si city absent)
9. Créer `GoogleFlightDTO` pour chaque segment avec données extraites

**Étape 4 : Retour données complètes**
10. Retourner tuple `(total_price: float, flights: list[GoogleFlightDTO])` avec len(flights)=3 pour 3 segments
11. `total_price` = prix total itinéraire extrait depuis `flight_combination.price.total`
12. `flights` = liste segments SANS champ price individuel (price n'existe que au niveau itinéraire complet)
13. Ordre flights respecte ordre segments itinéraire (index 0 = Paris→Tokyo, index 1 = Tokyo→Kyoto, index 2 = Kyoto→Paris)

**Edge cases** :
- **Structure JSON différente** : Si clés attendues absentes (`data.flights` manquant) → Logger ERROR, lève `ParsingError` avec message explicite
- **Segments incomplets** : Si segment manque champs obligatoires (ex: `duration` absent) → Utiliser valeurs par défaut (`duration="Unknown"`, `stops=0`)
- **Prix manquant** : Si `price.total` absent → Utiliser premier segment price comme fallback (peut être prix partiel)
- **Aucune flight option** : Si `len(data.flights) == 0` → Retourner liste vide (pas d'exception, caller gère)

**Erreurs levées** :
- `ParsingError` : Si JSON structure invalide ou clés critiques absentes
- `json.JSONDecodeError` : Si response body pas JSON valide (capturée et reemballée ParsingError)

**Logging structuré** :
- INFO : Nombre segments parsés depuis JSON API (ex: 3 segments extraits)
- DEBUG : Première et dernière flight DTO créée (sample vérification)
- ERROR : Structure JSON inattendue avec détails clés manquantes

---

## 4. FlightCombinationResult (Modification Modèle)

**Rôle** : Modifier modèle `FlightCombinationResult` pour supporter liste complète flights multi-segments au lieu de flight unique segment 1.

**Interface actuelle (Story 6)** :
```python
class FlightCombinationResult(BaseModel):
    """Résultat combinaison dates avec flight unique (segment 1 seulement)."""

    segment_dates: list[str]
    flights: list[GoogleFlightDTO]  # ⚠️ Actuellement: length=1 (premier segment)
```

**Interface modifiée (Story 8)** :
```python
class FlightCombinationResult(BaseModel):
    """Résultat combinaison dates avec flights complets (tous segments)."""

    model_config = ConfigDict(extra="forbid")

    segment_dates: list[str]
    total_price: float  # ✅ NOUVEAU: Prix total itinéraire au niveau racine
    flights: list[GoogleFlightDTO]  # ✅ Modifié: length=len(segment_dates), SANS champ price
```

**Champs** :

| Champ | Type | Description Actuelle | Description Modifiée | Validation Ajoutée |
|-------|------|---------------------|---------------------|-------------------|
| `segment_dates` | `list[str]` | Dates départ chaque segment (2-5 dates) | ❌ Inchangé | Inchangé |
| `total_price` | `float` | ❌ N'existe pas | ✅ NOUVEAU: Prix total itinéraire complet (somme implicite 3 segments) | ≥ 0, format 2 décimales |
| `flights` | `list[GoogleFlightDTO]` | Liste 1 flight (segment 1 uniquement) avec price | ✅ Liste N flights (N=len(segment_dates), tous segments) SANS price individuel | `field_validator`: vérifie `len(flights) == len(segment_dates)` |

**Validations Pydantic Ajoutées** :

```python
@field_validator('flights', mode='after')
@classmethod
def validate_flights_length(cls, v: list[GoogleFlightDTO], info: ValidationInfo) -> list[GoogleFlightDTO]:
    """Valide nombre flights égal nombre segment_dates (cohérence multi-city)."""
```

**Comportement Validation** :

- **Input valide** : `segment_dates=["2025-06-01", "2025-06-15", "2025-06-22"]`, `flights=[flight1, flight2, flight3]` → Validation OK
- **Input invalide** : `segment_dates` length=3 mais `flights` length=1 → Lève `ValidationError` avec message clair
- **Ordre flights** : Validator ne vérifie PAS ordre (flight[0] = segment_dates[0], etc.), responsabilité FlightParser garantir ordre correct

**Migration Story 6 → Story 8** :

| Aspect | Story 6 (CSS Extraction) | Story 8 (Network Capture) | Impact Migration |
|--------|-------------------------|--------------------------|------------------|
| **FlightCombinationResult.flights** | Always `len(flights) == 1` | `len(flights) == len(segment_dates)` (2-5) | ⚠️ Breaking change API response structure |
| **SearchResponse JSON** | `results[i].flights[0]` = segment 1 | `results[i].flights[0,1,2]` = tous segments | Clients API doivent adapter parsing (itérer liste au lieu d'accéder index 0) |
| **Ranking logic** | Tri par `flights[0].price` | ❌ Inchangé, tri par `flights[0].price` (prix total itinéraire dans premier flight) | Pas d'impact ranking |

**Edge cases** :
- **Segments inégaux** : Si `segment_dates` length=3 mais FlightParser retourne seulement 2 flights → ValidationError levée (empêche données incohérentes)
- **Flight vide** : Si `flights=[]` → ValidationError levée (minimum 1 flight requis pour résultat valide)

**Erreurs levées** :
- `ValidationError` : Si `len(flights) != len(segment_dates)` (validation Pydantic)

**Logging structuré** :
- DEBUG : Validation FlightCombinationResult avec segment_dates count et flights count

---

## 5. ResourceBlockingHook (Optimisation Bandwidth)

**Rôle** : Bloquer ressources non essentielles (images, fonts, domaines tiers) via hook Playwright `on_page_context_created` pour réduire consommation bandwidth Decodo ~40-60%.

**Interface** :
```python
async def optimize_google_flights_bandwidth(
    page: Page,
    context: BrowserContext,
    **kwargs
) -> Page:
    """
    Hook Crawl4AI pour bloquer ressources non essentielles Google Flights.

    Returns:
        Page configurée avec route filter actif
    """
```

**Configuration Domaines Bloqués** :

| Domaine | Type Ressource | Justification Blocage |
|---------|---------------|----------------------|
| `fonts.gstatic.com` | Fonts Google | ~50-100KB par page, non nécessaire extraction données |
| `fonts.googleapis.com` | CSS Fonts | Définitions fonts, non nécessaire |
| `maps.googleapis.com` | Maps API | Non utilisé Google Flights recherche |
| `play.google.com` | Play Store | Liens apps, non nécessaire |
| `*.doubleclick.net` | Ads | Tracking publicitaire |
| `*.googlesyndication.com` | Ads | Réseau publicitaire Google |

**Configuration Resource Types Bloqués** :

| Resource Type | Blocage | Justification |
|--------------|---------|---------------|
| `image` | ✅ Bloqué | Logos compagnies, photos destinations (~200-500KB par page) |
| `font` | ✅ Bloqué | Fonts personnalisées (~50-150KB par page) |
| `media` | ✅ Bloqué | Vidéos promotionnelles (rare mais lourd) |
| `stylesheet` | ❌ Autorisé | Peut affecter rendering DOM nécessaire network capture |
| `script` | ❌ Autorisé | JavaScript nécessaire pour API calls Google Flights |
| `xhr` | ❌ Autorisé | API responses = données vols à capturer |
| `fetch` | ❌ Autorisé | API responses = données vols à capturer |
| `document` | ❌ Autorisé | HTML page principale |

**Comportement Hook** :

**Étape 1 : Configuration route filter**
1. Hook appelé automatiquement par Crawl4AI après création `BrowserContext`
2. Définir liste `BLOCKED_DOMAINS` et `BLOCKED_RESOURCE_TYPES`
3. Enregistrer route filter via `context.route("**/*", route_filter)`

**Étape 2 : Filtrage requêtes (route_filter)**
1. Pour chaque requête interceptée :
   - Extraire `route.request.url` et `route.request.resource_type`
   - Si URL contient domaine dans `BLOCKED_DOMAINS` → `await route.abort()`
   - Si `resource_type` dans `BLOCKED_RESOURCE_TYPES` → `await route.abort()`
   - Sinon → `await route.continue_()`
2. Logger DEBUG chaque requête bloquée (pour monitoring bandwidth économisé)

**Étape 3 : Retour page configurée**
3. Retourner `page` avec route filter actif
4. Crawl4AI utilise cette page configurée pour navigation

**Intégration CrawlerService** :

```python
CrawlerRunConfig(
    capture_network_requests=True,
    wait_until="networkidle",
    hooks={
        "on_page_context_created": optimize_google_flights_bandwidth
    }
)
```

**Edge cases** :
- **Ressource critique bloquée par erreur** : Si blocage casse fonctionnalité (ex: JavaScript manquant) → Réduire liste blocage, logger ERROR
- **Hook échoue** : Try/except autour route registration, fallback sans blocage (dégradation gracieuse)
- **Domaine inconnu** : Par défaut autoriser (whitelist approach pour blocage, pas blacklist)

**Erreurs levées** :
- Aucune exception levée (hook silencieux, logging uniquement)

**Logging structuré** :
- INFO : Hook activé avec nombre domaines/types bloqués
- DEBUG : Chaque requête bloquée (URL, resource_type, taille estimée)
- WARNING : Hook registration échoue (fallback sans blocage)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### NetworkResponseFilter (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_filter_keeps_response_events_only` | Filtre garde seulement event_type=response | Liste 10 events : 5 "request", 3 "response", 2 "request_failed" | 3 events filtrés (seulement "response") | Vérifie filtrage type event correct |
| 2 | `test_filter_requires_status_200` | Filtre garde seulement status 200 | Liste 5 responses : 3 status 200, 1 status 404, 1 status 500 | 3 events filtrés (status 200 uniquement) | Vérifie exclusion erreurs HTTP |
| 3 | `test_filter_requires_xhr_fetch_resource_type` | Filtre garde seulement XHR/Fetch | Liste 6 responses : 2 "xhr", 2 "fetch", 1 "image", 1 "script" | 4 events filtrés (xhr + fetch) | Vérifie exclusion ressources non-API |
| 4 | `test_filter_requires_google_domain` | Filtre garde seulement URLs google.com | Liste 4 responses : 2 URLs "google.com/travel", 1 "googleapis.com", 1 "thirdparty.com" | 2 events filtrés (google.com uniquement) | Vérifie pattern matching domaine |
| 5 | `test_filter_requires_response_body_present` | Filtre exclut events sans body | Liste 3 responses : 2 avec "response_data", 1 sans body | 2 events filtrés (body présent) | Vérifie validation presence payload |
| 6 | `test_filter_returns_empty_if_no_match` | Retourne liste vide si aucun match | Liste 5 events : tous type "request" ou status 404 | `[]` liste vide | Vérifie comportement edge case aucun match |

### FlightParser JSON Parsing (7 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 7 | `test_parse_json_three_segments` | Parse JSON API avec 3 segments | Mock JSON avec `data.flights[0].segments` length=3 | Tuple `(total_price, flights)` avec `len(flights) == 3`, chaque DTO valide | Vérifie extraction complète 3 segments |
| 8 | `test_parse_json_extracts_total_price` | Extraction prix total itinéraire séparé | Mock JSON avec `price.total=1250.0` | `total_price == 1250.0`, `flights` ne contiennent PAS champ price | Vérifie prix extrait au niveau racine |
| 9 | `test_parse_json_extracts_airline` | Extraction nom compagnie | Mock JSON avec `carrier.name="Air France"` | `flights[0].airline == "Air France"` | Vérifie accès clé JSON airline |
| 10 | `test_parse_json_converts_duration` | Conversion duration minutes → format display | Mock JSON avec `duration_minutes=765` | `flights[0].duration == "12h 45min"` | Vérifie conversion format durée |
| 11 | `test_parse_json_formats_times` | Conversion ISO 8601 → HH:MM | Mock JSON avec `departure.time="2025-06-01T10:30:00Z"` | `flights[0].departure_time == "10:30"` | Vérifie parsing timestamp ISO |
| 12 | `test_parse_json_invalid_structure` | JSON structure invalide lève exception | Mock JSON sans clé `data.flights` | Lève `ParsingError` avec message clair | Vérifie error handling structure invalide |
| 13 | `test_parse_json_missing_segment_fields` | Champs segment manquants utilisent defaults | Mock JSON segment sans `duration` | `flights[0].duration == "Unknown"`, pas d'exception | Vérifie fallback valeurs par défaut |

### CrawlerService Network Capture (5 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 14 | `test_crawl_activates_network_capture` | Config network capture activée | Mock `AsyncWebCrawler`, URL valide | `CrawlerRunConfig` créée avec `capture_network_requests=True` | Vérifie activation network capture |
| 15 | `test_crawl_waits_networkidle` | Attend networkidle avant retour | Mock crawler avec network events arrivant après 1s | `wait_until="networkidle"` configuré, delay 2s respecté | Vérifie timing attente API calls |
| 16 | `test_crawl_returns_network_requests` | Retourne network events capturés | Mock crawler avec 10 network events | `result.network_requests` length=10 | Vérifie accès données network capture |
| 17 | `test_crawl_fallback_if_no_network_events` | Fallback gracieux si aucun event | Mock crawler avec `network_requests=[]` | Logger WARNING, retourne CrawlResult avec empty list (pas d'exception) | Vérifie dégradation gracieuse |
| 18 | `test_crawl_captcha_detection_unchanged` | Captcha detection fonctionne toujours | Mock HTML avec captcha pattern | Lève `CaptchaDetectedError` (comportement Story 4 inchangé) | Vérifie compatibilité captcha detection |

### ResourceBlockingHook (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 19 | `test_hook_blocks_gstatic_domain` | Blocage domaine fonts.gstatic.com | Mock route avec URL `fonts.gstatic.com/s/roboto/...` | `route.abort()` appelé | Vérifie blocage domaine Google Fonts |
| 20 | `test_hook_blocks_image_resource_type` | Blocage resource_type image | Mock route avec `resource_type="image"` | `route.abort()` appelé | Vérifie blocage images (logos, photos) |
| 21 | `test_hook_allows_xhr_requests` | XHR API calls non bloqués | Mock route avec `resource_type="xhr"`, URL Google Flights API | `route.continue_()` appelé | Vérifie données vols passent (essentiel) |
| 22 | `test_hook_allows_script_requests` | Scripts JavaScript non bloqués | Mock route avec `resource_type="script"`, URL `google.com` | `route.continue_()` appelé | Vérifie JS exécuté (nécessaire API calls) |

**Total tests unitaires** : 6 (NetworkResponseFilter) + 7 (FlightParser) + 5 (CrawlerService) + 4 (ResourceBlockingHook) = **22 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_network_capture_three_segments` | Mock AsyncWebCrawler avec network events contenant JSON API 3 segments, SearchRequest 2 dates × 3 segments = 6 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse.results[0].flights` length=3 (tous segments capturés), chaque flight contient airline, times, duration valides |
| 2 | `test_integration_css_vs_network_comparison` | Même SearchRequest exécuté avec CSS extraction (baseline) puis network capture | Comparer nombre champs non-null entre CSS result vs Network result | Network capture retourne 3x plus données (flights[0,1,2] vs seulement flights[0]), aucune perte données segment 1 |
| 3 | `test_integration_ranking_with_complete_flights` | Mock 10 combinaisons avec 3 segments chacune, prix variés | Appeler `search_service.search_flights(SearchRequest)` | Top 10 ranking fonctionne correctement, trié par `flights[0].price`, chaque result contient 3 flights complets |
| 4 | `test_integration_json_parsing_error_fallback` | Mock network events avec JSON structure invalide (clés manquantes) | Appeler `search_service.search_flights(SearchRequest)` | Logger ERROR parsing failed, skip combinaison (pas d'exception bloquante), retourne résultats partiels autres combinaisons |
| 5 | `test_integration_validation_flights_length` | Mock FlightParser retournant 2 flights pour 3 segment_dates (données incohérentes) | Créer `FlightCombinationResult` avec données incohérentes | Lève `ValidationError` Pydantic avec message clair "flights length != segment_dates length" |
| 6 | `test_integration_end_to_end_complete_data` | Application FastAPI TestClient avec network capture activé, mock 3 segments multi-city | POST `/api/v1/search-flights` avec body 3 segments | Status 200, JSON response conforme schema avec `results[i].flights` length=3 pour chaque result, total_results=10 |
| 7 | `test_integration_resource_blocking_reduces_requests` | Mock Playwright avec tracking requêtes bloquées, hook ResourceBlocking activé | Crawl page Google Flights mock avec 50 requêtes (20 images, 10 fonts, 20 essentielles) | ≥30 requêtes bloquées (images + fonts), 20 requêtes passent (xhr, scripts), logs DEBUG montrent blocage |

**Total tests intégration** : 7 tests

---

**TOTAL TESTS** : 22 unitaires + 7 intégration = **29 tests**

---

## Exemples JSON

**Exemple 1 : Network Event Capturé (API Response Google Flights)**

```json
{
  "event_type": "response",
  "url": "https://www.google.com/travel/flights/rpc/search?hl=fr",
  "status": 200,
  "status_text": "OK",
  "resource_type": "xhr",
  "request_timing": {
    "start_time": 1234567890.123,
    "response_time": 1234567891.456
  },
  "headers": {
    "content-type": "application/json; charset=UTF-8"
  },
  "response_data": "{\"data\": {\"flights\": [{\"id\": \"combo1\", \"price\": {\"total\": 1270.0, \"currency\": \"EUR\"}, \"segments\": [...]}]}}"
}
```

**Contexte** : Event network capturé par Crawl4AI, type "response", resource_type "xhr" (API call), status 200, body JSON brut dans `response_data`.

---

**Exemple 2 : JSON API Google Flights Multi-City (3 Segments)**

```json
{
  "data": {
    "flights": [
      {
        "id": "flight_combination_abc123",
        "price": {
          "total": 1270.0,
          "currency": "EUR"
        },
        "segments": [
          {
            "segment_index": 0,
            "departure": {
              "airport": "CDG",
              "city": "Paris",
              "time": "2025-06-01T10:30:00Z"
            },
            "arrival": {
              "airport": "NRT",
              "city": "Tokyo",
              "time": "2025-06-02T06:45:00Z"
            },
            "carrier": {
              "name": "ANA",
              "code": "NH"
            },
            "duration_minutes": 765,
            "stops": 0
          },
          {
            "segment_index": 1,
            "departure": {
              "airport": "NRT",
              "city": "Tokyo",
              "time": "2025-06-15T08:00:00Z"
            },
            "arrival": {
              "airport": "KIX",
              "city": "Kyoto",
              "time": "2025-06-15T09:30:00Z"
            },
            "carrier": {
              "name": "JAL",
              "code": "JL"
            },
            "duration_minutes": 90,
            "stops": 0
          },
          {
            "segment_index": 2,
            "departure": {
              "airport": "KIX",
              "city": "Kyoto",
              "time": "2025-06-22T14:00:00Z"
            },
            "arrival": {
              "airport": "CDG",
              "city": "Paris",
              "time": "2025-06-23T06:30:00Z"
            },
            "carrier": {
              "name": "Air France",
              "code": "AF"
            },
            "duration_minutes": 810,
            "stops": 1
          }
        ]
      }
    ]
  }
}
```

**Contexte** : Structure JSON observée empiriquement depuis API Google Flights (format non documenté officiel), contient 1 flight combination avec 3 segments complets (Paris→Tokyo, Tokyo→Kyoto, Kyoto→Paris).

---

**Exemple 3 : FlightCombinationResult Complet (Story 8) - Architecture Corrigée**

```json
{
  "segment_dates": ["2025-06-01", "2025-06-15", "2025-06-22"],
  "total_price": 1270.0,
  "flights": [
    {
      "airline": "ANA",
      "departure_time": "10:30",
      "arrival_time": "06:45+1",
      "duration": "12h 45min",
      "stops": 0,
      "departure_airport": "Paris",
      "arrival_airport": "Tokyo"
    },
    {
      "airline": "JAL",
      "departure_time": "08:00",
      "arrival_time": "09:30",
      "duration": "1h 30min",
      "stops": 0,
      "departure_airport": "Tokyo",
      "arrival_airport": "Kyoto"
    },
    {
      "airline": "Air France",
      "departure_time": "14:00",
      "arrival_time": "06:30+1",
      "duration": "13h 30min",
      "stops": 1,
      "departure_airport": "Kyoto",
      "arrival_airport": "Paris"
    }
  ]
}
```

**Notes** :
- `segment_dates` : 3 dates départ segments itinéraire multi-city
- `total_price` : ✅ **Prix total itinéraire complet (1270€) au niveau racine** - représente somme prix 3 segments combinés
- `flights` : Liste 3 flights (1 par segment), validation Pydantic vérifie `len(flights) == len(segment_dates)`
- `flights[i]` : ❌ **SANS champ price individuel** - Google Flights API ne fournit pas prix par segment isolé, seulement prix total itinéraire
- `departure_airport` / `arrival_airport` : Noms villes (pas codes IATA) pour lisibilité user

---

**Exemple 4 : SearchResponse Top 10 avec Données Complètes (Story 8) - Architecture Corrigée**

```json
{
  "results": [
    {
      "segment_dates": ["2025-06-01", "2025-06-15", "2025-06-22"],
      "total_price": 1270.0,
      "flights": [
        {
          "airline": "ANA",
          "departure_time": "10:30",
          "arrival_time": "06:45+1",
          "duration": "12h 45min",
          "stops": 0,
          "departure_airport": "Paris",
          "arrival_airport": "Tokyo"
        },
        {
          "airline": "JAL",
          "departure_time": "08:00",
          "arrival_time": "09:30",
          "duration": "1h 30min",
          "stops": 0,
          "departure_airport": "Tokyo",
          "arrival_airport": "Kyoto"
        },
        {
          "airline": "Air France",
          "departure_time": "14:00",
          "arrival_time": "06:30+1",
          "duration": "13h 30min",
          "stops": 1,
          "departure_airport": "Kyoto",
          "arrival_airport": "Paris"
        }
      ]
    },
    {
      "segment_dates": ["2025-06-03", "2025-06-17", "2025-06-25"],
      "total_price": 1320.0,
      "flights": [
        {
          "airline": "Air France",
          "departure_time": "11:00",
          "arrival_time": "07:15+1",
          "duration": "13h 15min",
          "stops": 0,
          "departure_airport": "Paris",
          "arrival_airport": "Tokyo"
        },
        {
          "airline": "ANA",
          "departure_time": "09:30",
          "arrival_time": "11:00",
          "duration": "1h 30min",
          "stops": 0,
          "departure_airport": "Tokyo",
          "arrival_airport": "Kyoto"
        },
        {
          "airline": "Lufthansa",
          "departure_time": "15:30",
          "arrival_time": "08:00+1",
          "duration": "14h 30min",
          "stops": 2,
          "departure_airport": "Kyoto",
          "arrival_airport": "Paris"
        }
      ]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 48500,
    "segments_count": 3
  }
}
```

**Contexte** : Response complète top 10 résultats multi-city après migration Story 8, chaque result contient `total_price` au niveau racine + 3 flights (tous segments SANS price individuel), triés par `total_price` croissant (1270€ < 1320€).

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Network capture activé** : CrawlerService configure `CrawlerRunConfig` avec `capture_network_requests=True`, `wait_until="networkidle"`, `delay_before_return_html=2.0` (vérifié config object)

2. **Tous network events capturés** : `result.network_requests` contient liste events non-vide après crawl Google Flights (vérifié length > 0)

3. **Filtrage API responses correct** : NetworkResponseFilter garde seulement events `event_type="response"`, `status=200`, `resource_type in ["xhr","fetch"]`, URL contient "google.com" (vérifié assertion filtering)

4. **Parsing JSON multi-segments** : FlightParser extrait exactement 3 `GoogleFlightDTO` depuis JSON API pour itinéraire 3 segments (vérifié `len(flights) == 3`)

5. **Données complètes 3 segments** : Chaque `FlightCombinationResult.flights` contient 3 flights avec airline, times, duration, stops valides (vérifié aucun champ None)

6. **Validation cohérence segments** : Pydantic validator vérifie `len(flights) == len(segment_dates)`, lève `ValidationError` si incohérent (vérifié exception levée)

7. **Prix total au niveau racine** : `FlightCombinationResult.total_price` contient prix total multi-city complet (ex: 1270€ pour 3 segments) au niveau racine, PAS dans `flights[i].price` (vérifié structure JSON response)

8. **Flights sans price individuel** : Chaque `GoogleFlightDTO` dans `flights` liste ne contient PAS champ `price` (Google Flights API ne fournit pas prix par segment isolé, seulement total itinéraire)

9. **Ordre segments respecté** : `flights[0]` = segment 1 (Paris→Tokyo), `flights[1]` = segment 2 (Tokyo→Kyoto), `flights[2]` = segment 3 (Kyoto→Paris) (vérifié departure/arrival airports ordonnés)

10. **Ranking modifié** : Top 10 ranking trie par `total_price` croissant (nouveau champ racine), pas `flights[0].price` (vérifié results[0].total_price ≤ results[1].total_price)

11. **Resource blocking activé** : Hook `on_page_context_created` enregistré dans `CrawlerRunConfig.hooks` avec fonction `optimize_google_flights_bandwidth` (vérifié config object)

12. **Domaines non essentiels bloqués** : Requêtes vers `fonts.gstatic.com`, `fonts.googleapis.com`, `*.doubleclick.net` bloquées via `route.abort()` (vérifié logs DEBUG blocage)

13. **Resource types lourds bloqués** : Requêtes `resource_type in ["image", "font", "media"]` bloquées, XHR/Fetch/Script autorisées (vérifié route filter logic)

## Critères techniques

14. **Type hints PEP 695** : NetworkResponseFilter, FlightParser.parse_api_responses, ResourceBlockingHook annotés avec type hints modernes (`list[dict]`, `tuple[float, list[GoogleFlightDTO]]`, `Page`, `BrowserContext`)

15. **Async/Await cohérent** : CrawlerService.crawl_google_flights reste async, utilise `await crawler.arun()`, compatibilité Story 7 retry logic préservée

16. **Configuration centralisée** : CrawlerRunConfig créée avec params network capture + hooks groupés (capture_network_requests, wait_until, delay, hooks), réutilisable tests

17. **Pydantic v2 validations** : FlightCombinationResult.flights validator `mode='after'` avec accès `ValidationInfo` pour comparaison `segment_dates` length, validator `total_price` vérifie ≥ 0

18. **JSON parsing résilient** : FlightParser gère `json.JSONDecodeError` avec try/except, lève `ParsingError` custom avec message clair (pas crash)

19. **Fallback gracieux** : Si `network_requests=[]` vide → Logger WARNING, retourne résultats partiels disponibles (pas d'exception bloquante)

20. **Logging structuré JSON complet** : Logs network capture incluent : events_captured_count, api_responses_filtered_count, segments_parsed_count, total_price_extracted, resources_blocked_count

21. **Extraction clés JSON robuste** : Parser utilise `.get()` avec defaults pour clés optionnelles (ex: `segment.get("duration", 0)`), évite KeyError

22. **Séparation prix/segments** : FlightParser retourne tuple `(total_price, flights)` pas seulement `list[GoogleFlightDTO]`, caller gère construction FlightCombinationResult avec prix séparé

23. **Hook async compatible** : ResourceBlockingHook fonction async avec signature `(Page, BrowserContext, **kwargs) -> Page`, compatible Crawl4AI hooks system

## Critères qualité

24. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code NetworkResponseFilter, FlightParser JSON parsing, ResourceBlockingHook, CrawlerService network config (pytest-cov)

25. **29 tests passent** : 22 tests unitaires (6 NetworkResponseFilter + 7 FlightParser + 5 CrawlerService + 4 ResourceBlockingHook) + 7 tests intégration tous verts (pytest -v)

26. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

27. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

28. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler network events configurés

29. **Docstrings 1 ligne** : NetworkResponseFilter, FlightParser et ResourceBlockingHook avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

30. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON, structures API (pas d'implémentation complète méthodes)

31. **Commits conventional** : Story 8 committée avec message `feat(crawler): add network capture for complete multi-city data` conforme Conventional Commits

---

**Note importante** : Story complexité élevée (8 story points) → 31 critères couvrent exhaustivement migration CSS→Network capture (13 fonctionnels incluant architecture prix corrigée + bandwidth optimization), architecture parsing JSON résilient + hooks (10 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (3 flights parsés, validation length, ~40-60% bandwidth réduit), **M**esurable (29 tests passent, coverage ≥80%), **A**tteignable (Crawl4AI 0.7.7+ network capture + hooks mature), **R**elevant (données 3x plus complètes pour UX multi-city + coûts Decodo optimisés), **T**emporel (MVP Phase 5-6, après CrawlerService/FlightParser Story 4-6 déjà implémentés).

**Migration Impact** : ⚠️ **2 Breaking changes API response structure** :
1. `flights` length passe de 1 à N segments (clients doivent itérer liste complète)
2. **ARCHITECTURE CORRIGÉE** : `total_price` déplacé au niveau racine `FlightCombinationResult`, plus dans `flights[i].price` (clients doivent accéder `result.total_price` au lieu de `result.flights[0].price`)

Nécessite coordination clients API pour adapter parsing responses. **Avantages** : Architecture logique (prix total = niveau itinéraire, pas segment individuel) + gain données 300% + réduction bandwidth ~40-60% via resource blocking.
