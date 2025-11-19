---
title: "Captcha Detection - reCAPTCHA & hCaptcha Patterns"
description: "Référence complète détection captchas : patterns HTML reCAPTCHA v2/v3 et hCaptcha, détecteur Python regex, stratégies retry avec rotation IP (Tenacity + Proxies Decodo), configuration exponential backoff, best practices stealth mode et user-agent rotation. Consulter pour implémentation anti-captcha, logging, minimisation blocages."
date: "2025-17-11"
keywords: ["captcha", "detection", "recaptcha", "hcaptcha", "patterns", "html", "retry", "rotation", "ip", "proxy", "tenacity", "stealth-mode", "user-agent", "blocking", "decodo", "anti-detection"]
scope: ["code"]
technologies: ["crawl4ai", "tenacity", "python"]
---

# Patterns HTML de reCAPTCHA

## Description

Les patterns reCAPTCHA permettent d'identifier les différentes versions (v2 Checkbox, v2 Invisible, v3) via des éléments HTML spécifiques. La détection repose sur les classes CSS, attributs data, iframes et scripts caractéristiques. reCAPTCHA v2 affiche un challenge interactif, tandis que v3 fonctionne en arrière-plan sans interaction utilisateur.

## Exemple - reCAPTCHA v2 (Checkbox)

```html
<!-- Élément conteneur principal -->
<div class="g-recaptcha"
     data-sitekey="VOTRE_SITE_KEY"
     data-callback="onCaptchaSuccess"></div>

<!-- Iframes associés -->
<iframe src="https://www.google.com/recaptcha/api2/frame..."
        title="reCAPTCHA"></iframe>
```

**reCAPTCHA v2 Invisible** :
```html
<div class="g-recaptcha"
     data-sitekey="VOTRE_SITE_KEY"
     data-size="invisible"></div>
```

**reCAPTCHA v3** :
```javascript
<script src="https://www.google.com/recaptcha/api.js?render=VOTRE_SITE_KEY"></script>
```

## Points clés

- **Classes CSS** : `g-recaptcha`, `grecaptcha` identifient le conteneur
- **Attributs** : `data-sitekey` contient la clé du site, `data-callback` définit la fonction de succès
- **Iframes** : Source depuis `google.com/recaptcha/api` confirme la présence
- **Token caché** : `<input name="g-recaptcha-response" type="hidden">` stocke la réponse
- **v2 vs v3** : v2 affiche challenge visible, v3 est invisible (détection par script uniquement)
- **Détection v3** : Pas d'élément DOM visible, identifier via script `recaptcha/api.js?render=`

# Patterns HTML de hCaptcha

## Description

hCaptcha est une alternative à reCAPTCHA axée sur la confidentialité. La détection repose sur des éléments HTML similaires : classe CSS distinctive, attributs data, scripts de chargement spécifiques et iframes. hCaptcha utilise un challenge visuel accessible avec options de personnalisation (thème, langue).

## Exemple - hCaptcha Standard

```html
<!-- Conteneur avec classe h-captcha -->
<div class="h-captcha"
     data-sitekey="YOUR_SITEKEY"
     data-theme="light"></div>

<!-- Script de chargement -->
<script src="https://js.hcaptcha.com/1/api.js" async defer></script>

<!-- Iframes hCaptcha -->
<iframe src="https://hcaptcha.com/captcha/..."
        title="hCaptcha"></iframe>
```

## Points clés

- **Classe CSS** : `h-captcha` identifie le conteneur (vs `g-recaptcha` pour reCAPTCHA)
- **Attributs** : `data-sitekey` (clé site), `data-theme` (light/dark), `data-callback` (fonction succès)
- **Script** : Domaine spécifique `js.hcaptcha.com` vs `google.com/recaptcha`
- **Iframes** : Source depuis `hcaptcha.com/captcha/`
- **Token response** : Stocké dans `<textarea id="h-captcha-response"></textarea>`
- **Détection double** : Rechercher à la fois div `.h-captcha` ET script `js.hcaptcha.com` pour fiabilité maximale

# Code de Détection Python

```python
from html.parser import HTMLParser
from typing import Dict, List, Optional
import re

class CaptchaDetector:
    """Détecte les captchas reCAPTCHA et hCaptcha dans le HTML"""

    RECAPTCHA_V2_PATTERN = r'class=["\']g-recaptcha["\']'
    RECAPTCHA_V3_PATTERN = r'recaptcha/api\.js\?render='
    HCAPTCHA_PATTERN = r'class=["\']h-captcha["\']'
    HCAPTCHA_SCRIPT = r'js\.hcaptcha\.com'

    @staticmethod
    def detect_recaptcha_v2(html: str) -> bool:
        """Détecte reCAPTCHA v2 (checkbox ou invisible)"""
        return bool(re.search(CaptchaDetector.RECAPTCHA_V2_PATTERN, html))

    @staticmethod
    def detect_recaptcha_v3(html: str) -> bool:
        """Détecte reCAPTCHA v3"""
        return bool(re.search(CaptchaDetector.RECAPTCHA_V3_PATTERN, html))

    @staticmethod
    def detect_hcaptcha(html: str) -> bool:
        """Détecte hCaptcha"""
        has_div = bool(re.search(CaptchaDetector.HCAPTCHA_PATTERN, html))
        has_script = bool(re.search(CaptchaDetector.HCAPTCHA_SCRIPT, html))
        return has_div or has_script

    @staticmethod
    def extract_sitekey(html: str) -> Optional[str]:
        """Extrait la clé de site captcha si présente"""
        patterns = [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'sitekey:["\']([^"\']+)["\']',
            r'render=([A-Za-z0-9_-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def detect_any_captcha(html: str) -> Dict[str, bool]:
        """Détecte tous les types de captchas"""
        return {
            'recaptcha_v2': CaptchaDetector.detect_recaptcha_v2(html),
            'recaptcha_v3': CaptchaDetector.detect_recaptcha_v3(html),
            'hcaptcha': CaptchaDetector.detect_hcaptcha(html),
            'has_sitekey': CaptchaDetector.extract_sitekey(html) is not None
        }
```

