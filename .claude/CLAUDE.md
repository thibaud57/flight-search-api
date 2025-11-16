# CLAUDE.md - flight-search-api

**Instructions de développement et standards du projet**

---

## 📋 Contexte Projet

**Nom** : flight-search-api

**Description** : API FastAPI pour recherche de vols multi-destinations via Google Flights (scraping avec Crawl4AI + proxies Decodo)

**Stack Technique** :
- Python 3.13.1+
- FastAPI 0.121.2+
- Pydantic v2.12.4+ (Settings)
- Crawl4AI 0.7.7+ (AsyncWebCrawler + Playwright intégré)
- Tenacity 9.1.2+ (retry logic async)
- Decodo Proxies (résidentiels, France targeting)

**Architecture** : API async, scraping stealth, extraction CSS (pas de LLM), Top 10 résultats en mémoire (pas de DB)

**Approche Captcha** :
- **MVP (Phase 5-6)** : Détection uniquement (logging), pas de résolution
- **Post-MVP (Phase 7 optionnel)** : 2Captcha si monitoring montre >5% blocages

---

## 🐍 Standards Python

### 1. Type Hints Modernes (PEP 695)

**Python 3.13+ supporte la syntaxe simplifiée** :

```python
# ❌ Ancienne syntaxe (< Python 3.12)
from typing import TypeVar, Generic
T = TypeVar('T')

class Response(Generic[T]):
    data: T

# ✅ Nouvelle syntaxe PEP 695 (Python 3.12+)
class Response[T]:
    data: T

# ✅ Fonctions génériques
def process[T](items: list[T]) -> T:
    return items[0]

# ✅ Type aliases
type JsonDict = dict[str, str | int | float | bool | None]
```

**Règles obligatoires** :
- ✅ Utiliser PEP 695 partout (classes, fonctions, type aliases)
- ✅ Annoter TOUTES les signatures de fonctions (args + return)
- ✅ Utiliser `list[T]`, `dict[K, V]` au lieu de `List[T]`, `Dict[K, V]`
- ✅ Préférer `X | None` à `Optional[X]`
- ✅ Type alias avec `type` keyword pour clarté

**Contraintes** :
```python
# ✅ Bounds
class Container[T: (str, int)]:  # T doit être str ou int
    value: T

# ✅ Upper bound
class Processor[T: BaseModel]:  # T doit hériter de BaseModel
    def process(self, item: T) -> T: ...
```

---

### 2. Ruff - Linter & Formatter

**Configuration `pyproject.toml`** :

```toml
[tool.ruff]
line-length = 88
indent-width = 4
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "RUF",    # Ruff-specific rules
]
ignore = [
    "E501",   # line-too-long (géré par formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101"]  # assert allowed in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Commandes** :
```bash
ruff check .              # Lint
ruff check . --fix        # Auto-fix
ruff format .             # Format
ruff format . --check     # Check sans modifier
```

**Règles projet** :
- ✅ Exécuter `ruff check . && ruff format .` avant chaque commit
- ✅ CI/CD doit bloquer si ruff échoue
- ✅ Line length 88 (cohérence Black)
- ✅ Imports triés (isort intégré)

---

### 3. Mypy - Type Checking Strict

**Configuration `pyproject.toml`** :

```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
no_implicit_reexport = true
strict_equality = true

# Relax strict pour tests
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

# Ignorer libs sans stubs
[[tool.mypy.overrides]]
module = ["crawl4ai.*"]
ignore_missing_imports = true
```

**Flags activés par `strict = true`** :
- `--disallow-any-generics`
- `--disallow-untyped-defs`
- `--disallow-incomplete-defs`
- `--check-untyped-defs`
- `--disallow-untyped-decorators`
- `--warn-redundant-casts`
- `--warn-unused-ignores`
- `--warn-return-any`
- `--no-implicit-reexport`
- `--strict-equality`

**Commande** :
```bash
mypy app/
```

**Règles projet** :
- ✅ Strict mode OBLIGATOIRE sur `app/`
- ✅ Relax sur `tests/` (moins contraignant)
- ✅ CI/CD doit bloquer si mypy échoue
- ✅ Aucun `# type: ignore` sans justification commentée

---

### 4. Patterns Async (crawl4ai, error handling)

**Context managers async** :
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def fetch_flights(url: str) -> str:
    browser_config = BrowserConfig(
        browser_type="undetected",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url)
        return result.html
```

**Error handling async avec tenacity** :
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
)
async def fetch_with_retry(url: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
```

