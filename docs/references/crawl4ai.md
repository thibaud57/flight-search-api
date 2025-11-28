---
title: "Crawl4AI - Référence Technique"
description: "Patterns Crawl4AI pour web scraping async : AsyncWebCrawler, BrowserConfig stealth mode, JsonCssExtractionStrategy sans LLM. Consulter pour scraping Google Flights, extraction CSS, gestion navigateur et anti-détection."
date: "2025-17-11"
keywords: ["crawl4ai", "async", "web-scraping", "webscraping", "asyncwebcrawler", "browserconfig", "stealth", "playwright", "extraction", "css-selectors", "anti-detection", "navigation", "browser"]
scope: ["code"]
technologies: ["crawl4ai", "playwright"]
---

# AsyncWebCrawler - Crawler Asynchrone

## Description

AsyncWebCrawler est la classe principale pour les opérations de web scraping. Elle fournit une interface asynchrone pour crawler des pages individuelles ou multiples avec support complet de la configuration du navigateur, l'extraction structurée et le caching.

## Méthodes principales

- `arun(url, config)` : Crawl une URL unique et retourne un objet CrawlResult
- `arun_many(urls, configs)` : Traite plusieurs URLs en parallèle avec configuration par URL

## Exemple minimal

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_cfg = BrowserConfig(browser_type="chromium", headless=True)
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun("https://example.com", config=run_cfg)
        print(result.cleaned_html)

asyncio.run(main())
```

## Points clés

- Utiliser le context manager `async with` pour gérer automatiquement les ressources
- Séparer BrowserConfig (global) et CrawlerRunConfig (par crawl)
- Le CrawlResult contient `cleaned_html`, `markdown`, et `extracted_content`

# BrowserConfig - Configuration Browser

## Description

BrowserConfig contrôle le comportement global du navigateur incluant le type de navigateur, le mode sans interface, les dimensions de la fenêtre, les proxies, les user-agents et les contextes persistants. Inclut le stealth mode pour contourner la détection de bots.

## Options principales

- `browser_type` : Type de navigateur ("chromium", "firefox", "webkit")
- `headless` : Mode sans interface (True/False)
- `enable_stealth` : Active le stealth mode via playwright-stealth (True/False)
- `user_agent` : User-Agent personnalisé
- `viewport` : Dimensions de la fenêtre
- `proxy_config` : Configuration proxy (dict avec server, username, password)

## Exemple avec proxy_config (v0.7+)

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_conf = BrowserConfig(
    headless=True,
    enable_stealth=True,
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "myuser",
        "password": "mypass",
    }
)
```

## Exemple avec stealth mode

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_conf = BrowserConfig(
    browser_type="chromium",
    headless=True,
    enable_stealth=True  # Active la protection contre la détection
)

async with AsyncWebCrawler(config=browser_conf) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown)
```

## Points clés

- Stealth mode modifie les fingerprints du navigateur pour éviter la détection basique
- Désactivé par défaut (`False`)
- Recommandé pour les sites avec protection anti-bot
- Peut être combiné avec UndetectedAdapter pour une protection accrue

# JsonCssExtractionStrategy - Extraction CSS

## Description

JsonCssExtractionStrategy permet l'extraction de données structurées sans utiliser de modèles de langage. Elle utilise des sélecteurs CSS pour identifier et extraire des données avec précision, rapidité et coût zéro. Idéale pour les pages avec structure HTML répétitive.

## Concept

- **Base Selector** : Identifie les conteneurs répétitifs (lignes de tableau, cartes de produits)
- **Fields** : Spécifie les sélecteurs CSS pour extraire les données individuelles

## Exemple complet

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_crypto_prices():
    schema = {
        "name": "Cryptocurrency Data",
        "baseSelector": ".crypto-row",  # Répéteur principal
        "fields": [
            {
                "name": "name",
                "selector": ".crypto-name",
                "type": "text"
            },
            {
                "name": "price",
                "selector": ".crypto-price",
                "type": "text"
            },
            {
                "name": "change",
                "selector": ".crypto-change",
                "type": "text"
            }
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.coinbase.com/explore",
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        print(json.dumps(result.extracted_content, indent=2))

asyncio.run(extract_crypto_prices())
```

## Types de champs supportés

- `text` : Contenu textuel
- `attribute` : Attributs HTML (href, data-*, etc.)
- `html` : HTML brut
- `regex` : Extraction via expression régulière

