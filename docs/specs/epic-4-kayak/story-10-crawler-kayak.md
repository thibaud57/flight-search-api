---
title: "Story 10: CrawlerService Kayak + Session Consent"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-4/story-9"]
date: "2025-11-26"
keywords: ["kayak", "crawler", "session", "consent", "cookies", "playwright", "network-capture"]
scope: ["specs"]
technologies: ["Python", "asyncio", "Crawl4AI", "Playwright"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Session Kayak persistante** : Gérer le popup de consentement cookies (RGPD) pour débloquer le chargement des résultats
- **Crawl Kayak avec network capture** : Capturer les requêtes XHR/Fetch pour récupérer le JSON des résultats (plus fiable que parsing HTML)
- **Réutilisation patterns existants** : Adapter le pattern `get_google_session()` pour créer `get_kayak_session()`

## Contraintes métier

- **Popup RGPD variable** : Peut apparaître ou non selon état cookies navigateur
- **Timeout consent 5s** : Popup doit être détecté rapidement pour ne pas ralentir scraping
- **Network capture async** : Kayak utilise polling XHR progressif, besoin `capture_network_requests=True`
- **Délais anti-détection** : Respecter délais entre requêtes pour éviter blocage

## Valeur business

- ✅ **Réutilisation architecture** : Adapter patterns CrawlerService existants (`get_google_session`) = moins de code nouveau
- ✅ **Fiabilité parsing** : JSON network capture plus stable que parsing HTML (structure API vs DOM)
- ✅ **Dérisquage RGPD** : Gestion consent dès Story 10 = pas de surprise en intégration
- ✅ **Foundation parsing** : Prépare les données JSON pour KayakFlightParser (Story 11)

## Métriques succès

- **Timeout consent** : 5s max pour détection popup (non bloquant si absent)
- **Taux succès session** : 100% pages Kayak chargées après consent handling
- **Network capture** : Requêtes XHR `/api/search/` capturées dans CrawlResult
- **Coverage tests** : ≥80% sur nouvelles méthodes CrawlerService

---

# 📋 Spécifications Techniques

## 1. Extension CrawlerService

**Rôle** : Ajouter les méthodes Kayak au CrawlerService existant, en suivant les patterns de `get_google_session()` et `crawl_google_flights()`.

### 1.1 Méthode get_kayak_session()

**Interface** :
```python
async def get_kayak_session(self, url: str, *, use_proxy: bool = True) -> None:
    """
    Initialise session Kayak avec gestion consent cookies.

    Similaire à get_google_session() mais avec sélecteurs Kayak.
    """
```

**Comportement** :

1. Créer `CrawlerRunConfig` similaire à Google mais avec :
   - `wait_for_selector` : Sélecteur résultats Kayak (ex: `.resultWrapper`, `[data-resultid]`)
   - `capture_network_requests=True` : Activer capture XHR pour polling
2. Configurer hook `_after_goto_hook` avec sélecteurs consent Kayak
3. Exécuter crawl initial pour établir session cookies
4. Gérer popup consent si présent via `_handle_kayak_consent()`

**Sélecteurs consent Kayak** :

| Priorité | Sélecteur CSS | Description |
|----------|---------------|-------------|
| 1 | `button[id*='accept']` | Bouton avec ID contenant "accept" |
| 2 | `button[class*='consent']` | Bouton avec classe contenant "consent" |
| 3 | `div[class*='cookie'] button` | Bouton dans div cookie générique |
| 4 | `.didomi-continue-without-agreeing` | Bouton Didomi "Continuer sans accepter" |

### 1.2 Méthode crawl_kayak()

**Interface** :
```python
async def crawl_kayak(
    self,
    url: str,
    *,
    use_proxy: bool = True
) -> CrawlResult:
    """
    Crawl URL Kayak avec network capture activé.

    Returns:
        CrawlResult avec HTML + network_requests capturés
    """
```

**Comportement** :

1. Appeler `get_kayak_session()` si pas de session active
2. Créer `CrawlerRunConfig` avec :
   - `capture_network_requests=True` : Capture XHR/Fetch
   - `wait_until="domcontentloaded"` : Pas networkidle (Kayak poll continuellement)
   - `delay_before_return_html=5.0` : Attendre premiers résultats
   - `wait_for_selector` : Sélecteur présence résultats
3. Exécuter `crawler.arun(url, config=config)`
4. Retourner `CrawlResult` avec `network_requests` contenant les responses JSON

**Configuration CrawlerRunConfig Kayak** :

```python
def _build_kayak_crawler_config(self, wait_for_selector: str) -> CrawlerRunConfig:
    """Config Kayak avec network capture."""
    return CrawlerRunConfig(
        wait_for_selector=wait_for_selector,
        capture_network_requests=True,  # Key: capture XHR
        wait_until="domcontentloaded",
        delay_before_return_html=5.0,
        js_code=self._scroll_js,  # Réutilise scroll existant
        page_timeout=30000,
    )
```

### 1.3 Hook _handle_kayak_consent()

**Interface** :
```python
async def _handle_kayak_consent(self, page: Page) -> None:
    """
    Détecte et ferme popup consent Kayak si présent.

    Non-bloquant : retourne silencieusement si pas de popup.
    """
```

**Comportement** :

- Itère sur sélecteurs consent dans l'ordre de priorité
- Attend popup max 5s (`timeout=5000`)
- Si popup détecté : click + sleep 1s (laisser popup se fermer)
- Si timeout : passe à sélecteur suivant
- Si aucun sélecteur matche : retourne silencieusement (non bloquant)

**Intégration avec _after_goto_hook** :

```python
async def _after_goto_hook(
    self, page: Page, context: Any, url: str, response: Any, **kwargs: Any
) -> Page:
    """Hook après navigation - gère consent selon provider."""
    if "kayak" in url.lower():
        await self._handle_kayak_consent(page)
    else:
        # Existant: gestion Google consent
        await self._handle_google_consent(page)
    return page
```

---

## 2. KayakConfig (Settings)

**Rôle** : Configuration Kayak-specific pour timeouts et sélecteurs.

**Interface** :
```python
class KayakConfig(BaseSettings):
    """Configuration Kayak crawling."""

    consent_timeout: int = 5000
    wait_for_results_timeout: int = 30000
    delay_before_return: float = 5.0
    results_selector: str = "[data-resultid]"

    model_config = ConfigDict(
        env_prefix="KAYAK_",
        extra="forbid"
    )
```

**Champs** :

| Champ | Type | Défaut | Description |
|-------|------|--------|-------------|
| `consent_timeout` | `int` | `5000` | Timeout détection popup consent (ms) |
| `wait_for_results_timeout` | `int` | `30000` | Timeout attente résultats (ms) |
| `delay_before_return` | `float` | `5.0` | Délai avant récupération HTML (s) |
| `results_selector` | `str` | `"[data-resultid]"` | Sélecteur CSS présence résultats |

---

## 3. Network Capture et CrawlResult

**Utilisation CrawlResult.network_requests** :

Le CrawlResult de Crawl4AI avec `capture_network_requests=True` contient automatiquement les requêtes capturées. On peut filtrer les responses Kayak API :

```python
def _extract_kayak_api_responses(self, result: CrawlResult) -> list[dict]:
    """Extrait les responses JSON Kayak API depuis network_requests."""
    kayak_responses = []
    for request in result.network_requests:
        if (
            "/api/search/" in request.url or "/poll" in request.url
        ) and request.response_status == 200:
            try:
                data = json.loads(request.response_body)
                if data.get("results"):
                    kayak_responses.append(data)
            except json.JSONDecodeError:
                continue
    return kayak_responses
```

**Note** : Cette méthode d'extraction sera utilisée par `KayakFlightParser` (Story 11).

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### KayakConfig (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_kayak_config_defaults` | Valeurs par défaut | Pas d'env vars | `consent_timeout=5000`, `delay_before_return=5.0` | Vérifie defaults |
| 2 | `test_kayak_config_env_override` | Override via env | `KAYAK_CONSENT_TIMEOUT=10000` | `consent_timeout=10000` | Vérifie lecture env |
| 3 | `test_kayak_config_extra_forbid` | Champ inconnu rejeté | `unknown_field="x"` | Lève `ValidationError` | Vérifie extra=forbid |
| 4 | `test_kayak_config_results_selector` | Sélecteur configurable | `KAYAK_RESULTS_SELECTOR=".flight-card"` | `results_selector=".flight-card"` | Vérifie sélecteur custom |

### CrawlerService Kayak (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 5 | `test_get_kayak_session_success` | Session établie avec consent | Mock crawler + page avec popup | Session créée, pas d'exception | Vérifie flow session |
| 6 | `test_get_kayak_session_no_popup` | Session sans popup consent | Mock page sans popup | Session créée silencieusement | Vérifie non-bloquant |
| 7 | `test_crawl_kayak_with_network_capture` | Crawl avec capture activée | Mock crawler | CrawlResult avec `network_requests` non vide | Vérifie capture activée |
| 8 | `test_crawl_kayak_returns_html` | HTML retourné | Mock crawler | CrawlResult avec `html` contenant DOM | Vérifie HTML présent |
| 9 | `test_handle_kayak_consent_click` | Popup cliqué | Mock page avec bouton consent | `button.click()` appelé | Vérifie click consent |
| 10 | `test_handle_kayak_consent_timeout` | Timeout sans popup | Mock page sans bouton | Retourne sans erreur après timeout | Vérifie timeout gracieux |
| 11 | `test_handle_kayak_consent_fallback_selector` | Fallback sélecteur | Mock avec 2e sélecteur match | Click sur 2e sélecteur | Vérifie fallback |
| 12 | `test_after_goto_hook_kayak_url` | Hook détecte URL Kayak | URL `kayak.fr/flights/...` | `_handle_kayak_consent()` appelé | Vérifie routing hook |

### Network extraction (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 13 | `test_extract_kayak_api_filters_url` | Filtre URLs API | Requests avec `/api/search/` et autres | Seules `/api/search/` retournées | Vérifie filtre URL |
| 14 | `test_extract_kayak_api_filters_status` | Filtre status 200 | Requests status 200 et 404 | Seules status 200 retournées | Vérifie filtre status |
| 15 | `test_extract_kayak_api_parses_json` | Parse JSON response | Request avec body JSON valide | Dict parsé retourné | Vérifie parsing JSON |
| 16 | `test_extract_kayak_api_ignores_invalid_json` | Ignore JSON invalide | Request avec body non-JSON | Liste vide, pas d'exception | Vérifie résilience |

**Total tests unitaires** : 4 (Config) + 8 (CrawlerService) + 4 (Network) = **16 tests**

---

### Tests unitaires - Scénarios complexes (3 tests)

**Note** : Ces tests utilisent des mocks pour simuler des scénarios complexes multi-composants. Ils restent des tests unitaires car ils n'utilisent pas TestClient FastAPI pour tester la couche HTTP.

**Format recommandé : Given/When/Then (BDD) pour lisibilité scénarios complexes**

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 17 | `test_kayak_session_with_consent_flow` | Session établie avec popup consent visible | Mock page avec popup consent visible | `get_kayak_session(url)` réussit, popup cliqué | Vérifie flow complet session + consent |
| 18 | `test_crawl_kayak_captures_network_requests` | Crawl avec capture network | Mock crawler avec responses API | CrawlResult contient `network_requests` avec JSON API | Vérifie capture network activée |
| 19 | `test_hook_routing_kayak_vs_google` | Hook routing selon provider | URL Google et URL Kayak | `_after_goto_hook()` appelle consent adapté | Vérifie routing hook selon URL |

---

**TOTAL STORY 10** : 16 + 3 = **19 tests unitaires**

---

## Exemples JSON

**Exemple 1 : CrawlResult.network_requests structure**

```json
{
  "url": "https://www.kayak.fr/api/search/V8/flight/poll",
  "method": "GET",
  "response_status": 200,
  "response_headers": {"content-type": "application/json"},
  "response_body": "{\"status\":\"polling\",\"results\":[...]}"
}
```

**Exemple 2 : KayakConfig env vars**

```bash
KAYAK_CONSENT_TIMEOUT=10000
KAYAK_WAIT_FOR_RESULTS_TIMEOUT=45000
KAYAK_DELAY_BEFORE_RETURN=8.0
KAYAK_RESULTS_SELECTOR=".resultWrapper"
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Méthode get_kayak_session()** : Crée session Kayak avec gestion consent, similaire pattern `get_google_session()`
2. **Méthode crawl_kayak()** : Crawl URL Kayak avec `capture_network_requests=True`, retourne CrawlResult
3. **Gestion consent Kayak** : Popup détecté et cliqué dans timeout 5s, fallback si pas de popup
4. **Sélecteurs consent multiples** : 4 sélecteurs testés en cascade (button[id*=accept], consent class, cookie div, didomi)
5. **Hook routing** : `_after_goto_hook` route vers consent Google ou Kayak selon URL
6. **Network capture activé** : `CrawlerRunConfig` avec `capture_network_requests=True` pour Kayak
7. **Extraction API responses** : Méthode helper filtre responses `/api/search/` et `/poll`

## Critères techniques

8. **Type hints PEP 695** : Toutes méthodes annotées avec types modernes
9. **Async/Await cohérent** : Méthodes async compatibles event loop existant
10. **Pydantic v2 Settings** : KayakConfig avec `env_prefix`, `extra="forbid"`
11. **Réutilisation patterns** : Suit architecture `get_google_session()` existante
12. **Non-bloquant consent** : Timeout géré, retourne silencieusement si pas popup
13. **JSON parsing résilient** : `try/except JSONDecodeError` sur extraction responses

## Critères qualité

14. **Coverage ≥80%** : Tests couvrent nouvelles méthodes CrawlerService
15. **19 tests passent** : 19 tests unitaires tous verts (16 basiques + 3 scénarios complexes)
16. **Ruff + Mypy passent** : Code conforme standards projet
17. **Docstrings 1 ligne** : Méthodes publiques documentées

---

**💡 Note** : Cette story se concentre sur l'extension CrawlerService pour Kayak. Le parsing des responses JSON capturées est fait dans Story 11 (KayakFlightParser).
