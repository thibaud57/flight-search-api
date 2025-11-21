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

# Ressources

## Documentation Officielle

- **Crawl4AI Documentation** : https://docs.crawl4ai.com/
- **AsyncWebCrawler API** : https://docs.crawl4ai.com/api/async-webcrawler/
- **BrowserConfig Reference** : https://docs.crawl4ai.com/core/browser-config/
- **JsonCssExtractionStrategy** : https://docs.crawl4ai.com/extraction/no-llm-strategies/

## Ressources Complémentaires

- **Playwright Documentation** : https://playwright.dev/python/docs/intro
