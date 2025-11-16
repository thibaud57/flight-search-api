# Matrice de Compatibilité - flight-search-api

**Date de dernière mise à jour** : 16 novembre 2025

## Vue d'ensemble

| Technologie | Version Recommandée | Python 3.13 | Statut Production | Notes Critiques |
|-------------|---------------------|-------------|-------------------|-----------------|
| **Python** | 3.13.1+ | ✅ Natif | ✅ Stable | Release 7 oct 2024, bugfix 3 déc 2024 |
| **FastAPI** | 0.121.2+ | ✅ Oui | ✅ Stable | Support Python 3.8-3.14 |
| **Pydantic** | 2.12.4+ (≥2.8.0) | ✅ v2.8.0+ | ✅ Stable | **CRITIQUE** : v2.8.0 min pour Python 3.13 |
| **tenacity** | 9.1.2+ | ✅ Oui | ✅ Stable | Support async complet |
| **crawl4ai** | 0.7.7+ | ✅ Oui | ✅ Stable | Playwright auto-installé via `crawl4ai-setup` |
| **uvicorn** | 0.30+ | ✅ Oui | ✅ Stable | Serveur ASGI production-ready |

---

## Détails par Technologie

### 1. Python 3.13.1

**Version actuelle** : `3.13.1` (3 décembre 2024)

**Stabilité** : ✅ Production-ready (première bugfix après 3.13.0)

**Breaking Changes Majeurs** :
- ❌ 19 modules stdlib supprimés (`aifc`, `cgi`, `cgitb`, `telnetlib`, etc.)
- ❌ `2to3` et `lib2to3` complètement supprimés
- ❌ Fonctions dépréciées dans `typing` et `urllib`
- ⚠️ Centaines de changements C API (impact sur libs natives)

**Nouvelles Features Pertinentes** :
- ✅ **PEP 695** : Type hints simplifiés (`class Response[T]` au lieu de `Generic[T]`)
- ✅ Messages d'erreur en couleur (meilleur débogage)
- ✅ Améliorations asyncio 5-15% (gain direct pour FastAPI)
- ⚠️ JIT Compiler expérimental (désactivé par défaut, gain 0-5%)
- ⚠️ Free-threading expérimental (peu pertinent pour APIs async)

**Compatibilité Écosystème** :
- ✅ FastAPI, Pydantic v2.8+, uvicorn, httpx, SQLAlchemy 2.0+, pytest

**Recommandation** : ✅ **OK pour production** avec Pydantic ≥ 2.8.0

**Sources** :
- https://docs.python.org/3.13/whatsnew/3.13.html
- https://peps.python.org/pep-0695/
- https://www.python.org/downloads/release/python-3130/

---

### 2. FastAPI 0.121.2

**Version actuelle** : `0.121.2` (13 novembre 2024)

**Stabilité** : ✅ Production-ready (dernière version stable)

**Breaking Changes depuis 0.100.x** :
- ⚠️ **v0.118.0** : Cycle de vie dépendances `yield` modifié
  - Code après `yield` s'exécute **après envoi réponse** (pas avant)
  - Impact sur libération ressources (sessions DB, fichiers, etc.)

**Support Pydantic v2** :
- ✅ Pydantic v1 et v2 supportés (`>1.7.4` et `<3.0.0`)
- ✅ Pydantic v2 recommandé (20x+ performance)
- ⚠️ Pydantic v1 en dépréciation (sera supprimé futur)

**Support Async** :
- ✅ Routes `async def` natives
- ✅ Dépendances `async def` natives
- ✅ Mélange libre async/sync (résolution graphe auto)

**Support Python** :
- ✅ Python 3.8+ minimum
- ✅ Python 3.13 confirmé
- ✅ Python 3.14 confirmé (ajouté v0.118.3)

**Tests Async** :
- ✅ TestClient sync : `def test_*()`
- ❌ TestClient async : Ne fonctionne PAS avec `async def test_*()`
- ✅ Solution : `httpx.AsyncClient` + `ASGITransport` + `@pytest.mark.anyio`

