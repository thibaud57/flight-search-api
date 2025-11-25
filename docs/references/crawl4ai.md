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
