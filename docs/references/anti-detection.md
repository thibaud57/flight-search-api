---
title: "Anti-Detection - Stealth Browsing & Detection Evasion"
description: "Référence complète anti-détection : stealth mode Crawl4AI, undetected browser mode, user-agent rotation pondérée, proxy rotation (datacenter/residential), stratégie combinée multi-couches. Techniques pour contourner Cloudflare, DataDome, Akamai. Configuration, best practices, escalade progressive."
date: "2025-17-11"
keywords: ["anti-detection", "stealth", "undetected-browser", "user-agent", "rotation", "proxies", "bot-detection", "scraping", "crawl4ai", "cloudflare", "datadome", "akamai", "fingerprinting", "headless"]
scope: ["code"]
technologies: ["crawl4ai", "playwright"]
---

# Stealth Mode Crawl4AI

## Description

Le Stealth Mode de Crawl4AI utilise `playwright-stealth` pour modifier les fingerprints du navigateur en supprimant les indicateurs détectables comme `navigator.webdriver` et en émulant un comportement de plugins réaliste.

## Exemple

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False  # Important : éviter le mode headless
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://example.com")
```

## Points clés

- **Mode headless déconseillé** : Plus facile à détecter, préférer headless=False
- **Délais requis** : Implémenter délais raisonnables entre requêtes
- **Combinaison techniques** : Combiner avec rotation proxies et user-agents pour efficacité maximale

# Undetected Browser Mode (Mode Avancé)

## Description

Pour les sites avec détection sophistiquée (Cloudflare, DataDome, Akamai), le mode Undetected Browser applique des patches plus profonds offrant une protection maximale contre les systèmes de détection modernes.

## Exemple

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    browser_type="undetected",  # Chrome non-détectable
    headless=True,
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security"
    ]
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://protected-site.com")
```

## Points clés

- **Stratégie progressive** : Commencer avec stealth mode, escalader vers undetected si bloqué
- **Protection maximale** : Combiner stealth mode + undetected browser pour sites très protégés
- **Sites cibles** : Cloudflare, DataDome, Akamai nécessitent généralement undetected browser
- **Patches profonds** : Modifications plus invasives que stealth mode seul

# User-Agent Rotation

## Description

La rotation des User-Agents alterne les chaînes d'identification du navigateur pour simuler des requêtes provenant d'utilisateurs différents. La rotation pondérée (weighted rotation) est plus efficace que la sélection purement aléatoire.

## Exemple

```python
import random

# Pool de user-agents avec poids
USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.4),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.3),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", 0.2),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.1),
]

def get_random_user_agent():
    agents, weights = zip(*USER_AGENTS)
    return random.choices(agents, weights=weights, k=1)[0]

# Utilisation avec Crawl4AI
browser_config = BrowserConfig(
    user_agent=get_random_user_agent()
)
```

## Points clés

- **User-agents réalistes** : Utiliser versions actuelles Chrome/Firefox (éviter user-agents obsolètes)
- **Pool diversifiée** : Inclure Windows, macOS, Linux pour simulation multi-plateformes
- **Rotation pondérée** : Assigner poids plus élevés aux versions modernes (Chrome 40%, Firefox 20%)
- **Combinaison obligatoire** : Combiner avec throttling et rotation proxies pour efficacité maximale

# Proxy Rotation

## Description

La rotation des proxies distribue les requêtes sur plusieurs adresses IP pour éviter les blocages. Combiner proxies avec fingerprinting du navigateur et stealth mode simule un comportement utilisateur organique.

## Types de Proxies

| Type | Détectabilité | Coût | Utilisation Recommandée |
|------|---------------|------|------------------------|
| Datacenter | Élevée | Très bas | Throttling simple |
| Residential (ISP) | Faible | Moyen-Haut | Web scraping complexe |
| Static Residential | Très faible | Haut | Connexions persistantes |
| Mobile | Très faible | Très haut | Contenu mobile-restricted |

## Exemple

**Configuration avec Stealth Mode et Proxy** :
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False,
    proxy="http://user:pass@proxy-ip:port",
    user_agent=get_random_user_agent()
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://example.com")
```

**Pool Manager Pattern** :
```python
import random
from itertools import cycle

PROXY_POOL = [
    "http://proxy1:port",
    "http://proxy2:port",
    "http://proxy3:port",
]

proxy_cycle = cycle(PROXY_POOL)

def get_next_proxy():
    return next(proxy_cycle)

# Ou sélection aléatoire pour plus de variation
def get_random_proxy():
    return random.choice(PROXY_POOL)
```

## Points clés

- **Types recommandés** : ISP/Static Residential proxies pour évasion optimale (détectabilité très faible)
- **Pool manager** : Implémenter rotation intelligente avec cycle() ou random.choice()
- **Fingerprint association** : Associer chaque proxy à nouveau fingerprint navigateur pour cohérence
- **Monitoring requis** : Monitorer taux de succès et adapter stratégie de rotation selon blocages

# Stratégie Complète Combinée

## Description

Approche multi-couches combinant toutes les techniques anti-détection pour maximiser l'évasion. Cette stratégie progressive permet d'adapter le niveau de protection selon la sophistication de la détection rencontrée.

## Exemple

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
import random
import asyncio

# Configuration avec toutes les techniques
browser_config = BrowserConfig(
    enable_stealth=True,           # Stealth mode
    headless=False,                # Désactiver headless
    browser_type="chromium",       # Ou "undetected" si nécessaire
    user_agent=get_random_user_agent(),  # User-agent rotation
    proxy=get_next_proxy(),        # Proxy rotation
    viewport={"width": 1920, "height": 1080},
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox"
    ]
)

# Avec délais aléatoires
async with AsyncWebCrawler(config=browser_config) as crawler:
    for url in urls:
        result = await crawler.arun(url)
        await asyncio.sleep(random.uniform(2, 5))  # Délai humain
```

## Points clés

- **Couche 1** : Stealth Mode + User-Agent Rotation (protection basique)
- **Couche 2** : Ajouter Proxy Rotation (distribution IP)
- **Couche 3** : Basculer Undetected Browser si blocages (protection maximale)
- **Couche 4** : Délais aléatoires 2-5s entre requêtes (comportement humain)
- **Approche progressive** : Commencer simple, escalader selon besoins

# Ressources

## Documentation Officielle

- **Crawl4AI Undetected Browser** : https://docs.crawl4ai.com/advanced/undetected-browser/
- **Crawl4AI BrowserConfig** : https://docs.crawl4ai.com/core/browser-config/
- **Playwright Stealth** : https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth

## Ressources Complémentaires

- **User-Agent Strings Database** : https://useragentstring.com/
- **Browser Fingerprinting Guide** : https://pixelprivacy.com/resources/browser-fingerprinting/
- **Cloudflare Bot Detection** : https://developers.cloudflare.com/bots/
- **DataDome Documentation** : https://docs.datadome.co/