**Recommandation** : ✅ **Production-ready** - Vérifier cycle de vie `yield`

**Sources** :
- https://fastapi.tiangolo.com/release-notes/
- https://github.com/tiangolo/fastapi/releases
- https://fastapi.tiangolo.com/advanced/async-tests/

---

### 3. Pydantic 2.12.4

**Version actuelle** : `2.12.4` (5 novembre 2025)

**Stabilité** : ✅ Production-ready

**CRITIQUE Python 3.13** :
- ❌ **Pydantic < 2.8.0 INCOMPATIBLE avec Python 3.13**
- ✅ **Pydantic ≥ 2.8.0 requis ABSOLUMENT**
- ✅ Support Python 3.14 depuis v2.12.0

**Breaking Changes v1 → v2 (Top 5)** :

| V1 | V2 | Impact |
|----|-----|--------|
| `.dict()` | `.model_dump()` | 🔴 Très haut |
| `.json()` | `.model_dump_json()` | 🔴 Très haut |
| `.parse_obj()` | `.model_validate()` | 🔴 Très haut |
| `class Config` | `model_config = ConfigDict(...)` | 🔴 Haut |
| `@validator` | `@field_validator` | 🔴 Haut |
| `@root_validator` | `@model_validator` | 🔴 Haut |
| `BaseSettings` intégré | `pip install pydantic-settings` | 🔴 Très haut |
| `Optional[T]` = défaut None | `Optional[T]` = requis (peut être None) | 🔴 Très haut |

**field_validator vs @validator** :
```python
# V1
@validator('name')
def validate_name(cls, v):
    return v.upper()

# V2
@field_validator('name', mode='after')
@classmethod
def validate_name(cls, v: str) -> str:
    return v.upper()
```

**Pydantic Settings v2** :
```bash
pip install pydantic-settings  # Paquet séparé obligatoire
```

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='APP_',
        env_file='.env',
        case_sensitive=False
    )
    api_key: str
```

**Performance** :
- ✅ **17x plus rapide** que Pydantic v1 en moyenne
- ✅ Jusqu'à **50x** dans certains cas
- ✅ Réécriture en Rust via `pydantic-core`

**Migration** :
```bash
pip install bump-pydantic
bump-pydantic my_package  # Automatisation migration
```

**Recommandation** : ✅ **Migration v1→v2 smooth** (2-5 jours) - ROI très haut

**Sources** :
- https://docs.pydantic.dev/latest/migration/
- https://docs.pydantic.dev/latest/concepts/validators/
- https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- https://github.com/pydantic/pydantic/releases

---

### 4. tenacity 9.1.2

**Version actuelle** : `9.1.2` (2 avril 2024)

**Stabilité** : ✅ Production-ready

**Support Async** :
- ✅ Décorateur `@retry` avec async/await natif
- ✅ `AsyncRetrying` context manager
- ✅ Sleep asynchrone (non-bloquant)

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(httpx.TimeoutException)
)
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url, timeout=10)
```

**Wait Strategies** :

| Stratégie | Configuration | Use Case |
|-----------|---------------|----------|
| **Fixed** | `wait_fixed(2)` | Délais constants |
| **Random** | `wait_random(min=1, max=2)` | Anti-patterns |
| **Exponential** | `wait_exponential(multiplier=1, min=4, max=10)` | Systèmes distribués |
| **Exp + Jitter** | `wait_random_exponential(multiplier=1, max=60)` | **RECOMMANDÉ** |

**Stop Strategies** :
- `stop_after_attempt(N)` : Max tentatives
- `stop_after_delay(X)` : Max délai secondes
- Combinaison avec `|` opérateur

**Retry Conditions** :
```python
retry=retry_if_exception_type((
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.NetworkError
))
```

**Python 3.13** : ✅ Confirmé compatible (version 9.1.1+)

**Best Practice Web Scraping** :
- ✅ Exponential backoff + jitter (évite thundering herd)
- ✅ Timeouts explicites
- ✅ Exceptions spécifiques réseau (pas 404)
- ✅ Callbacks logging (`before_sleep`, `after`)