## Points clés

- **Performance** : Exécution quasi-instantanée (pas de LLM)
- **Fiabilité** : Résultats consistants et reproductibles
- **Scalabilité** : Traitement parallèle de milliers de pages
- **Coût zéro** : Aucun appel API ou surcharge computationnelle
- **Précision** : Sélecteurs CSS permettent extraction ciblée exacte

# Network Capture - Interception Requêtes Réseau

## Description

La fonctionnalité de **network capture** permet d'intercepter et d'analyser toutes les requêtes HTTP effectuées par la page pendant le crawl. Contrairement à l'extraction CSS qui parse le HTML rendu, le network capture récupère directement les données JSON des appels API internes. Cette approche est **particulièrement adaptée pour Google Flights** car elle permet de capturer les réponses JSON complètes de l'API interne, contenant tous les vols et métadonnées.

## Activation

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

config = CrawlerRunConfig(
    capture_network_requests=True,   # Active la capture réseau
    capture_console_messages=True    # Optionnel : logs console JS
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com", config=config)

    if result.network_requests:
        print(f"Captured {len(result.network_requests)} network events")
```

## Structure des Données Capturées

Les données capturées sont accessibles via `result.network_requests` - une liste de dictionnaires avec un champ `event_type` indiquant le type d'événement.

### Types d'événements

**1. Request Events** (`event_type == "request"`)
- `url` : URL de la requête
- `method` : Méthode HTTP (GET, POST, etc.)
- `headers` : En-têtes de la requête
- `post_data` : Données POST (si applicable)
- `resource_type` : Type de ressource (xhr, fetch, document, etc.)
- `is_navigation_request` : Boolean indiquant si c'est une navigation
- `timestamp` : Timestamp Unix de la capture

**2. Response Events** (`event_type == "response"`)
- `url` : URL de la réponse
- `status` : Code HTTP (200, 404, etc.)
- `status_text` : Texte du statut
- `headers` : En-têtes de la réponse
- `request_timing` : Métriques de timing
- `timestamp` : Timestamp Unix de la capture

**3. Failed Request Events** (`event_type == "request_failed"`)
- `url` : URL de la requête échouée
- `method` : Méthode HTTP
- `resource_type` : Type de ressource
- `failure_text` : Description de l'erreur (ex: "net::ERR_ABORTED 404")
- `timestamp` : Timestamp Unix de la capture

## Exemples de Filtrage

### Filtrer par type d'événement

```python
if result.network_requests:
    # Séparer par type d'événement
    requests = [r for r in result.network_requests
                if r.get("event_type") == "request"]
    responses = [r for r in result.network_requests
                 if r.get("event_type") == "response"]
    failures = [r for r in result.network_requests
                if r.get("event_type") == "request_failed"]

    print(f"Requests: {len(requests)}, Responses: {len(responses)}, Failed: {len(failures)}")
```

### Filtrer par pattern URL

```python
# Identifier les appels API
api_calls = [r for r in result.network_requests
             if r.get("event_type") == "response"
             and "api" in r.get("url", "").lower()]

# Filtrer requêtes XHR/Fetch (souvent des API)
xhr_requests = [r for r in result.network_requests
                if r.get("resource_type") in ["xhr", "fetch"]]

# Capturer réponses JSON Google Flights (exemple)
gf_responses = [r for r in result.network_requests
                if r.get("event_type") == "response"
                and "google.com/travel" in r.get("url", "")]
```

### Analyser les échecs

```python
# Identifier ressources échouées
for failure in failures:
    print(f"Failed: {failure.get('url')} - {failure.get('failure_text')}")

# Compter échecs par type
from collections import Counter
failure_types = Counter(f.get("failure_text") for f in failures)
print(failure_types)
```

## Cas d'Usage Google Flights

### Contexte

Google Flights charge les résultats via des appels API internes qui retournent du JSON structuré. Au lieu de parser le HTML rendu (qui peut être incomplet ou manquer des vols), le network capture permet de récupérer directement ces données JSON.

### Workflow Recommandé

```python
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def extract_google_flights_data(url: str):
    config = CrawlerRunConfig(
        capture_network_requests=True,
        wait_until="networkidle",  # Attendre fin des requêtes réseau
        delay_before_return_html=2.0  # Laisser temps aux API de répondre
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            return None

        # Filtrer les réponses API Google Flights
        flight_responses = [
            r for r in result.network_requests
            if r.get("event_type") == "response"
            and r.get("status") == 200
            and "google.com" in r.get("url", "")
            and r.get("resource_type") in ["xhr", "fetch"]
        ]

        # Extraire et parser le JSON de chaque réponse
        for response in flight_responses:
            # La réponse peut contenir un champ 'body' ou 'response_body'
            # selon la version de Crawl4AI
            if "response_data" in response or "body" in response:
                try:
                    data = json.loads(response.get("response_data") or response.get("body"))
                    # Traiter les données JSON...
                    print(f"Found flight data in: {response.get('url')[:50]}...")
                except json.JSONDecodeError:
                    continue

        return flight_responses
```

## Avantages vs CSS Extraction

**Network Capture** :
- ✅ Données JSON structurées complètes (tous les vols, pas juste ceux affichés)
- ✅ Plus fiable (pas dépendant du DOM rendu)
- ✅ Métadonnées supplémentaires (IDs internes, pricing details)
- ✅ Moins fragile aux changements d'UI
- ❌ Nécessite d'identifier les bonnes URLs d'API
- ❌ Peut nécessiter du reverse engineering

**CSS Extraction** :
- ✅ Plus simple à mettre en place
- ✅ Pas besoin de comprendre l'API interne
- ❌ Limité aux données visibles dans le HTML
- ❌ Fragile aux changements de structure CSS
- ❌ Peut manquer des vols non rendus initialement

## Points Clés

- **Performances** : Le network capture ajoute un overhead minimal (~5-10% de temps de crawl)
- **Débogage** : Utiliser `capture_console_messages=True` pour voir les logs JS
- **Filtrage** : Combiner filtres `event_type`, `resource_type` et pattern URL
- **Export** : Les données peuvent être exportées en JSON pour analyse ultérieure
- **Security** : Vérifier que les données capturées ne contiennent pas de secrets (tokens, API keys)

## Use Cases Typiques

1. **API Discovery** : Identifier les endpoints et flux de données cachés dans les SPAs
2. **Extraction Complète** : Récupérer toutes les données JSON d'une page (pas juste le rendu)
3. **Debugging** : Localiser erreurs JS et requêtes échouées
4. **Performance Analysis** : Analyser les timings et patterns de chargement
5. **Security Audit** : Détecter requêtes tierces non souhaitées

# Resource Blocking - Optimisation Bandwidth

## Description

Le blocage de ressources permet de réduire significativement la consommation de bandwidth en empêchant le chargement de ressources non essentielles (images, fonts, stylesheets). Cette optimisation est particulièrement utile pour le scraping où seules les données textuelles ou les réponses API sont nécessaires.

## Méthodes Disponibles

### 1. BrowserConfig - text_mode (Simple)

Active un mode texte qui désactive images et contenus lourds. **Attention** : désactive aussi le JavaScript, ce qui peut casser les sites dynamiques comme Google Flights.

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    text_mode=True,  # Désactive images ET JavaScript
    light_mode=True  # Désactive features background pour performance
)
```

**Limitations** :
- ❌ Désactive JavaScript → incompatible avec Google Flights
- ✅ Simple à activer
- ✅ Gain performance 3-4x pour sites statiques

### 2. BrowserConfig - extra_args (Chrome Flags)

Utilise les flags Chrome pour désactiver uniquement les images tout en gardant JavaScript actif.

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    extra_args=["--blink-settings=imagesEnabled=false"]
)
```

**Limitations** :
- ✅ Garde JavaScript actif
- ❌ Ne bloque pas fonts/stylesheets
- ❌ Contrôle limité sur les types de ressources

### 3. Hook on_page_context_created (Recommandé)

Utilise le système de hooks Crawl4AI pour intercepter les requêtes via Playwright `context.route()`. **Méthode la plus flexible et recommandée**.

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
from playwright.async_api import Page, BrowserContext, Route

async def block_heavy_resources(
    page: Page,
    context: BrowserContext,
    **kwargs
) -> Page:
    """Bloque images, fonts et stylesheets pour réduire bandwidth."""
    async def route_filter(route: Route) -> None:
        resource_type = route.request.resource_type
        if resource_type in ["image", "font", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()

    await context.route("**/*", route_filter)
    return page

# Utilisation
browser_config = BrowserConfig(headless=True)

async with AsyncWebCrawler(config=browser_config) as crawler:
    crawler.crawler_strategy.set_hook(
        "on_page_context_created",
        block_heavy_resources
    )
    result = await crawler.arun(url="https://example.com")
```

## Blocage par Domaine Spécifique

Pour bloquer des domaines spécifiques (ex: gstatic.com pour Google) :

```python
BLOCKED_DOMAINS = [
    "fonts.gstatic.com",
    "fonts.googleapis.com",
    "www.gstatic.com",
]

async def block_specific_domains(
    page: Page,
    context: BrowserContext,
    **kwargs
) -> Page:
    """Bloque domaines spécifiques et types de ressources lourdes."""
    async def route_filter(route: Route) -> None:
        url = route.request.url
        resource_type = route.request.resource_type

        # Bloquer domaines spécifiques
        if any(domain in url for domain in BLOCKED_DOMAINS):
            await route.abort()
        # Bloquer types de ressources lourdes
        elif resource_type in ["image", "font", "media"]:
            await route.abort()
        else:
            await route.continue_()

    await context.route("**/*", route_filter)
    return page
```

## Types de Ressources Playwright

| Type | Description | Impact Bandwidth |
|------|-------------|------------------|
| `document` | Page HTML principale | ❌ Ne pas bloquer |
| `stylesheet` | Fichiers CSS | Moyen (~5-10%) |
| `image` | Images (png, jpg, gif, webp, svg) | Élevé (~20-40%) |
| `font` | Polices (woff, woff2, ttf) | Moyen (~10-20%) |
| `script` | JavaScript | ❌ Ne pas bloquer (casse sites dynamiques) |
| `xhr` | Requêtes AJAX | ❌ Ne pas bloquer (données API) |
| `fetch` | Fetch API | ❌ Ne pas bloquer (données API) |
| `media` | Audio/Vidéo | Élevé si présent |
| `websocket` | WebSocket | ❌ Ne pas bloquer |
| `manifest` | Web App Manifest | Faible |
| `other` | Autres ressources | Variable |

## Compatibilité avec Network Capture

Le blocage de ressources et le network capture sont **indépendants et compatibles** :

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def block_heavy_resources(page, context, **kwargs):
    async def route_filter(route):
        if route.request.resource_type in ["image", "font"]:
            await route.abort()
        else:
            await route.continue_()
    await context.route("**/*", route_filter)
    return page

browser_config = BrowserConfig(headless=True)
run_config = CrawlerRunConfig(
    capture_network_requests=True,  # Network capture actif
    wait_until="networkidle"
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    crawler.crawler_strategy.set_hook("on_page_context_created", block_heavy_resources)
    result = await crawler.arun(url="https://example.com", config=run_config)

    # Les requêtes XHR/Fetch sont toujours capturées
    api_responses = [r for r in result.network_requests
                     if r.get("resource_type") in ["xhr", "fetch"]]
```

**Points clés** :
- Les ressources bloquées apparaissent comme `request_failed` dans network_requests
- Les requêtes XHR/Fetch (API) ne sont pas affectées par le blocage images/fonts
- Le blocage réduit le temps de chargement total → network capture plus rapide

## Impact Bandwidth Estimé

| Ressources Bloquées | Économie Bandwidth | Impact Fonctionnel |
|---------------------|-------------------|-------------------|
| Images seules | ~30-40% | Aucun pour scraping data |
| Images + Fonts | ~50-60% | Aucun pour scraping data |
| Images + Fonts + CSS | ~60-70% | Rendu visuel dégradé (non pertinent) |
| Domaines tiers (analytics, ads) | ~10-20% | Aucun |

## Recommandations Google Flights

Pour le scraping Google Flights avec network capture :

1. **Bloquer** : `image`, `font`, `media`, domaines `gstatic.com`
2. **Ne pas bloquer** : `script`, `xhr`, `fetch`, `document`
3. **Garder** : JavaScript actif (essentiel pour charger les résultats)

```python
GOOGLE_BLOCKED_DOMAINS = [
    "fonts.gstatic.com",
    "fonts.googleapis.com",
    "maps.googleapis.com",
    "play.google.com",
]

async def optimize_google_flights(page, context, **kwargs):
    """Optimisation bandwidth pour Google Flights."""
    async def route_filter(route):
        url = route.request.url
        resource_type = route.request.resource_type

        # Bloquer domaines non essentiels
        if any(domain in url for domain in GOOGLE_BLOCKED_DOMAINS):
            await route.abort()
        # Bloquer ressources lourdes
        elif resource_type in ["image", "font", "media"]:
            await route.abort()
        else:
            await route.continue_()

    await context.route("**/*", route_filter)
    return page
```

# Exemples Projet flight-search-api

## Configuration Complète Google Flights

Exemple complet de configuration utilisée dans le projet pour Google Flights :

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from app.core import get_settings

settings = get_settings()

# Configuration navigateur avec stealth mode et proxy
browser_config = BrowserConfig(
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    proxy_config={
        "server": f"http://pr.decodo.com:8080",
        "username": f"customer-{username}-country-FR",
        "password": password,
    },
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
    ],
    enable_stealth=True,
)

# Configuration crawl avec network capture
crawler_config = CrawlerRunConfig(
    wait_until="networkidle",
    page_timeout=30000,
    wait_for="css:.pIav2d",  # Attendre résultats de vols
    capture_network_requests=True,
    delay_before_return_html=settings.crawler.crawl_delay_s,
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        url="https://www.google.com/travel/flights?...",
        config=crawler_config
    )

    if not result.success:
        logger.error("Crawl failed", extra={"error": result.error})
        raise CrawlerError(result.error)

    # Détection captcha
    if "recaptcha" in result.html.lower() or "h-captcha" in result.html.lower():
        logger.warning("Captcha detected", extra={"url": url})
        raise CaptchaDetectedError("Google Flights captcha")

    return result.html
```

## Configuration Kayak avec Network Capture

Exemple spécifique pour Kayak utilisant network capture pour récupérer les données poll :

```python
from app.utils import capture_kayak_poll_data

async def crawl_after_goto_hook(
    page: Page,
    context: BrowserContext,
    url: str,
    response: Response,
    **kwargs: object,
) -> Page:
    """Hook qui capture poll_data Kayak après chargement page."""
    try:
        poll_data = await capture_kayak_poll_data(
            page,
            timeout=60.0,
        )
        # Stocker poll_data pour usage ultérieur
        logger.info("Poll data captured", extra={"keys": list(poll_data.keys())})
    except Exception as e:
        logger.warning("Poll_data capture failed", extra={"error": str(e)})

    return page

# Configuration Kayak
browser_config = BrowserConfig(
    headless=True,
    magic=True,  # Active mode spécial Kayak
)

run_config = CrawlerRunConfig(
    wait_until="networkidle",
    page_timeout=60000,
    simulate_user=True,
    override_navigator=True,
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    crawler.crawler_strategy.set_hook("after_goto", crawl_after_goto_hook)
    result = await crawler.arun(url=kayak_url, config=run_config)
```

## Retry Logic avec Tenacity

Exemple d'intégration avec stratégie de retry du projet :

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from app.services.retry_strategy import RetryStrategy

@retry(**RetryStrategy.get_crawler_retry())
async def crawl_with_retry(url: str, provider: str) -> str:
    """Crawl avec retry automatique sur erreurs réseau."""
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        # Validation résultat
        if not result.success:
            raise NetworkError(f"Crawler failed: {result.error}")

        if result.status_code in [403, 429, 500, 502, 503, 504]:
            raise NetworkError(f"HTTP {result.status_code}")

        return result.html

# Configuration retry (depuis app/services/retry_strategy.py)
# - stop_after_attempt(3)
# - wait_exponential(multiplier=1, min=2, max=10)
# - reraise=True
```

# Troubleshooting Spécifique Projet

## Erreur "Proxy Connection Failed"

**Symptôme** : `ProxyError: Cannot connect to proxy` ou `NetworkError: ERR_PROXY_CONNECTION_FAILED`

**Causes** :
1. Credentials Decodo invalides
2. Bandwidth épuisé sur le compte proxy
3. Country targeting incorrect
4. Proxy rotation désactivée dans `.env`

**Debug** :
```bash
# 1. Tester proxy manuellement
curl -x http://customer-XXX-country-FR:password@pr.decodo.com:8080 https://ipinfo.io

# 2. Vérifier configuration proxy dans logs
grep "proxy_host" logs/app.log

# 3. Vérifier rotation activée
grep "PROXY_ROTATION_ENABLED" .env
```

**Fix** :
```python
# Vérifier format username Decodo
# ✅ BON : customer-USERNAME-country-FR-sessid-123
# ❌ MAUVAIS : customer-USERNAME  (manque country + sessid)

# Activer rotation dans .env
PROXY_ROTATION_ENABLED=true
PROXY_ROTATION_MAX_SESSION_ID=100
```

## Erreur "TimeoutError after 30s"

**Symptôme** : `asyncio.TimeoutError` après timeout configuré

**Causes** :
1. Google Flights/Kayak charge lent (JS lourd)
2. Proxy latence élevée
3. Captcha non détecté (page bloque infiniment)
4. Timeout global trop court

**Fix** :
```python
# 1. Augmenter timeouts dans settings
crawler:
  crawl_global_timeout_s: 60  # Au lieu de 30
  crawl_page_timeout_ms: 60000  # Au lieu de 30000

# 2. Utiliser wait_until moins strict
run_config = CrawlerRunConfig(
    wait_until="domcontentloaded",  # Au lieu de "networkidle"
    page_timeout=60000,
)

# 3. Ajouter logging pour identifier étape bloquée
logger.info("Starting crawl", extra={"url": url, "timeout": timeout})
```

## Erreur "Captcha Detected" Silencieux

**Symptôme** : Crawl réussit mais HTML vide ou ne contient aucun résultat de vol

**Causes** :
1. Captcha affiché mais non détecté par patterns
2. Proxy IP banni temporairement
3. User-Agent trop suspect

**Debug** :
```python
# 1. Activer screenshot pour debug
run_config = CrawlerRunConfig(
    screenshot=True,
    screenshot_wait_for="css:body",
)

# 2. Vérifier patterns captcha dans HTML
if result.html:
    patterns = ["g-recaptcha", "h-captcha", "captcha", "challenge"]
    for pattern in patterns:
        if pattern in result.html.lower():
            logger.warning(f"Captcha pattern found: {pattern}")

# 3. Forcer rotation proxy
if captcha_detected:
    proxy_service.get_next_proxy()
```

**Fix** :
- Augmenter pool de session IDs proxy
- Randomiser User-Agent entre crawls
- Ajouter delay entre requêtes (rate limiting)

## Erreur "Empty HTML Returned"

**Symptôme** : `result.html` est vide ou contient `<html><head></head><body></body></html>`

**Causes** :
1. JavaScript non exécuté (timeout trop court)
2. Consent popup non fermé
3. Page bloque scripts proxy
4. wait_for selector incorrect

**Fix** :
```python
# 1. Vérifier consent popup géré
async def _handle_consent(page: Page) -> None:
    selectors = ['button:has-text("Tout accepter")', 'button:has-text("Accept all")']
    for selector in selectors:
        try:
            button = await page.wait_for_selector(selector, timeout=10000)
            if button:
                await button.click()
                await asyncio.sleep(1)
                logger.info("Consent clicked")
                return
        except TimeoutError:
            continue

# 2. Augmenter delay avant retour HTML
run_config = CrawlerRunConfig(
    delay_before_return_html=3.0,  # Laisser temps JS de s'exécuter
    wait_for="css:.pIav2d",  # Attendre élément spécifique
)
```

## Erreur "Poll Data is None" (Kayak)

**Symptôme** : `poll_data` capturé est `None` alors que crawl réussit

**Causes** :
1. Network capture non activé
2. Timeout capture poll trop court
3. URL Kayak non valide (endpoint ne retourne pas poll)
4. Hook `after_goto` non configuré

**Fix** :
```python
# 1. Vérifier network capture activé
run_config = CrawlerRunConfig(
    capture_network_requests=True,  # CRITIQUE pour Kayak
    magic=True,
)

# 2. Augmenter timeout poll capture
poll_data = await capture_kayak_poll_data(
    page,
    timeout=90.0,  # Au lieu de 60.0
)

# 3. Vérifier URL Kayak valide
# ✅ BON : https://www.kayak.fr/flights/PAR-NYC/2025-06-01?...
# ❌ MAUVAIS : https://www.kayak.fr/hotels/...  (pas flights)
```

# Performance Benchmarks (Local Tests)

Résultats de performance mesurés en local sur la stack actuelle (Python 3.13, Windows 10, 16GB RAM, Fiber 1Gbps).

| Scénario | Temps Moyen | P95 | P99 | Notes |
|----------|-------------|-----|-----|-------|
| **Google Flights - Single city** | 8.5s | 12s | 15s | Sans proxy, stealth mode activé |
| **Google Flights - Single city + proxy** | 12.3s | 18s | 23s | Decodo France, session rotation |
| **Google Flights - Multi-city 3 segments** | 25.7s | 35s | 42s | 3 requêtes séquentielles, avec proxy |
| **Kayak - Single city** | 15.2s | 22s | 28s | Avec poll_data capture |
| **Kayak - Multi-city 3 segments** | 42.1s | 55s | 68s | 3 requêtes séquentielles, poll_data |
| **Captcha détecté** | 2.1s | 3s | 4s | Fail fast dès détection pattern |
| **Network timeout (429)** | 30.5s | 31s | 32s | Timeout global atteint |

## Métriques Détaillées

### Google Flights Single City (Baseline)

```
URL: https://www.google.com/travel/flights?hl=fr&tfs=...
Config: headless=True, stealth=True, proxy=None
Sample size: 50 crawls

Timings:
- Browser init: 1.2s ± 0.3s
- Page load (networkidle): 5.8s ± 2.1s
- HTML extraction: 0.5s ± 0.1s
- Parsing: 1.0s ± 0.2s

Success rate: 94% (47/50)
Failures: 3 x Captcha detected
```

### Kayak Poll Data Capture

```
URL: https://www.kayak.fr/flights/PAR-NYC/2025-06-01/2025-06-08
Config: headless=True, magic=True, capture_network=True
Sample size: 30 crawls

Timings:
- Browser init: 1.5s ± 0.4s
- Page load (networkidle): 9.2s ± 3.2s
- Poll data capture: 3.5s ± 1.8s  ← Variabilité élevée
- JSON parsing: 0.5s ± 0.1s

Success rate: 83% (25/30)
Failures: 5 x Poll data timeout (None returned)
```

## Impact Proxy Rotation

| Configuration | Temps Moyen | Overhead |
|--------------|-------------|----------|
| Sans proxy | 8.5s | Baseline |
| Proxy fixe (France) | 11.2s | +32% |
| Proxy avec rotation (session) | 12.3s | +45% |
| Proxy USA (latence élevée) | 16.8s | +98% |

## Optimisations Bandwidth

Impact du blocage de ressources sur temps de crawl :

| Ressources Bloquées | Temps Moyen | Économie | Bandwidth Réduit |
|---------------------|-------------|----------|-----------------|
| Aucune (baseline) | 8.5s | - | ~2.5 MB |
| Images seulement | 7.2s | -15% | ~1.5 MB (-40%) |
| Images + Fonts | 6.8s | -20% | ~1.0 MB (-60%) |
| Images + Fonts + CSS | 6.5s | -24% | ~0.8 MB (-68%) |

**Note** : Blocage CSS peut casser layout-based selectors, utiliser avec prudence.

## Recommandations Performance

### Pour Production

1. **Timeout Configuration**
   - `crawl_global_timeout_s`: 60 (permet gérer pics latence)
   - `crawl_page_timeout_ms`: 45000
   - `delay_before_return_html`: 2.0 (optimal Google Flights)

2. **Proxy Optimization**
   - Pool minimal: 50 session IDs (évite bannissement)
   - Country targeting: FR ou EU (latence <100ms)
   - Rotation automatique sur 403/429

3. **Resource Blocking**
   - Bloquer: `image`, `font`, `media`
   - Garder: `script`, `xhr`, `fetch` (essentiels JS)
   - Économie: ~60% bandwidth sans impact fonctionnel

4. **Retry Strategy**
   - Max attempts: 3
   - Backoff: exponentiel (2s → 4s → 8s)
   - Retry sur: 500, 502, 503, 504, TimeoutError
   - No retry sur: 404, 400, captcha

# Ressources

## Documentation Officielle

- **Crawl4AI Documentation** : https://docs.crawl4ai.com/
- **AsyncWebCrawler API** : https://docs.crawl4ai.com/api/async-webcrawler/
- **BrowserConfig Reference** : https://docs.crawl4ai.com/core/browser-config/
- **JsonCssExtractionStrategy** : https://docs.crawl4ai.com/extraction/no-llm-strategies/
- **Network & Console Capture** : https://docs.crawl4ai.com/advanced/network-console-capture/
- **CrawlResult Structure** : https://docs.crawl4ai.com/api/crawl-result/

## Ressources Complémentaires

- **Playwright Documentation** : https://playwright.dev/python/docs/intro