# Stratégie de Retry avec Rotation IP (Tenacity + Proxies)

## Architecture Recommandée
```
Requête initiale
    ↓
[Crawl4AI + Stealth Mode]
    ↓
Captcha détecté ? → Oui → Rotate IP + Retry (Tenacity)
    ↓ Non                  ↓
    Success            [Wait exponential backoff]
                            ↓
                        Retry avec nouveau proxy
                            ↓
                        Max tentatives? → Oui → Log + Abandon
                        ↓ Non
                        Retry avec proxy suivant
```

## Implémentation Complète

```python
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
from crawl4ai import AsyncWebCrawler, BrowserConfig
import logging
import random
from typing import Dict, List

logger = logging.getLogger(__name__)

class CaptchaHandlingCrawler:
    """Crawler avec détection et retry avec rotation IP"""

    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.current_proxy_index = 0
        self.logger = logger

    def get_next_proxy(self) -> str:
        """Récupère le prochain proxy en rotation"""
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    async def _crawl_single(self, url: str, proxy: str) -> Dict:
        """Effectue un seul crawl avec un proxy"""
        browser_config = BrowserConfig(
            enable_stealth=True,
            proxy=proxy if proxy else None,
            headless=True
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url)

            # Détection captcha
            detection = CaptchaDetector.detect_any_captcha(result.html)
            is_blocked = result.status_code in [403, 429]

            return {
                'success': not (any(detection.values()) or is_blocked),
                'html': result.html,
                'status_code': result.status_code,
                'captcha_detected': detection,
                'proxy_used': proxy
            }

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.INFO)
    )
    async def crawl_with_retry(self, url: str) -> Dict:
        """
        Crawl avec retry et rotation IP.

        Stratégie:
        - 1ère tentative: Sans proxy (plus rapide)
        - 2-5ème tentatives: Avec rotation IP
        - Wait: 2^x * 2 secondes (min 4s, max 60s)
        """
        attempt_num = getattr(self.crawl_with_retry, 'retry_num', 0)
        use_proxy = attempt_num > 0
        proxy = self.get_next_proxy() if use_proxy else None

        self.logger.info(f"Attempt {attempt_num + 1} for {url}" +
                        (f" with proxy {proxy}" if proxy else " without proxy"))

        result = await self._crawl_single(url, proxy)

        if not result['success']:
            self.logger.warning(
                f"Captcha/Block detected: {result['captcha_detected']}, "
                f"Status: {result['status_code']}"
            )
            raise Exception(f"Captcha detected on attempt {attempt_num + 1}")

        self.logger.info(f"Success for {url} with proxy {result['proxy_used']}")
        return result
```

# Configuration Optimale de Retry

## Paramètres et Justifications

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| **Max tentatives** | 5 | Équilibre entre flexibilité et coûts |
| **Initial delay** | 4s | Évite les blocages immédiats |
| **Max delay** | 60s | Respecte les limites serveur |
| **Exponential base** | 2 | Croissance rapide pour éviter spam |
| **Proxy rotation** | À chaque retry | Force le changement d'IP |
| **User-Agent rotation** | À chaque tentative | Augmente la légitimité |

## Délais Progressifs
```
Tentative 1: Pas de proxy, attendre 0s
Tentative 2: Proxy 1, attendre 4s (2^1 * 2)
Tentative 3: Proxy 2, attendre 8s (2^2 * 2)
Tentative 4: Proxy 3, attendre 16s (2^3 * 2)
Tentative 5: Proxy 4, attendre 32s (2^4 * 2)
```

# Best Practices pour Minimiser les Captchas

## Approche Préventive
```python
# ✅ Utiliser des proxies résidentiels (Decodo)
# → Clés résidentiels = +95% moins de captchas

# ✅ Ajouter des délais aléatoires
import random
import asyncio

async def crawl_with_delays(urls: List[str]):
    for url in urls:
        delay = random.uniform(2, 8)  # 2-8 secondes
        await asyncio.sleep(delay)
        # Crawl...

# ✅ Rotation user-agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0"
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)
```

## Mode Stealth

```python
# ✅ Activer stealth mode
browser_config = BrowserConfig(
    enable_stealth=True,  # Masque les indicateurs bot
    headless=True,
    ignore_https_errors=True,
    extra_http_headers={
        'Accept-Language': 'fr-FR,fr;q=0.9',
        'User-Agent': get_random_user_agent()
    }
)
```

# Ressources

## Documentation Officielle

- **Google reCAPTCHA Documentation** : https://developers.google.com/recaptcha
- **hCaptcha Documentation** : https://docs.hcaptcha.com
- **Tenacity Documentation** : https://tenacity.readthedocs.io/

## Ressources Complémentaires

- **Crawl4AI Stealth Mode** : https://docs.crawl4ai.com/core/browser-config/
- **Decodo Proxies** : https://decodo.com/docs