**Recommandation** : ✅ **Parfait pour retry logic async**

**Sources** :
- https://tenacity.readthedocs.io/en/latest/
- https://tenacity.readthedocs.io/en/latest/index.html#async-code
- https://github.com/jd/tenacity/releases

---

### 5. crawl4ai 0.7.7

**Version actuelle** : `0.7.7` (15 novembre 2024)

**Stabilité** : ✅ Production-ready

**AsyncWebCrawler** :
- ✅ API 100% asynchrone native
- ✅ `arun()` : Crawl single URL
- ✅ `arun_many()` : Crawl multi-URL avec rate limiting
- ✅ Context manager (`async with`)

**Playwright Intégré** :
- ✅ Installation automatique via `crawl4ai-setup`
- ✅ Browsers : Chromium (défaut), Firefox, WebKit
- ✅ Commande post-install : `crawl4ai-setup` (auto-install binaries)

**Installation** :
```bash
pip install -U crawl4ai
crawl4ai-setup          # Auto-install Playwright
crawl4ai-doctor         # Validation setup
```

**Stealth Mode (Anti-Détection)** :

| Mode | Configuration | Niveau |
|------|---------------|--------|
| **Basic Stealth** | `enable_stealth=True` | Basique |
| **Undetected** | `browser_type="undetected"` | **Enterprise** |

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Mode undetected (recommandé Google Flights)
browser_config = BrowserConfig(
    browser_type="undetected",  # Bypass Cloudflare/Akamai
    headless=True,
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security"
    ]
)
```

**Features Anti-Bot** :
- ✅ Masquage fingerprints navigateur
- ✅ Désactivation AutomationControlled
- ✅ Rotation user-agents
- ✅ Bypass Cloudflare, Akamai, protections enterprise

**Extraction Strategies** :

| Stratégie | Coût | Performance | Use Case |
|-----------|------|-------------|----------|
| **JsonCssExtractionStrategy** | ✅ Gratuit | ⚡ Ultra-rapide | Données structurées (RECOMMANDÉ Google Flights) |
| **LLMExtractionStrategy** | ❌ Payant (API) | 🐢 Lent | Données non-structurées, sémantique |

**JsonCssExtractionStrategy (Recommandé)** :
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "price": ".price-value",
    "departure": ".departure-time",
    "airline": ".airline-name"
}

strategy = JsonCssExtractionStrategy(schema=schema)
```

**Avantages CSS** :
- ✅ Zéro coût API
- ✅ Déterministe et reproductible
- ✅ Scalable (1000+ pages parallèles)
- ✅ Pas de dépendance LLM

**Proxy Support** :
- ✅ HTTP, HTTPS, SOCKS5
- ✅ Authentification (username/password)
- ✅ Rotation automatique (`RoundRobinProxyStrategy`)

```python
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy, ProxyConfig

proxies = ProxyConfig.from_env()  # Format: "ip:port:user:pass,..."
strategy = RoundRobinProxyStrategy(proxies=proxies)
```

**Python 3.13** : ✅ Confirmé compatible

**Recommandation** : ✅ **Parfait pour Google Flights scraping**
- Undetected browser (anti-bot enterprise)
- JsonCssExtractionStrategy (gratuit, rapide)
- Proxy rotation (évite ban IP)

**Sources** :
- https://docs.crawl4ai.com/
- https://docs.crawl4ai.com/core/browser-config/
- https://docs.crawl4ai.com/advanced/undetected-browser/
- https://docs.crawl4ai.com/extraction/no-llm-strategies/
- https://github.com/unclecode/crawl4ai/releases

---

## Matrice de Compatibilité Croisée

### Dépendances Critiques

| Dépendance A | Dépendance B | Compatibilité | Notes |
|--------------|--------------|---------------|-------|
| **Python 3.13** | **Pydantic ≥2.8.0** | ✅ REQUIS | ❌ Blocker si < 2.8.0 |
| **Python 3.13** | **FastAPI 0.121.2** | ✅ OK | Support 3.8-3.14 |
| **Python 3.13** | **crawl4ai 0.7.7** | ✅ OK | Confirmé compatible |
| **Python 3.13** | **tenacity 9.1.2** | ✅ OK | Confirmé compatible |
| **FastAPI 0.121.2** | **Pydantic 2.12.4** | ✅ OK | Support v1 et v2 |
| **crawl4ai 0.7.7** | **Playwright** | ✅ Auto | Installé via `crawl4ai-setup` |
| **tenacity 9.1.2** | **asyncio** | ✅ Natif | Retry strategies async |

