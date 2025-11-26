---
title: "Story 12: Polling Mechanism + Timeout"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-4/story-11"]
date: "2025-25-11"
keywords: ["kayak", "polling", "timeout", "async", "status", "network-capture", "xhr-interception", "timing-optimization"]
scope: ["specs"]
technologies: ["Python", "asyncio", "Crawl4AI", "Playwright"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Résultats progressifs Kayak** : Contrairement à Google Flights qui charge résultats rapidement (10-15s), Kayak utilise polling progressif pouvant prendre 45-90s pour completion totale, utilisateurs attendent résultats rapides sans timeout
- **Stratégie smart first batch** : Kayak trie résultats par "bestflight" donc meilleurs prix apparaissent dans premier batch (15-25s), pas besoin attendre status=complete pour Top 10 valides
- **Timeout gracieux** : Si polling dépasse 45s (seuil raisonnable), retourner premiers résultats disponibles plutôt que échouer totalement, garantit UX dégradée mais fonctionnelle
- **Transparence latence** : Utilisateurs doivent voir indication durée recherche Kayak (plus long que Google Flights), logs structurés permettent monitoring performance real-time

## Contraintes métier

- **Polling non documenté** : API interne Kayak `/api/search/V8/flight/poll` non officielle, structure JSON peut changer, nécessite parsing résilient avec fallback
- **Coûts bandwidth variables** : Polling continu consomme bandwidth Decodo (chaque poll = requête proxy), stratégie first batch minimise polls tout en garantissant données Top 10
- **Performance variable** : Timing Kayak dépend complexité recherche (multi-city 3 segments plus lent que aller-retour simple), configuration timeout doit s'adapter via Settings
- **Anti-détection critique** : Délais randomisés entre polls (4-8s) essentiels pour éviter pattern bot détectable, trop rapide = risque captcha/ban

## Valeur business

- **Résultats 2x plus rapides** : Stratégie first batch (20-25s) vs polling complet (45-90s) = 50-75% réduction latence perçue tout en gardant qualité Top 10 résultats
- **Différenciation source Kayak** : Offrir Kayak comme source alternative Google Flights = valeur ajoutée client (comparaison cross-platform, layover détails Kayak supérieurs)
- **Fallback robuste** : Timeout gracieux garantit 0% échecs totaux si Kayak lent, toujours retourner résultats partiels = fiabilité API renforcée
- **Foundation monitoring** : Logs timing détaillés permettent analytics futures (médiane temps polling, taux timeout, corrélation segments/latence) pour optimisations post-MVP

## Métriques succès

- **Taux first batch success** : ≥90% recherches Kayak retournent résultats exploitables en <30s (premier batch suffisant pour Top 10)
- **Zéro timeout fatal** : 100% recherches avec timeout retournent résultats partiels (pas d'exception bloquante), logging WARNING si timeout atteint
- **Latence médiane** : Médiane temps polling <25s pour multi-city 3 segments, <20s pour aller-retour simple (objectif performance)
- **Anti-détection efficace** : 0% captchas durant polling (délais randomisés 4-8s prouvés suffisants), taux succès ≥95%
- **Coverage tests** : ≥80% sur KayakPollingService, KayakPollingConfig, intégration CrawlerService polling flow

---

# 📋 Spécifications Techniques

## 1. KayakPollingConfig (Pydantic Settings)

**Rôle** : Configuration centralisée timing et comportement polling Kayak, séparée de GoogleFlightsConfig pour permettre tuning indépendant.

**Interface** :
```python
class KayakPollingConfig(BaseSettings):
    """Configuration timing et comportement polling Kayak."""

    page_load_timeout: int
    first_results_wait: int
    max_total_wait: int
    poll_interval_min: int
    poll_interval_max: int
```

**Champs** :

| Champ | Type | Valeur Défaut | Description | Contraintes |
|-------|------|---------------|-------------|-------------|
| `page_load_timeout` | `int` | `30` | Timeout chargement page initial Kayak (secondes) | ≥ 10, ≤ 60 |
| `first_results_wait` | `int` | `20` | Attente premier batch résultats après page load (secondes) | ≥ 10, ≤ 40 |
| `max_total_wait` | `int` | `45` | Timeout total polling avant fallback gracieux (secondes) | ≥ 30, ≤ 120 |
| `poll_interval_min` | `int` | `4` | Intervalle minimum entre polls anti-détection (secondes) | ≥ 2, ≤ 10 |
| `poll_interval_max` | `int` | `8` | Intervalle maximum entre polls randomisé (secondes) | ≥ `poll_interval_min`, ≤ 15 |

**Comportement** :

**Configuration Pydantic BaseSettings** :
- `env_prefix="KAYAK_"` : Préfixe variables environnement pour isolation namespace (ex: `KAYAK_PAGE_LOAD_TIMEOUT=35`)
- `extra="forbid"` : Rejette champs inconnus avec ValidationError (protection contre typos config)
- Fallback valeurs défaut si env vars absentes (configuration MVP optimisée selon observations timing)
- Validation Pydantic lève `ValidationError` si contraintes violées (ex: `max_total_wait < 30`)

**Validations Pydantic** :

```python
@field_validator('poll_interval_max', mode='after')
@classmethod
def validate_poll_interval_max(cls, v: int, info: ValidationInfo) -> int:
    """Vérifie poll_interval_max >= poll_interval_min (cohérence range randomisation)."""
```

**Edge cases** :
- **poll_interval_max < poll_interval_min** : Validation Pydantic lève exception avec message clair
- **max_total_wait trop court** : Logger WARNING si <30s (risque aucun résultat capturé), autoriser mais signaler
- **Configuration production vs dev** : Env vars permettent tuning prod (ex: `KAYAK_MAX_TOTAL_WAIT=60` si infrastructure lente)

**Erreurs levées** :
- `ValidationError` : Si contraintes champs violées (ex: timeout négatif)

**Logging structuré** :
- INFO : Configuration polling chargée avec valeurs effectives (timeout, intervals)
- DEBUG : Valeurs par défaut vs overrides env vars

---

## 2. KayakPollingService

**Rôle** : Service async gérant polling network capture Kayak pour intercepter XHR `/api/search/` et `/poll` progressivement jusqu'à obtenir résultats exploitables ou timeout.

**Interface** :
```python
class KayakPollingService:
    """Service polling async pour capturer API responses Kayak."""

    def __init__(self, config: KayakPollingConfig):
        """Initialise service avec configuration timing."""

    async def wait_for_results(self, page: Page) -> dict:
        """
        Attend premiers résultats Kayak via network capture XHR.

        Returns:
            Dict JSON première API response contenant results[] non vide
        """
```

**Dépendances** :

| Dépendance | Type | Utilisation |
|------------|------|-------------|
| `KayakPollingConfig` | Injection | Configuration timeouts et intervals |
| `playwright.async_api.Page` | Argument | Page Playwright pour capture network |
| `asyncio.sleep()` | Stdlib | Délais randomisés entre checks |
| `random.randint()` | Stdlib | Randomisation interval polling anti-détection |

**Comportement `wait_for_results()`** :

**Étape 1 : Configuration network capture listener**
1. Enregistrer listener Playwright `page.on("response", on_response_handler)` pour intercepter XHR/Fetch
2. Créer liste partagée `captured_responses: list[dict]` pour stocker responses capturées (accès async safe)
3. Handler `on_response_handler` filtre uniquement responses :
   - URL contient `/api/search/` OU `/poll`
   - Status code 200
   - Content-Type `application/json`
   - Ajoute response JSON parsée à `captured_responses` liste

**Étape 2 : Polling loop avec timeout**
4. Initialiser `start_time = time.time()`
5. Boucle `while True` :
   - Vérifier `time.time() - start_time > config.max_total_wait` → Si timeout dépassé, sortir boucle (fallback gracieux)
   - Itérer `captured_responses` liste pour trouver première response avec `results[]` non vide et `len(results) >= 10`
   - Si trouvé → Retourner dict JSON (polling terminé avec succès)
   - Si pas trouvé → Attendre délai randomisé `await asyncio.sleep(randint(poll_interval_min, poll_interval_max))`
   - Logger DEBUG chaque itération avec elapsed time et nombre responses capturées

**Étape 3 : Retour résultats ou timeout gracieux**
6. Si boucle sortie par timeout :
   - Logger WARNING avec timing total et nombre responses capturées
   - Retourner première response avec `results[]` non vide (même si <10 résultats) OU dict vide si aucune
7. Si résultats trouvés avant timeout :
   - Logger INFO avec timing success et nombre résultats capturés
   - Retourner dict JSON complet

**Edge cases** :
- **Aucune API response capturée** : Si `captured_responses=[]` après timeout → Retourner dict vide `{}`, caller gère fallback (pas d'exception)
- **results[] vide toutes responses** : Si toutes responses ont `results=[]` → Logger WARNING, retourner dict vide après timeout
- **Multiples API endpoints** : Kayak peut appeler `/start`, `/poll`, `/filters` → Garder tous, prioriser `/poll` avec results[] non vide
- **Timeout dépassé immédiatement** : Si `max_total_wait=0` (config invalide mais possible) → Sortir immédiatement, retourner vide

**Erreurs levées** :
- Aucune exception levée directement (méthode défensive, retourne dict vide si échec)
- `json.JSONDecodeError` capturée si response body pas JSON valide → Ignorer response, continuer polling

**Logging structuré** :

| Event | Niveau | Extra Fields |
|-------|--------|--------------|
| Début polling | INFO | `page_url`, `max_total_wait`, `poll_interval` |
| Chaque poll check | DEBUG | `elapsed_time`, `responses_captured_count`, `iteration_number` |
| Timeout atteint | WARNING | `total_time`, `responses_captured`, `results_partial` |
| Success avant timeout | INFO | `total_time`, `results_count`, `api_endpoint_used` |
| JSON parsing error | DEBUG | `url`, `error_message` (continue polling) |

---

## 3. CrawlerService (Intégration Kayak Polling)

**Rôle** : Adapter CrawlerService existant (Story 8 network capture) pour supporter polling Kayak avec délais configurables et network listener.

**Modifications Interface** :

Aucune modification signature publique `crawl_google_flights()`, ajout méthode séparée :

```python
class CrawlerService:
    """Service crawling multi-providers (Google Flights + Kayak)."""

    async def crawl_kayak_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True
    ) -> tuple[CrawlResult, dict]:
        """
        Crawl URL Kayak avec polling network capture.

        Returns:
            Tuple (CrawlResult, api_response_dict) avec HTML + première API response JSON
        """
```

**Comportement `crawl_kayak_flights()`** :

**Étape 1 : Configuration crawler avec network capture**
1. Créer `CrawlerRunConfig` avec :
   - `capture_network_requests=True` (réutilise Story 8 network capture)
   - `wait_until="domcontentloaded"` (pas networkidle car polling manuel)
   - `delay_before_return_html=2.0` (laisser page initialiser listeners)
   - Proxy config si `use_proxy=True` (inchangé Story 5)
   - Stealth mode browser config (inchangé Story 6)

**Étape 2 : Crawl page initial + consent**
2. Appeler `await crawler.arun(url, config=config)` dans async context manager
3. Accéder `page: Page` depuis `crawler._browser.contexts[0].pages[0]` (Playwright page active)
4. Appeler `ConsentHandler.handle_kayak_consent(page)` si popup présent (Story 4.1)

**Étape 3 : Polling avec KayakPollingService**
5. Instancier `KayakPollingService(config=kayak_polling_config)`
6. Appeler `api_response = await polling_service.wait_for_results(page)` avec timeout géré
7. Si `api_response` vide (timeout sans résultats) → Logger ERROR, retourner tuple `(result, {})`

**Étape 4 : Retour données complètes**
8. Retourner tuple `(CrawlResult, api_response)` avec :
   - `CrawlResult` contient HTML + network_requests capturés (fallback parsing HTML si besoin)
   - `api_response` dict JSON première response exploitable (results[] non vide)

**Edge cases** :
- **Captcha détecté durant polling** : Vérifier HTML après page load, si captcha → Lève `CaptchaDetectedError` avant polling (éviter waste polling loop)
- **Page crash durant polling** : Try/except autour `page.on()` listener, si crash → Logger ERROR, retourner résultats partiels
- **Multiples pages Playwright** : Assurer utiliser première page active (index 0), pas créer nouvelle page

**Erreurs levées** :
- `CaptchaDetectedError` : Si captcha détecté dans HTML initial (avant polling)
- `NetworkError` : Si timeout crawler ou erreur Playwright durant page load
- Polling timeout ne lève PAS exception (retourne dict vide, caller gère)

**Logging structuré** :
- INFO : Début crawl Kayak avec polling enabled
- DEBUG : Page loaded, consent handled, polling started
- WARNING : Polling timeout atteint sans résultats complets
- ERROR : Captcha détecté ou page crash durant polling

---

## 4. NetworkCaptureListener (Utilitaire Playwright)

**Rôle** : Utilitaire helper pour enregistrer listener Playwright `page.on("response")` avec filtrage Kayak-specific et stockage async-safe.

**Interface** :
```python
class NetworkCaptureListener:
    """Helper network capture pour polling Kayak."""

    def __init__(self):
        """Initialise liste thread-safe pour responses capturées."""

    def create_handler(self) -> Callable[[Response], Awaitable[None]]:
        """
        Créer handler async pour page.on("response").

        Returns:
            Handler filtrant responses Kayak API et stockant JSON
        """

    def get_captured_responses(self) -> list[dict]:
        """Retourne copie liste responses capturées."""
```

**Comportement** :

**Stockage thread-safe** :
- Liste interne `_captured: list[dict]` protégée par `asyncio.Lock()` pour accès concurrent safe
- Handler async ajoute responses via `async with self._lock: self._captured.append(data)`

**Filtrage handler** :
- Vérifier `response.request.resource_type in ["xhr", "fetch"]` (API calls uniquement)
- Vérifier `response.status == 200` (succès uniquement)
- Vérifier URL contient `/api/search/` OU `/poll` (endpoints Kayak spécifiques)
- Parser body via `await response.json()` (try/except si body pas JSON)

**Edge cases** :
- **JSON parsing fail** : Ignorer response silencieusement (logger DEBUG), continuer capture autres
- **Response body vide** : Ignorer si `body` None ou empty string
- **Lock contention** : Lock automatiquement released via context manager, pas de deadlock

**Erreurs levées** :
- Aucune exception levée (handler silencieux, ignore responses invalides)

**Logging structuré** :
- DEBUG : Chaque response capturée avec URL et content-length
- DEBUG : Response ignorée (status non-200, type non-xhr, JSON invalid)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### KayakPollingConfig (5 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_config_default_values` | Config avec valeurs défaut si env vars absentes | Pas d'env vars `KAYAK_*` | `page_load_timeout=30`, `first_results_wait=20`, `max_total_wait=45`, intervals=4-8s | Vérifie defaults MVP optimisés |
| 2 | `test_config_env_override` | Env vars overrides valeurs défaut | `KAYAK_MAX_TOTAL_WAIT=60` | `max_total_wait=60` (override), autres defaults | Vérifie lecture env vars avec prefix |
| 3 | `test_config_validates_poll_interval` | Validation `poll_interval_max >= min` | `poll_interval_min=10`, `poll_interval_max=5` | Lève `ValidationError` message clair | Vérifie cohérence range randomisation |
| 4 | `test_config_validates_min_timeout` | Validation `max_total_wait >= 30` (warning) | `max_total_wait=10` | Config créée mais logger WARNING | Vérifie contrainte minimum timeout |
| 5 | `test_config_extra_forbid` | Champs inconnus rejetés | `unknown_field="value"` | Lève `ValidationError` "extra fields not permitted" | Vérifie Pydantic `extra="forbid"` |

### KayakPollingService (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 6 | `test_wait_for_results_first_batch` | Résultats trouvés dans premier batch (<20s) | Mock Page avec response JSON `results[]` length=10 après 15s | Retourne dict JSON avec 10 résultats, elapsed time ~15s | Vérifie success early exit polling |
| 7 | `test_wait_for_results_timeout` | Timeout atteint sans résultats complets | Mock Page sans responses valides, timeout 5s | Retourne dict vide `{}`, logger WARNING, elapsed time ≥5s | Vérifie fallback gracieux timeout |
| 8 | `test_wait_for_results_partial` | Timeout avec résultats partiels (<10) | Mock Page avec response `results[]` length=5, timeout atteint | Retourne dict avec 5 résultats (partiel), logger WARNING | Vérifie retour meilleur effort si timeout |
| 9 | `test_polling_randomized_intervals` | Délais polling randomisés anti-détection | Mock config intervals 4-8s, 3 polls | Chaque sleep duration entre 4-8s (vérifié via mock `asyncio.sleep`) | Vérifie randomisation appliquée |
| 10 | `test_polling_ignores_invalid_json` | Responses JSON invalides ignorées | Mock Page avec 2 responses : 1 JSON valide, 1 invalid | Retourne response valide (ignore invalid), pas d'exception | Vérifie parsing résilient JSON |
| 11 | `test_polling_filters_empty_results` | Responses avec `results=[]` ignorées | Mock Page avec 3 responses : 2 avec `results=[]`, 1 avec `results=[...]` | Retourne response avec results non-empty | Vérifie filtrage results vides |
| 12 | `test_polling_multiple_api_endpoints` | Multiples endpoints capturés (`/start`, `/poll`) | Mock Page avec responses `/start` (no results) + `/poll` (results) | Retourne response `/poll` (priorisée), ignore `/start` | Vérifie sélection endpoint correct |
| 13 | `test_polling_elapsed_time_logging` | Logs structurés chaque itération | Mock Page avec 3 polls avant success | Logs DEBUG contiennent `elapsed_time`, `iteration_number`, `responses_captured_count` | Vérifie observabilité timing |

### NetworkCaptureListener (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 14 | `test_listener_filters_xhr_only` | Garde seulement XHR/Fetch responses | Mock responses : 2 xhr, 1 image, 1 script | Liste capturée length=2 (xhr uniquement) | Vérifie filtrage resource type |
| 15 | `test_listener_filters_status_200` | Garde seulement status 200 | Mock responses : 2 status 200, 1 status 404 | Liste capturée length=2 (200 uniquement) | Vérifie exclusion erreurs HTTP |
| 16 | `test_listener_filters_kayak_urls` | Garde seulement URLs `/api/search/` ou `/poll` | Mock responses : 2 URLs valides Kayak, 1 URL tierce | Liste capturée length=2 (Kayak uniquement) | Vérifie pattern matching URL |
| 17 | `test_listener_thread_safe_concurrent` | Accès concurrent async-safe | Simuler 10 responses ajoutées concurrently via `asyncio.gather()` | Liste capturée length=10, pas de race condition | Vérifie Lock protection liste |

### CrawlerService Kayak Integration (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 18 | `test_crawl_kayak_with_polling` | Crawl Kayak complet avec polling | Mock AsyncWebCrawler + KayakPollingService returning results | Tuple `(CrawlResult, dict)` avec HTML + JSON response | Vérifie intégration bout-en-bout |
| 19 | `test_crawl_kayak_timeout_fallback` | Polling timeout retourne résultats partiels | Mock polling service returning empty dict (timeout) | Tuple `(CrawlResult, {})`, logger ERROR, pas d'exception | Vérifie fallback gracieux timeout |
| 20 | `test_crawl_kayak_captcha_detected` | Captcha détecté avant polling | Mock HTML avec captcha pattern | Lève `CaptchaDetectedError` avant polling start | Vérifie early captcha check |

**Total tests unitaires** : 5 (Config) + 8 (PollingService) + 4 (Listener) + 3 (CrawlerService) = **20 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_kayak_polling_first_batch` | Mock CrawlerService + KayakPollingService avec responses arrivant après 20s | Appeler `crawler_service.crawl_kayak_flights(url)` | Retourne résultats en ~20s, API response contient `results[]` length≥10, pas de timeout |
| 2 | `test_integration_kayak_polling_timeout_graceful` | Mock polling service avec delay >45s (timeout atteint) | Appeler `crawler_service.crawl_kayak_flights(url)` | Retourne résultats partiels si disponibles sinon dict vide, logger WARNING, pas d'exception levée |
| 3 | `test_integration_kayak_vs_google_timing` | Mock CrawlerService avec Google Flights (10-15s) vs Kayak (20-25s) | Appeler les 2 méthodes crawl successivement | Google timing <15s, Kayak timing ~20-25s (2x plus lent), logs montrent différence latence |

**Total tests intégration** : 3 tests

---

**TOTAL TESTS** : 20 unitaires + 3 intégration = **23 tests**

---

## Exemples JSON

**Exemple 1 : API Response Kayak Première Batch**

```json
{
  "status": "polling",
  "searchStatus": {
    "tripType": "multicity",
    "legs": [
      {"origin": "PAR", "destination": "SLZ", "date": "2026-01-14"},
      {"origin": "SLZ", "destination": "LIM", "date": "2026-03-28"},
      {"origin": "LIM", "destination": "PAR", "date": "2026-04-10"}
    ]
  },
  "results": [
    {
      "resultId": "result_abc123",
      "price": 1250.00,
      "legs": ["leg_id_1", "leg_id_2", "leg_id_3"]
    },
    {
      "resultId": "result_def456",
      "price": 1320.00,
      "legs": ["leg_id_4", "leg_id_5", "leg_id_6"]
    }
  ],
  "legs": {
    "leg_id_1": {
      "duration": 765,
      "stops": 0,
      "segments": ["seg_1"]
    }
  },
  "segments": {
    "seg_1": {
      "airline": "AF",
      "flightNumber": "123",
      "origin": "CDG",
      "destination": "SLZ",
      "departure": "2026-01-14T10:30:00",
      "arrival": "2026-01-14T18:45:00",
      "duration": 495
    }
  }
}
```

**Contexte** : Première API response capturée après ~20s polling, `status="polling"` (pas encore complete) mais `results[]` déjà contient 2 options exploitables, structure dénormalisée avec refs legs/segments.

---

**Exemple 2 : Configuration Polling MVP**

```json
{
  "page_load_timeout": 30,
  "first_results_wait": 20,
  "max_total_wait": 45,
  "poll_interval_min": 4,
  "poll_interval_max": 8
}
```

**Contexte** : Configuration par défaut KayakPollingConfig optimisée selon observations timing Kayak (MVP Phase 6), balance rapidité (45s max) vs qualité résultats (20s first batch suffisant Top 10).

---

**Exemple 3 : Logs Structurés Polling Success**

```json
{
  "timestamp": "2025-11-25T14:30:25.123Z",
  "level": "INFO",
  "logger": "kayak_polling_service",
  "message": "Kayak polling completed successfully",
  "extra": {
    "total_time_seconds": 22.5,
    "results_count": 12,
    "api_endpoint_used": "/api/search/V8/flight/poll",
    "iterations": 3,
    "status": "success"
  }
}
```

**Contexte** : Log structuré après polling success en 22.5s (3 itérations avec délais randomisés 4-8s), 12 résultats capturés (>10 requis Top 10), endpoint `/poll` utilisé.

---

**Exemple 4 : Logs Structurés Polling Timeout**

```json
{
  "timestamp": "2025-11-25T14:31:15.456Z",
  "level": "WARNING",
  "logger": "kayak_polling_service",
  "message": "Kayak polling timeout reached, returning partial results",
  "extra": {
    "total_time_seconds": 45.2,
    "responses_captured": 5,
    "results_partial": 7,
    "status": "timeout"
  }
}
```

**Contexte** : Log WARNING après timeout 45s atteint, 5 responses capturées dont 7 résultats partiels (insuffisant Top 10 mais retournés quand même), fallback gracieux sans exception.

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Configuration polling centralisée** : KayakPollingConfig créée avec 5 champs (timeouts, intervals), valeurs défaut MVP optimisées (30/20/45s, 4-8s intervals), lecture env vars `KAYAK_*` (vérifié config object)

2. **Polling first batch success** : KayakPollingService détecte premiers résultats Kayak en <25s (médiane), retourne dict JSON avec `results[]` length≥10 sans attendre `status=complete` (vérifié timing logs)

3. **Timeout gracieux** : Si polling dépasse `max_total_wait` (45s défaut) sans résultats complets, retourne résultats partiels disponibles ou dict vide, logger WARNING, aucune exception levée (vérifié retour non-null)

4. **Délais randomisés anti-détection** : Intervalle entre polls randomisé via `randint(poll_interval_min, poll_interval_max)` (4-8s défaut), chaque itération utilise délai différent (vérifié mock `asyncio.sleep` calls)

5. **Network capture Kayak-specific** : NetworkCaptureListener filtre responses XHR/Fetch avec URL contenant `/api/search/` OU `/poll`, status 200, body JSON valide (vérifié liste capturée)

6. **Intégration CrawlerService** : Nouvelle méthode `crawl_kayak_flights()` réutilise network capture Story 8, ajoute polling service, retourne tuple `(CrawlResult, api_response_dict)` (vérifié signature)

7. **Early exit polling** : Si résultats suffisants trouvés avant timeout (ex: après 20s), polling s'arrête immédiatement sans attendre `max_total_wait` (vérifié elapsed time logs)

8. **Parsing JSON résilient** : Responses JSON invalides ignorées silencieusement (logger DEBUG), polling continue sans crash, retourne première response valide (vérifié try/except `json.JSONDecodeError`)

9. **Captcha detection avant polling** : Vérifier HTML captcha pattern après page load initial, si détecté → lève `CaptchaDetectedError` avant démarrer polling loop (éviter waste bandwidth)

10. **Logs timing détaillés** : Chaque itération polling loggée DEBUG avec `elapsed_time`, `iteration_number`, `responses_captured_count`, log final INFO/WARNING avec `total_time`, `results_count`, `status` (vérifié structure JSON logs)

## Critères techniques

11. **Type hints PEP 695** : KayakPollingConfig, KayakPollingService, NetworkCaptureListener annotés avec type hints modernes (`int`, `dict`, `Page`, `Callable[[Response], Awaitable[None]]`)

12. **Async/Await cohérent** : Toutes méthodes polling async (`async def wait_for_results`), utilise `await asyncio.sleep()`, compatible loop event asyncio existant

13. **Pydantic v2 validations** : KayakPollingConfig avec `field_validator` pour `poll_interval_max >= min`, `model_config` avec `extra="forbid"`, lève `ValidationError` si contraintes violées

14. **Thread-safe storage** : NetworkCaptureListener utilise `asyncio.Lock()` pour protéger liste `_captured` accès concurrent (handler async append + getter)

15. **Configuration injection** : KayakPollingService reçoit `KayakPollingConfig` via constructor (dependency injection), testable avec mock configs

16. **Séparation concerns** : PollingService responsable timing/loops, NetworkCaptureListener responsable filtrage/stockage, CrawlerService orchestre intégration (Single Responsibility Principle)

17. **Réutilisation Story 8** : `crawl_kayak_flights()` réutilise `CrawlerRunConfig(capture_network_requests=True)`, hooks bandwidth optimization, pas de duplication code network capture

18. **Edge cases gérés** : Timeout immédiat (config invalide), aucune response capturée, results[] vide toutes responses, multiples API endpoints, JSON parsing fail → tous gérés sans crash

19. **Playwright page access** : Accès Playwright `Page` depuis `crawler._browser.contexts[0].pages[0]` après `arun()`, vérifié page active pour listener registration

20. **Logging structuré complet** : Logs JSON avec `extra={}` contexte métier (timing, results_count, status, iterations), intégration logger existant `app/core/logger.py`

## Critères qualité

21. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code KayakPollingService, KayakPollingConfig, NetworkCaptureListener, intégration CrawlerService (pytest-cov)

22. **23 tests passent** : 20 tests unitaires (5 Config + 8 PollingService + 4 Listener + 3 CrawlerService) + 3 tests intégration tous verts (pytest -v)

23. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

24. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

25. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler + polling configurés

26. **Docstrings 1 ligne** : KayakPollingService, KayakPollingConfig, NetworkCaptureListener avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

27. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON, configurations (pas d'implémentation complète méthodes)

28. **Commits conventional** : Story 4.3 committée avec message `feat(kayak): add polling mechanism with smart first batch strategy` conforme Conventional Commits

---

**Note importante** : Story complexité moyenne (5 story points) → 28 critères couvrent exhaustivement polling async (10 fonctionnels incluant first batch strategy, timeout gracieux, anti-détection), architecture async résiliente + thread-safety (10 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (premier batch <25s, délais 4-8s randomisés, timeout 45s), **M**esurable (23 tests passent, coverage ≥80%, timing logs), **A**tteignable (Crawl4AI network capture mature Story 8, Playwright listener standard), **R**elevant (résultats 2x plus rapides que polling complet, différenciation source Kayak), **T**emporel (MVP Phase 6, après Story 4.2 parser).
