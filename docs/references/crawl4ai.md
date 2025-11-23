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