### Conflits Potentiels

| Conflit | Risque | Solution |
|---------|--------|----------|
| **Pydantic < 2.8.0 + Python 3.13** | 🔴 Blocker absolu | Upgrade Pydantic ≥ 2.8.0 |
| **FastAPI < 0.100 + Pydantic v2** | 🟡 Incompatibilité | Upgrade FastAPI ≥ 0.100 |
| **crawl4ai sans crawl4ai-setup** | 🟡 Playwright manquant | Exécuter `crawl4ai-setup` post-install |

---

## Configuration Recommandée

### pyproject.toml

```toml
[project]
name = "flight-search-api"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.121.2",
    "pydantic>=2.12.4",        # CRITIQUE: ≥2.8.0 pour Python 3.13
    "pydantic-settings>=2.0",  # Séparé depuis Pydantic v2
    "crawl4ai>=0.7.7",
    "tenacity>=9.1.2",
    "uvicorn>=0.30",
    "httpx>=0.27",             # Client HTTP async
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.6",
    "mypy>=1.11",
]
```

### Post-Install

```bash
# 1. Install dépendances
pip install -e ".[dev]"

# 2. Setup crawl4ai (installe Playwright)
crawl4ai-setup

# 3. Vérification
crawl4ai-doctor
python -c "import crawl4ai; print(crawl4ai.__version__)"
```

---

## Risques Identifiés

| Risque | Sévérité | Mitigation |
|--------|----------|------------|
| **Pydantic < 2.8.0 avec Python 3.13** | 🔴 Critique | Forcer `pydantic>=2.12.4` dans pyproject.toml |
| **Breaking change FastAPI 0.118.0** | 🟡 Moyen | Vérifier cycle de vie dépendances `yield` |
| **Oubli crawl4ai-setup** | 🟡 Moyen | Documenter dans README + CI/CD |
| **Pydantic v1 déprécié** | 🟢 Faible | Migrer v2 maintenant (ROI positif) |

---

## Checklist Validation Compatibilité

- [x] Python 3.13.1 installé
- [x] Pydantic ≥ 2.8.0 confirmé
- [x] FastAPI ≥ 0.121.2 confirmé
- [x] tenacity ≥ 9.1.2 confirmé
- [x] crawl4ai ≥ 0.7.7 confirmé
- [ ] `crawl4ai-setup` exécuté (à faire après install)
- [ ] `crawl4ai-doctor` validé
- [ ] Tests unitaires Pydantic v2 (field_validator)
- [ ] Tests async tenacity + httpx
- [ ] Tests crawl4ai undetected mode + proxy

---

## Recommandation Finale

### ✅ STACK VALIDÉE POUR PRODUCTION

**Verdict** : Toutes les technologies sont compatibles Python 3.13 et production-ready.

**Points Critiques** :
1. ✅ Utiliser **Pydantic ≥ 2.12.4** (≥2.8.0 strict minimum)
2. ✅ Exécuter **crawl4ai-setup** après installation
3. ⚠️ Vérifier **cycle de vie `yield`** FastAPI 0.118.0+
4. ✅ Migrer **Pydantic v1 → v2** maintenant (gains 17x)
5. ✅ Utiliser **JsonCssExtractionStrategy** (pas LLM)
6. ✅ Activer **undetected browser mode** pour Google Flights

**ROI Migration** :
- Performance validation : +17x (Pydantic v2)
- Performance asyncio : +5-15% (Python 3.13)
- Coûts API : $0 (JsonCSS vs LLM)
- Temps migration : 2-5 jours
- Support long terme : 5 ans (Python 3.13)

---

**Dernière validation** : 16 novembre 2025
