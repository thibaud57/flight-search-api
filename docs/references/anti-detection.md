# Techniques Anti-Détection - Référence Technique

**Date de dernière mise à jour** : 16 novembre 2025

---

## 1. Stealth Mode Crawl4AI

**Description**
Le Stealth Mode de Crawl4AI utilise `playwright-stealth` pour modifier les fingerprints du navigateur en supprimant les indicateurs détectables comme `navigator.webdriver` et en émulant un comportement de plugins réaliste.

**Configuration**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False  # Important : éviter le mode headless
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://example.com")
```

**Best Practices**
- Désactiver le mode headless (plus facile à détecter)
- Implémenter des délais raisonnables entre les requêtes
- Combiner avec d'autres techniques d'anti-détection

**Source** : https://docs.crawl4ai.com/advanced/undetected-browser/

---

## 2. Undetected Browser Mode (Mode Avancé)

**Description**
Pour les sites avec détection sophistiquée (Cloudflare, DataDome, Akamai), le mode Undetected Browser applique des patches plus profonds offrant une protection maximale contre les systèmes de détection modernes.

**Configuration**
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

**Stratégie Progressive**
1. Commencer avec navigateur régulier + stealth mode
2. Si bloqué, escalader vers undetected browser
3. Pour protection maximale, combiner stealth mode + undetected browser

**Source** : https://docs.crawl4ai.com/advanced/undetected-browser/

---

## 3. User-Agent Rotation

**Description**
La rotation des User-Agents alterne les chaînes d'identification du navigateur pour simuler des requêtes provenant d'utilisateurs différents. La rotation pondérée (weighted rotation) est plus efficace que la sélection purement aléatoire.

**Configuration avec Pool Pondéré**
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

**Best Practices**
- Utiliser des user-agents actuels et réalistes (Chrome/Firefox récents)
- Maintenir une diverse pool (Windows, macOS, navigateurs populaires)
- Assigner des poids plus élevés aux versions modernes
- Combiner avec throttling et rotation de proxies

---

## 4. Proxy Rotation

**Description**
La rotation des proxies distribue les requêtes sur plusieurs adresses IP pour éviter les blocages. Combiner proxies avec fingerprinting du navigateur et stealth mode simule un comportement utilisateur organique.

**Types de Proxies**

| Type | Détectabilité | Coût | Utilisation Recommandée |
|------|---------------|------|------------------------|
| Datacenter | Élevée | Très bas | Throttling simple |
| Residential (ISP) | Faible | Moyen-Haut | Web scraping complexe |
| Static Residential | Très faible | Haut | Connexions persistantes |
| Mobile | Très faible | Très haut | Contenu mobile-restricted |

**Configuration avec Stealth Mode et Proxy**
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

**Pool Manager Pattern**
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

**Best Practices de Rotation**
- Utiliser ISP/Static Residential proxies pour l'evasion optimale
- Implémenter un pool manager avec rotation intelligente
- Associer chaque proxy à un nouveau fingerprint du navigateur
- Monitorer les taux de succès et adapter la rotation

---

## 5. Stratégie Complète Combinée

**Configuration Multi-Couches**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
import random

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
import asyncio

async with AsyncWebCrawler(config=browser_config) as crawler:
    for url in urls:
        result = await crawler.arun(url)
        await asyncio.sleep(random.uniform(2, 5))  # Délai humain
```

**Ordre d'Application Recommandé**
1. **Couche 1** : Stealth Mode + User-Agent Rotation
2. **Couche 2** : Ajouter Proxy Rotation
3. **Couche 3** : Basculer à Undetected Browser si bloqué
4. **Couche 4** : Ajouter délais aléatoires et comportements humains