**Règles projet** :
- ✅ TOUJOURS utiliser `async with` pour AsyncWebCrawler
- ✅ Retry logic avec tenacity (exponential backoff + jitter)
- ✅ Timeouts explicites (ex: `httpx.AsyncClient(timeout=10)`)
- ✅ Capturer exceptions spécifiques (pas `except Exception:`)
- ✅ Logger avant retry (`before_sleep` callback tenacity)

**Anti-patterns** :
- ❌ Bloquer event loop avec code sync dans routes async
- ❌ Retry sur 404 (erreur client, pas serveur)
- ❌ Pas de timeout → risque hang

---

### 5. Structured Logging (JSON, contexte)

**Configuration logger** :
```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        timestamp=True
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logger("flight-search-api")
```

**Usage avec contexte** :
```python
logger.info(
    "Flight search started",
    extra={
        "search_id": search_id,
        "destinations": destinations,
        "date_range": date_range,
        "proxy_used": proxy_host
    }
)

logger.warning(
    "Captcha detected",
    extra={
        "url": url,
        "retry_count": retry_count,
        "captcha_type": "recaptcha"
    }
)
```

**Règles projet** :
- ✅ Format JSON structuré (machine-readable)
- ✅ TOUJOURS ajouter `extra={}` avec contexte métier
- ✅ Niveaux : DEBUG (dev), INFO (prod), WARNING (retry), ERROR (fail)
- ✅ Logger captcha detection, proxy rotation, parsing errors
- ✅ Pas de secrets dans logs (masquer API keys, passwords)

**Métriques à logger** :
- Search ID, destinations, dates
- Proxy utilisé, bandwidth consommé
- Captcha détectés (type, URL, retry count)
- Parsing success/failure
- Top 10 résultats

---

### 6. Docstrings Pragmatiques (PEP 257)

**Règle : 1 ligne par défaut** (90% des cas) :

```python
def parse_price(html: str) -> float:
    """Extrait le prix depuis le HTML Google Flights."""
    ...

async def search_flights(request: SearchRequest) -> SearchResponse:
    """Orchestre la recherche de vols multi-destinations."""
    ...
```

**Format complet uniquement si nécessaire** :

```python
@retry(stop=stop_after_attempt(5))
async def crawl_with_proxy(url: str, proxy_config: ProxyConfig) -> str:
    """
    Crawl URL avec proxy et retry logic.

    Args:
        url: URL Google Flights à crawler
        proxy_config: Configuration proxy Decodo

    Returns:
        HTML brut de la page

    Raises:
        CaptchaDetectedError: Si captcha détecté après 5 tentatives
        ProxyRotationError: Si tous les proxies échouent
    """
    ...
```

**Quand utiliser format complet** :
- ✅ Comportement non-évident (side-effects, mutations)
- ✅ Exceptions importantes levées
- ✅ Algorithmes complexes (ex: combinaison generator)
- ✅ API publiques (routes FastAPI)

**Règles projet** :
- ✅ 1 ligne suffit si signature explicite
- ✅ Pas de verbosité (ne pas répéter ce que le type dit déjà)
- ✅ Focus sur **POURQUOI**, pas **QUOI** (code montre le quoi)

**Anti-patterns** :
```python
# ❌ Redondant
def add(a: int, b: int) -> int:
    """Adds two integers and returns the result."""
    return a + b

# ✅ Inutile si évident
def add(a: int, b: int) -> int:
    return a + b
```

---

## 🚫 Anti-Patterns

### Commentaires Inline Interdits

**Règle stricte** : ❌ **AUCUN commentaire inline** sauf demande explicite user

**Pourquoi** :
- Code doit être self-explanatory (noms explicites, types, docstrings)
- Commentaires deviennent obsolètes rapidement
- Augmente bruit visuel

**Alternatives** :
```python
# ❌ Commentaire inline
price = float(html.select_one(".price").text.strip())  # Extract price from HTML

# ✅ Nom de fonction explicite
def extract_price(html: str) -> float:
    """Extrait le prix depuis le HTML."""
    return float(html.select_one(".price").text.strip())
```

**Exceptions autorisées** :
- ✅ User demande explicitement commentaires
- ✅ TODO/FIXME temporaires (à résoudre avant merge)
- ✅ Type hints complexes nécessitant clarification

**Conséquence** : PR rejetée si commentaires inline non justifiés

---

## 📁 Organisation Fichiers

_À compléter en Phase 2.3_

---

## 🔄 Workflow Développement

_À compléter en Phase 2.3_

---

## 🧪 Tests

_À compléter en Phase 2.3_

---

## 🐳 Docker

_À compléter en Phase 2.3_

---

## 📦 Git

_À compléter en Phase 0.2 et Phase 1.5_
