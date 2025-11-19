---
title: "Story 7: Retry Logic avec Tenacity"
epic: "Epic 3: Production Ready"
story_points: 5
dependencies: ["epic-2/story-4", "epic-2/story-5", "epic-2/story-6"]
date: "2025-11-19"
keywords: ["tenacity", "retry", "exponential-backoff", "jitter", "error-handling", "resilience", "async", "before-sleep", "logging", "production-ready"]
scope: ["specs"]
technologies: ["tenacity", "asyncio", "python"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Robustesse production garantie** : Utilisateurs finaux attendent recherches vols abouties même si Google Flights/Decodo subissent erreurs temporaires (timeouts réseau, rate limiting 429, erreurs serveur 5xx)
- **SLA minimum viable** : Taux de succès global recherche ≥85% (target production) nécessite retry automatique intelligent sur erreurs récupérables (erreurs network, proxies instables, captchas temporaires)
- **Expérience utilisateur fluide** : Retry transparent invisible pour l'utilisateur final, pas de timeout brutal après première erreur, feedback progressif via logs monitoring
- **Décision business data-driven** : Métriques retry observables (nombre tentatives, temps ajouté par retry, taux succès après retry) pour optimiser configuration production

## Contraintes métier

- **Coûts bandwidth Decodo limités** : Chaque retry = nouvelle requête HTTP facturée au GB ($2.60-3.50/GB), nécessite limiter nombre max tentatives (3-5 recommandé) pour éviter explosion coûts sur erreurs persistantes
- **Timeout total acceptable** : Recherche multi-destinations doit compléter en <60 secondes au p95 même avec retry logic (évite frustration utilisateur), nécessite exponential backoff optimisé (wait time min 4s, max 60s total)
- **Pas de retry sur erreurs client** : Erreurs 4xx (ValidationError, ParsingError, 404) non-retryables car problème logique application pas transient error, retry uniquement sur 5xx/network/captcha
- **Thundering herd prevention** : Retry simultané de multiples requêtes peut surcharger Google Flights, nécessite jitter randomness pour distribuer charges retry dans le temps
- **Observabilité production** : Logs structurés retry obligatoires pour monitoring (attempt_number, exception type, wait time, proxy rotated) sans exposer secrets (masquer credentials proxies)

## Valeur business

- **Réduction échecs recherche quantifiable** : Retry logic augmente taux succès crawl de 60-70% (sans retry) à 85-90% (avec retry + rotation IP), économie ~100-200€ coûts support/client par mois
- **SLA production garantis** : Permet promettre uptime API ≥99% même si Google Flights instable (retry masque erreurs temporaires 5xx, timeouts réseau)
- **Foundation resilience scalable** : Patterns Tenacity retry réutilisables pour futures intégrations externes (APIs tierces, webhooks, database queries si post-MVP), gain vélocité 30-40%
- **Métriques observables actionables** : Before_sleep callback fournit insights temps réel : retry patterns populaires, proxies défaillants identifiés, configuration exponential backoff optimisable

## Métriques succès

- **Taux retry déclenché** : 15-25% de requêtes nécessitent ≥1 retry (baseline production attendue avec proxies + Google rate limiting)
- **Taux succès après retry** : ≥90% de requêtes retries aboutissent avec succès (retry logic efficace sur erreurs transient)
- **Temps ajouté par retry** : Médiane <8 secondes par retry (exponential backoff 4s-8s-16s optimal), p95 <30 secondes total retry time
- **Économie échecs évités** : Retry logic évite ~200-300 recherches échouées/mois (validation business ROI retry config)
- **Coverage tests** : ≥80% sur composants retry (RetryStrategy, CrawlerService intégration, before_sleep callback)

---

# 📋 Spécifications Techniques

## 1. RetryStrategy (Configuration Centralisée)

**Rôle** : Définir la configuration Tenacity centralisée réutilisable pour tous les services nécessitant retry logic (CrawlerService, futurs services API tierces).

**Interface** :
```python
class RetryStrategy:
    """Configuration Tenacity centralisée pour retry logic production."""

    @staticmethod
    def get_crawler_retry() -> Retrying:
        """
        Retourne configuration retry optimisée CrawlerService.

        Returns:
            Retrying instance avec exponential backoff + jitter
        """
```

**Paramètres Configuration** :

| Paramètre | Type | Valeur Recommandée | Justification |
|-----------|------|-------------------|---------------|
| `stop` | `stop_after_attempt` | `3` | Équilibre robustesse vs coûts bandwidth (3 tentatives = 2 retries max après échec initial) |
| `wait` | `wait_random_exponential` | `multiplier=2, min=4, max=60` | Exponential backoff évite spam, jitter évite thundering herd, min 4s évite blocages immédiats |
| `retry` | `retry_if_exception_type` | `(CaptchaDetectedError, NetworkError)` | Retry uniquement erreurs récupérables (network, captcha temporaire), pas ValidationError/ParsingError |
| `before_sleep` | `before_sleep_log` callback | Custom callback avec logging structuré | Observabilité retry attempts avec contexte métier |
| `reraise` | `bool` | `True` | Lève exception finale si max retries atteint (caller gère error handling) |

**Comportement** :

- **Exponential backoff calculation** :
  - Tentative 1 : Attendre 0s (pas de retry encore)
  - Tentative 2 : Attendre 2^1 × 2 = 4s minimum (avec jitter random 0-4s additionnel)
  - Tentative 3 : Attendre 2^2 × 2 = 8s minimum (avec jitter random 0-8s additionnel)
  - Max wait time : 60s (plafonné pour éviter timeouts >60s total)

- **Jitter randomness** :
  - `wait_random_exponential` ajoute random delay jusqu'à 2^x × multiplier secondes
  - Exemple : tentative 2 → random(0, 4s) → wait total 0-4s
  - Exemple : tentative 3 → random(0, 8s) → wait total 0-8s
  - Prévient thundering herd : requêtes simultanées retries distribuées dans le temps

- **Exception types retry** :
  - `CaptchaDetectedError` : Captcha détecté (reCAPTCHA/hCaptcha) → retry avec rotation proxy
  - `NetworkError` : Timeout réseau, erreurs HTTP 5xx, connexion refusée → retry avec backoff
  - ❌ Pas de retry : `ValidationError`, `ParsingError`, erreurs HTTP 4xx (erreurs client non-récupérables)

**Erreurs levées** :
- Exception finale reraise si max_retries atteint (type original : CaptchaDetectedError ou NetworkError)

**Logging structuré** :
- DEBUG : Configuration retry créée avec paramètres (stop, wait strategy, retry conditions)

---

## 2. CrawlerService (Intégration Retry)

**Rôle** : Intégrer retry logic Tenacity dans méthode `crawl_google_flights` avec rotation automatique proxies et logging before_sleep callback.

**Interface** :
```python
class CrawlerService:
    """Service crawling Google Flights avec retry logic Tenacity."""

    @retry(**RetryStrategy.get_crawler_retry())
    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True
    ) -> CrawlResult:
        """
        Crawl URL Google Flights avec retry automatique.

        Raises:
            CaptchaDetectedError: Si captcha détecté après max_retries
            NetworkError: Si erreur réseau persistante après max_retries
        """
```

**Comportement Retry Intégré** :

**Scénario 1 : Crawl réussi dès première tentative** :
1. Appeler `crawler.arun(url)` avec proxy actuel
2. Vérifier status code 200 + absence captcha
3. Retourner CrawlResult directement (aucun retry nécessaire)

**Scénario 2 : CaptchaDetectedError → Retry avec rotation proxy** :
1. Tentative 1 : Captcha détecté → lève `CaptchaDetectedError`
2. Before_sleep callback : Logger WARNING avec contexte (attempt 1/3, exception type, wait time 4s, proxy utilisé)
3. **Rotation proxy** : Appeler `proxy_service.get_next_proxy()` pour obtenir nouvelle IP
4. Attendre exponential backoff : ~4s avec jitter
5. Tentative 2 : Retry avec nouveau proxy
6. Si succès → retourner CrawlResult
7. Si échec persistant après 3 tentatives → lève `CaptchaDetectedError` finale

**Scénario 3 : NetworkError (5xx, timeout) → Retry avec backoff** :
1. Tentative 1 : Timeout réseau ou status 500 → lève `NetworkError`
2. Before_sleep callback : Logger WARNING avec contexte (attempt 1/3, exception NetworkError, wait time 4s)
3. **Rotation proxy optionnelle** : Si erreur 429 (rate limiting) → rotation proxy, sinon même proxy
4. Attendre exponential backoff : ~4s avec jitter
5. Tentative 2 : Retry
6. Si succès → retourner CrawlResult
7. Si échec persistant après 3 tentatives → lève `NetworkError` finale

**Scénario 4 : ValidationError → Pas de retry** :
1. Tentative 1 : URL invalide, paramètres incorrects → lève `ValidationError`
2. Exception propagée immédiatement (pas de retry)
3. Caller gère erreur (HTTP 400 retourné à client)

**Edge cases** :
- **Max retries atteint** : Lève exception finale avec attribut `attempts=3` pour observabilité
- **Before_sleep callback échoue** : Ne doit jamais bloquer retry logic (try/except autour logging)
- **Proxy rotation échoue** : Fallback même proxy si pool épuisé, logger ERROR

**Logging structuré** :
- INFO : Début crawl avec URL et proxy
- WARNING : Retry déclenché (attempt N/max, exception type, wait time, proxy rotated)
- ERROR : Max retries atteint, crawl définitivement échoué
- DEBUG : Proxy rotation effectuée, nouvelle IP utilisée

---

## 3. Error Handling Différencié

**Rôle** : Mapper erreurs HTTP et exceptions custom vers stratégies retry appropriées selon type erreur (transient vs permanent).

**Mapping Erreurs → Stratégie Retry** :

| Code/Exception | Type Erreur | Stratégie Retry | Rotation Proxy | Justification |
|----------------|-------------|----------------|----------------|---------------|
| **5xx (500, 502, 503, 504)** | Serveur temporaire | ✅ Retry avec exponential backoff | 🟡 Optionnel | Erreur serveur Google transient, retry peut aboutir |
| **429 Rate Limiting** | Trop de requêtes | ✅ Retry avec backoff + rotation proxy | ✅ Obligatoire | Changement IP contourne rate limit IP-based |
| **403 Forbidden** | Blocage IP | ✅ Retry avec rotation proxy immédiate | ✅ Obligatoire | IP blacklistée, changement IP obligatoire |
| **Timeout réseau** | Connexion instable | ✅ Retry avec backoff | 🟡 Optionnel | Network transient error, retry peut aboutir |
| **CaptchaDetectedError** | Captcha présent | ✅ Retry avec rotation proxy | ✅ Obligatoire | Changement IP peut éviter captcha (fingerprint différent) |
| **404 Not Found** | Ressource inexistante | ❌ Pas de retry | ❌ Non | Erreur client permanente, retry inutile |
| **400 Bad Request** | Paramètres invalides | ❌ Pas de retry | ❌ Non | Erreur client logique, nécessite correction code |
| **ValidationError** | Validation Pydantic | ❌ Pas de retry | ❌ Non | Erreur application logique, pas transient error |
| **ParsingError** | Parsing HTML échoué | ❌ Pas de retry | ❌ Non | Structure HTML invalide, retry ne changera rien |

**Exceptions Custom** :

```python
class NetworkError(Exception):
    """Erreur réseau récupérable via retry."""

    def __init__(self, url: str, status_code: int | None, attempts: int):
        """
        Args:
            url: URL concernée
            status_code: Code HTTP si disponible (None si timeout)
            attempts: Nombre tentatives effectuées
        """

class CaptchaDetectedError(Exception):
    """Captcha détecté, récupérable via retry + rotation IP."""

    def __init__(self, url: str, captcha_type: str, proxy_used: str):
        """
        Args:
            url: URL concernée
            captcha_type: Type captcha (recaptcha_v2, recaptcha_v3, hcaptcha)
            proxy_used: Proxy ayant déclenché captcha (format masqué)
        """
```

**Logging par Type Erreur** :

- **5xx/Timeout** : `WARNING - Network error detected, retrying... (attempt X/3, status: 503, wait: 4s)`
- **429/403** : `WARNING - Rate limit detected, rotating proxy... (attempt X/3, new_proxy: customer-XXX-FR-2)`
- **CaptchaDetectedError** : `WARNING - Captcha detected (recaptcha_v2), rotating proxy... (attempt X/3, proxy: customer-XXX-FR-1)`
- **ValidationError** : `ERROR - Validation failed, no retry (url: ..., error: ...)`
- **Max retries** : `ERROR - Max retries exceeded (3 attempts), operation failed (last_exception: NetworkError, url: ...)`

---

## 4. Before_Sleep Callback (Logging Retry Attempts)

**Rôle** : Logger contexte complet de chaque retry attempt via callback Tenacity `before_sleep` pour observabilité production.

**Interface** :
```python
def log_retry_attempt(retry_state: RetryCallState) -> None:
    """
    Callback Tenacity before_sleep pour logging structuré retry attempts.

    Args:
        retry_state: État retry fourni par Tenacity
    """
```

**Paramètres Callback** :

| Paramètre RetryCallState | Type | Description | Utilisation |
|--------------------------|------|-------------|-------------|
| `attempt_number` | `int` | Numéro tentative actuelle (1-indexed) | Logger "attempt X/max_attempts" |
| `outcome.exception()` | `Exception` | Exception levée par tentative précédente | Extraire type exception (CaptchaDetectedError, NetworkError) |
| `next_action.sleep` | `float` | Temps attente avant prochaine tentative (secondes) | Logger "wait_time_seconds" |
| `fn` | `Callable` | Fonction retryée (ex: `crawl_google_flights`) | Extraire nom fonction pour contexte |
| `args` / `kwargs` | Tuple/Dict | Arguments fonction retryée | Extraire URL crawlée |

**Extraction Contexte** :

```python
def log_retry_attempt(retry_state: RetryCallState) -> None:
    """Callback before_sleep avec extraction contexte complet."""
    # Extraire infos de base
    attempt_number = retry_state.attempt_number
    exception = retry_state.outcome.exception()
    wait_time = retry_state.next_action.sleep

    # Extraire URL depuis args (premier arg de crawl_google_flights)
    url = retry_state.args[0] if retry_state.args else "unknown"

    # Extraire proxy utilisé si disponible (depuis service instance)
    proxy_used = getattr(retry_state.args[0], 'current_proxy', 'unknown') if retry_state.args else 'unknown'

    # Calculer attempts restants
    max_attempts = 3  # Depuis RetryStrategy configuration
    attempts_remaining = max_attempts - attempt_number

    # Logging JSON structuré
    logger.warning(
        "Retry attempt triggered",
        extra={
            "url": url,
            "proxy_used": proxy_used,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "attempt_number": attempt_number,
            "attempts_remaining": attempts_remaining,
            "wait_time_seconds": round(wait_time, 2),
            "next_retry_at": (datetime.now() + timedelta(seconds=wait_time)).isoformat()
        }
    )
```

**Logging JSON Output Exemple** :

```json
{
  "timestamp": "2025-11-19T14:23:45Z",
  "level": "WARNING",
  "message": "Retry attempt triggered",
  "url": "https://www.google.com/travel/flights?...",
  "proxy_used": "customer-XXX-country-FR-1",
  "exception_type": "CaptchaDetectedError",
  "exception_message": "reCAPTCHA v2 detected",
  "attempt_number": 1,
  "attempts_remaining": 2,
  "wait_time_seconds": 4.23,
  "next_retry_at": "2025-11-19T14:23:49Z"
}
```

**Edge cases** :
- **Exception extraction échoue** : Fallback `exception_type: "UnknownError"`, logger DEBUG warning
- **URL extraction échoue** : Fallback `url: "unknown"`, ne doit jamais bloquer retry
- **Callback lève exception** : Try/except global autour logging, ne jamais bloquer retry logic

**Logging structuré** :
- WARNING : Chaque retry attempt avec contexte complet
- DEBUG : Callback appelé avec success
- ERROR : Callback échoue (exception loggée mais retry continue)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### RetryStrategy (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_retry_on_network_error` | Retry déclenché sur NetworkError | Mock fonction levant `NetworkError` 2 fois puis succès | Fonction appelée 3 fois (1 initiale + 2 retries), succès final | Vérifie retry automatique sur NetworkError |
| 2 | `test_retry_on_captcha_detected` | Retry déclenché sur CaptchaDetectedError | Mock fonction levant `CaptchaDetectedError` 1 fois puis succès | Fonction appelée 2 fois (1 initiale + 1 retry), succès final | Vérifie retry automatique sur CaptchaDetectedError |
| 3 | `test_no_retry_on_validation_error` | Pas de retry sur ValidationError | Mock fonction levant `ValidationError` | Exception propagée immédiatement, fonction appelée 1 seule fois | Vérifie ValidationError non-retryable |
| 4 | `test_exponential_backoff_timing` | Wait time augmente exponentiellement | Mock fonction avec 3 échecs NetworkError | Wait times ≈ [4s, 8s, 16s] avec jitter (tolérance ±2s) | Vérifie exponential backoff calculation |
| 5 | `test_max_retries_exceeded` | Lève exception finale si max retries atteint | Mock fonction levant `NetworkError` 4 fois (>max_attempts) | Exception `NetworkError` finale levée après 3 tentatives | Vérifie stop_after_attempt(3) |
| 6 | `test_jitter_randomness` | Jitter ajoute randomness wait time | Exécuter retry 10 fois avec même erreur | Wait times varient dans range [0, 4s] pour tentative 2 | Vérifie wait_random_exponential randomness |
| 7 | `test_before_sleep_callback_logging` | Before_sleep callback appelé à chaque retry | Mock fonction avec 2 échecs | Callback appelé 2 fois avec `attempt_number=1` puis `attempt_number=2` | Vérifie before_sleep intégration |
| 8 | `test_retry_success_after_failures` | Succès après N échecs < max_attempts | Mock fonction : 2 échecs `NetworkError` puis succès | Fonction appelée 3 fois, retour succès final (pas d'exception) | Vérifie retry aboutit si erreur transient |

### CrawlerService avec Retry (7 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 9 | `test_crawl_success_no_retry` | Crawl réussi première tentative, aucun retry | Mock `crawler.arun()` retourne HTML valide status 200 | `CrawlResult` retourné, `crawler.arun()` appelé 1 fois | Vérifie comportement nominal sans retry |
| 10 | `test_crawl_retry_on_500_error` | Retry automatique sur status 500 | Mock `crawler.arun()` : 1er appel status 500, 2ème status 200 | `CrawlResult` succès, `crawler.arun()` appelé 2 fois, logs WARNING retry | Vérifie retry sur 5xx errors |
| 11 | `test_crawl_retry_on_timeout` | Retry automatique sur timeout réseau | Mock `crawler.arun()` : 1er appel timeout exception, 2ème succès | `CrawlResult` succès, `crawler.arun()` appelé 2 fois | Vérifie retry sur NetworkError timeout |
| 12 | `test_crawl_max_retries_network_error` | Max retries atteint, NetworkError finale | Mock `crawler.arun()` lève `NetworkError` 4 fois (>max_attempts) | Lève `NetworkError` avec `attempts=3`, logs ERROR max retries | Vérifie abandon après max_retries |
| 13 | `test_crawl_no_retry_on_404` | Pas de retry sur 404 Not Found | Mock `crawler.arun()` retourne status 404 | Exception propagée immédiatement (ou retour vide), aucun retry | Vérifie erreur 4xx non-retryable |
| 14 | `test_crawl_before_sleep_logging` | Logging before_sleep callback chaque retry | Mock `crawler.arun()` : 2 échecs `CaptchaDetectedError` puis succès | Logs WARNING contiennent `attempt_number=1` et `attempt_number=2` avec contexte complet | Vérifie before_sleep callback logging |
| 15 | `test_crawl_retry_with_proxy_rotation` | Rotation proxy à chaque retry | Mock `crawler.arun()` : 1er appel captcha proxy1, 2ème succès proxy2 | `proxy_service.get_next_proxy()` appelé 1 fois, logs montrent proxy rotation | Vérifie intégration rotation proxy dans retry |

**Total tests unitaires** : 8 (RetryStrategy) + 7 (CrawlerService) = **15 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_with_transient_errors` | Mock AsyncWebCrawler : 30% requêtes timeout puis succès, 2 destinations × 3 dates = 6 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ≥4 résultats (60% succès immédiat + retry succès), logs WARNING retry pour 2 combinaisons, temps total <30s |
| 2 | `test_integration_retry_exhaustion_graceful_degradation` | Mock AsyncWebCrawler : 40% requêtes lèvent `NetworkError` persistant (4 tentatives), 3 destinations × 2 dates = 12 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~7 résultats (60% réussis), logs ERROR max retries pour 5 combinaisons, pas d'exception bloquante |
| 3 | `test_integration_partial_retry_success` | Mock AsyncWebCrawler : 50% requêtes captcha 1ère tentative puis succès retry, 2 destinations × 5 dates = 10 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~10 résultats (100% succès après retry), logs WARNING retry pour 5 combinaisons, proxy rotation visible dans logs |
| 4 | `test_integration_no_retry_on_client_errors` | Mock AsyncWebCrawler : 20% requêtes retournent status 404, 3 destinations × 3 dates = 18 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~14 résultats (80% succès), 4 erreurs 404 propagées sans retry, logs montrent aucun retry pour 404 |
| 5 | `test_integration_end_to_end_retry_metrics_logging` | Mock AsyncWebCrawler : mix erreurs (20% timeout, 10% captcha, 70% succès), 5 destinations × 2 dates = 20 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~18 résultats après retry, logs structurés contiennent métriques : total_retries, retry_rate, avg_wait_time, success_after_retry_rate |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 15 unitaires + 5 intégration = **20 tests**

---

## Exemples JSON

**Exemple 1 : CrawlResult après retry success**

```json
{
  "html": "<html>...Google Flights content...</html>",
  "success": true,
  "status_code": 200,
  "retry_metadata": {
    "attempts": 2,
    "total_wait_time_seconds": 4.23,
    "retry_reasons": ["CaptchaDetectedError"],
    "proxies_used": ["customer-XXX-FR-1", "customer-XXX-FR-2"]
  }
}
```

**Contexte** : Première tentative captcha détecté (proxy1), retry après 4.23s avec rotation proxy (proxy2), succès.

---

**Exemple 2 : NetworkError après max retries**

```json
{
  "error": "NetworkError",
  "message": "Max retries exceeded (3 attempts) for URL",
  "details": {
    "url": "https://www.google.com/travel/flights?...",
    "attempts": 3,
    "last_status_code": 503,
    "total_wait_time_seconds": 28.47,
    "retry_history": [
      {"attempt": 1, "exception": "NetworkError", "status_code": 503, "wait_time": 4.12},
      {"attempt": 2, "exception": "NetworkError", "status_code": 503, "wait_time": 8.35},
      {"attempt": 3, "exception": "NetworkError", "status_code": 503, "wait_time": 16.00}
    ]
  }
}
```

**Contexte** : 3 tentatives échouées avec status 503 (service unavailable), exponential backoff respecté, erreur finale après 28.47s total wait.

---

**Exemple 3 : Logging before_sleep callback avec contexte complet**

```json
{
  "timestamp": "2025-11-19T14:23:45.123Z",
  "level": "WARNING",
  "service": "CrawlerService",
  "message": "Retry attempt triggered",
  "url": "https://www.google.com/travel/flights?departure_id=CDG&arrival_id=NRT",
  "proxy_used": "customer-abc123-country-FR-1",
  "exception_type": "CaptchaDetectedError",
  "exception_message": "reCAPTCHA v2 detected",
  "captcha_type": "recaptcha_v2",
  "attempt_number": 1,
  "max_attempts": 3,
  "attempts_remaining": 2,
  "wait_time_seconds": 4.23,
  "next_retry_at": "2025-11-19T14:23:49.353Z",
  "exponential_backoff_multiplier": 2,
  "jitter_applied": true,
  "proxy_rotation_triggered": true,
  "new_proxy": "customer-abc123-country-FR-2"
}
```

**Contexte** : Before_sleep callback appelé après 1ère tentative échouée (captcha), logging JSON structuré complet avec contexte métier, proxy rotation effectuée, prochaine tentative dans 4.23 secondes.

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Retry automatique sur erreurs récupérables** : CrawlerService retry automatiquement sur `CaptchaDetectedError` et `NetworkError` avec exponential backoff (vérifié logs contiennent retry attempts)

2. **Pas de retry sur erreurs client** : Erreurs `ValidationError`, `ParsingError`, HTTP 4xx propagées immédiatement sans retry (vérifié fonction appelée 1 seule fois)

3. **Exponential backoff respecté** : Wait times entre retries augmentent exponentiellement ~4s, ~8s, ~16s avec jitter aléatoire (tolérance ±2s, vérifié via mock asyncio.sleep)

4. **Max retries limité à 3 tentatives** : Retry logic arrête après 3 tentatives totales (1 initiale + 2 retries), lève exception finale (vérifié assertion `attempts=3`)

5. **Jitter randomness appliqué** : Wait times varient aléatoirement dans range [0, 2^x × multiplier] secondes pour éviter thundering herd (vérifié statistiquement sur 10+ exécutions)

6. **Rotation proxy à chaque retry** : Si retry déclenché → `proxy_service.get_next_proxy()` appelé pour obtenir nouvelle IP (vérifié mock spy proxy_service)

7. **Before_sleep callback logging** : Chaque retry attempt logge contexte complet : attempt_number, exception_type, wait_time, proxy_used (vérifié logs JSON structurés)

8. **Succès après retry** : Si erreur transient résolu (ex: captcha disparaît après rotation IP) → retourne `CrawlResult` success sans lever exception (vérifié pas d'exception finale)

## Critères techniques

9. **Type hints PEP 695** : RetryStrategy, before_sleep callback, exceptions custom annotés avec type hints modernes (`RetryCallState`, `Exception`, `float`)

10. **Async/Await cohérent** : Retry logic fonctionne avec fonctions async (`async def crawl_google_flights`), utilise `asyncio.sleep()` pour wait times (pas de blocage)

11. **Tenacity version 9.1.2+** : Utilise Tenacity avec support async natif, `wait_random_exponential`, `before_sleep` callback, `retry_if_exception_type` (vérifié pyproject.toml)

12. **Configuration centralisée RetryStrategy** : Classe RetryStrategy fournit méthode `get_crawler_retry()` retournant config Tenacity réutilisable (testable, modifiable sans toucher CrawlerService)

13. **Décorateur @retry appliqué** : CrawlerService.crawl_google_flights décoré avec `@retry(**RetryStrategy.get_crawler_retry())` (syntaxe Tenacity standard)

14. **Exceptions custom typées** : `NetworkError` et `CaptchaDetectedError` héritent `Exception`, contiennent attributs contextuels (`url`, `status_code`, `attempts`, `captcha_type`, `proxy_used`)

15. **Before_sleep callback extraction contexte** : Callback extrait `retry_state.attempt_number`, `retry_state.outcome.exception()`, `retry_state.next_action.sleep`, URL depuis args (vérifié logging contient tous champs)

16. **Logging structuré JSON complet** : Logs retry incluent contexte métier : url, proxy_used, exception_type, attempt_number, attempts_remaining, wait_time_seconds, next_retry_at (format pythonjsonlogger)

17. **Reraise exception finale** : Si max retries atteint → exception finale reraise avec contexte (type original préservé : `CaptchaDetectedError` ou `NetworkError`)

18. **Mock asyncio.sleep pour tests** : Tests unitaires retry mockent `asyncio.sleep()` pour vitesse (pas attendre vraies secondes retry, vérifié exécution tests <5s total)

## Critères qualité

19. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code RetryStrategy, CrawlerService retry integration, before_sleep callback (pytest-cov)

20. **20 tests passent** : 15 tests unitaires (8 RetryStrategy + 7 CrawlerService) + 5 tests intégration tous verts (pytest -v)

21. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

22. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

23. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler/ProxyService configurés

24. **Docstrings 1 ligne** : RetryStrategy et before_sleep callback avec docstring descriptive, focus POURQUOI pas QUOI

25. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON, formules exponential backoff (pas d'implémentation complète)

26. **Commits conventional** : Story 7 committée avec message `docs(specs): add story 7 specifications` conforme Conventional Commits

---

**Note importante** : Story moyenne complexité (5 story points) → 26 critères couvrent exhaustivement retry logic production-ready (8 fonctionnels), architecture Tenacity réutilisable (10 techniques), qualité tests TDD (8 qualité). Réutilise CrawlerService/ProxyService existants (Story 4 et 6), ajoute layer resilience transparent.

**Principe SMART** : Chaque critère est **S**pécifique (exponential backoff 4s-8s-16s), **M**esurable (20 tests passent, coverage ≥80%), **A**tteignable (Tenacity lib mature), **R**elevant (SLA production ≥85%), **T**emporel (MVP Phase 5, après CrawlerService/ProxyService déjà implémentés).
