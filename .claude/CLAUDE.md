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

### Structure Arborescence

```
flight-search-api/
├── .claude/
│   ├── commands/
│   │   └── execute-plan-phase.md
│   ├── CLAUDE.md           # Standards, conventions (ce fichier)
│   └── PLAN.md             # Plan d'action détaillé
│
├── .github/
│   └── workflows/
│       ├── ci.yml          # Quality checks (Phase 3.6)
│       └── release.yml     # Release automation (Phase 0.2)
│
├── docs/
│   ├── references/         # Documentation technique modulaire
│   │   ├── anti-detection.md
│   │   ├── captcha-detection.md
│   │   ├── crawl4ai.md
│   │   ├── decodo-proxies.md
│   │   ├── dokploy.md
│   │   ├── fastapi.md
│   │   ├── github-actions.md
│   │   ├── google-flights.md
│   │   ├── pydantic-v2.md
│   │   └── tenacity.md
│   ├── ARCHITECTURE.md     # Architecture + ADR
│   ├── CHANGELOG.md        # Historique versions
│   ├── PLANNING.md         # Specs détaillées (Phase 4)
│   ├── REFERENCES.md       # Index références
│   └── VERSIONS.md         # Matrice compatibilité
│
├── app/
│   ├── api/
│   │   └── routes.py       # Endpoints FastAPI
│   ├── core/
│   │   ├── config.py       # Pydantic Settings
│   │   └── logger.py       # Structured logging
│   ├── models/
│   │   ├── request.py      # SearchRequest, Flight, DateRange
│   │   └── response.py     # SearchResponse, FlightResult, SearchStats
│   ├── services/
│   │   ├── combination_generator.py    # Génère permutations multi-city
│   │   ├── crawler_service.py          # Crawl4AI + retry logic
│   │   ├── flight_parser.py            # JsonCssExtractionStrategy
│   │   ├── proxy_service.py            # Decodo config + rotation
│   │   ├── search_service.py           # Orchestration + Top 10 ranking
│   │   └── (captcha_solver.py)         # Phase 7 optionnelle
│   ├── utils/              # Helpers génériques
│   └── main.py             # FastAPI app entry point
│
├── tests/
│   ├── integration/
│   │   ├── test_api_routes.py
│   │   └── test_health.py
│   └── unit/
│       ├── test_combination_generator.py
│       ├── test_config.py
│       ├── test_crawler_service.py
│       ├── test_flight_parser.py
│       ├── test_models.py
│       ├── test_proxy_service.py
│       ├── test_search_service.py
│       └── (test_captcha_solver.py)    # Phase 7
│
├── .dockerignore
├── .env.example            # Template variables env
├── .gitignore
├── Dockerfile              # Multi-stage optimisé Dokploy
├── pyproject.toml          # Dependencies + tools config
└── README.md
```

### Principes Organisation

**Séparation des responsabilités** :
- `app/api/` : Couche HTTP (routes, validation)
- `app/core/` : Configuration et logging
- `app/models/` : Schémas Pydantic (request/response)
- `app/services/` : Logique métier (scraping, parsing, orchestration)
- `app/utils/` : Helpers réutilisables

**Documentation modulaire** :
- `docs/references/` : Docs techniques par technologie (10 fichiers)
- `docs/REFERENCES.md` : Index léger avec liens
- Avantage : Chargement ciblé (~44% économie tokens)

**Tests miroir** :
- Structure `tests/` reflète `app/`
- `unit/` : Tests isolés avec mocks
- `integration/` : Tests end-to-end avec TestClient

**Configuration centralisée** :
- `pyproject.toml` : Dependencies + ruff + mypy + pytest
- `.env.example` : Template variables (jamais committer `.env`)
- `.github/workflows/` : CI/CD automation

---

## 🔄 Workflow Développement

### Installation & Setup

**Prérequis** :
- Python 3.13.1+
- [uv](https://github.com/astral-sh/uv) (package manager moderne)
- Docker (optionnel, pour build image)

**Installation dépendances** :
```bash
# Installation projet + deps dev
uv sync --all-extras

# Post-install : Setup Playwright (automatique via crawl4ai-setup)
crawl4ai-setup
```

**Note** : `crawl4ai-setup` installe automatiquement Playwright et ses dépendances système. Pas besoin d'installation manuelle de Playwright.

### Commandes Développement

**Lancer l'application** :
```bash
# Mode développement (hot-reload)
fastapi dev app/main.py

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Quality Checks** (à exécuter avant commit) :
```bash
# Lint + Auto-fix
ruff check . --fix

# Format
ruff format .

# Type check
mypy app/

# Tests unitaires
pytest tests/unit/ -v

# All-in-one pre-commit
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

**Tests** :
```bash
# Tests unitaires uniquement
pytest tests/unit/ -v

# Tests intégration uniquement
pytest tests/integration/ -v

# Tous les tests
pytest -v

# Avec coverage
pytest --cov=app --cov-report=html
# Rapport généré dans htmlcov/index.html

# Test spécifique
pytest tests/unit/test_models.py::test_search_request_validation -v
```

**Docker** :
```bash
# Build image
docker build -t flight-search-api .

# Run container
docker run -p 8000:8000 --env-file .env flight-search-api

# Run avec override env vars
docker run -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e DECODO_USERNAME=customer-XXX-country-FR \
  flight-search-api
```

### Workflow Feature Development

**Étape 1 : Créer branche feature**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/nom-descriptif
```

**Étape 2 : Développer avec TDD**
```bash
# 1. Écrire tests d'abord
vim tests/unit/test_nouveau_service.py

# 2. Run tests (doivent échouer)
pytest tests/unit/test_nouveau_service.py -v

# 3. Implémenter feature
vim app/services/nouveau_service.py

# 4. Run tests (doivent passer)
pytest tests/unit/test_nouveau_service.py -v

# 5. Refactor si nécessaire
```

**Étape 3 : Vérifications locales**
```bash
# Quality checks complets
ruff check . --fix && ruff format . && mypy app/ && pytest -v

# Si tout passe → Commit
git add .
git commit -m "feat(services): add nouveau service"
```

**Étape 4 : Push + Pull Request**
```bash
# Push branche
git push -u origin feature/nom-descriptif

# Créer PR sur GitHub : feature/nom-descriptif → develop
# CI s'exécute automatiquement (lint, format, typecheck, tests)
# Merger après validation CI
```

**Étape 5 : Cleanup après merge**
```bash
git checkout develop
git pull origin develop
git branch -d feature/nom-descriptif
```

### Variables Environnement

**Fichier `.env` local** (créer depuis `.env.example`) :
```bash
cp .env.example .env
vim .env  # Remplir avec vraies valeurs
```

**Variables requises** :
```bash
# Logging
LOG_LEVEL=INFO  # DEBUG en dev, INFO en prod

# Decodo Proxies
DECODO_USERNAME=customer-{api_key}-country-FR
DECODO_PASSWORD=your_password
DECODO_PROXY_HOST=pr.decodo.com:8080

# Features
PROXY_ROTATION_ENABLED=true
CAPTCHA_DETECTION_ENABLED=true

# Optionnel (Phase 7)
# CAPTCHA_SOLVING_ENABLED=false
# TWOCAPTCHA_API_KEY=your_2captcha_key
```

**⚠️ Sécurité** :
- ❌ **JAMAIS** committer `.env` (déjà dans `.gitignore`)
- ✅ Utiliser `.env.example` comme template
- ✅ Secrets stockés dans Dokploy UI pour production

### Debugging

**Logs structurés** :
```python
# Dans le code
logger.info(
    "Flight search started",
    extra={
        "search_id": search_id,
        "destinations": destinations
    }
)

# Output JSON
{"asctime": "2025-11-16T10:30:00", "name": "flight-search-api", "levelname": "INFO", "message": "Flight search started", "search_id": "abc123", "destinations": ["Paris", "Tokyo"]}
```

**Activer DEBUG logs** :
```bash
LOG_LEVEL=DEBUG fastapi dev app/main.py
```

**Breakpoints** (avec debugpy si besoin) :
```python
# Ajouter dans le code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Troubleshooting Commun

**Erreur `crawl4ai-setup` échoue** :
- Vérifier connexion internet (télécharge Playwright browsers)
- Espace disque suffisant (~500MB)
- Permissions écriture dans cache directory

**Tests échouent avec `ModuleNotFoundError`** :
```bash
# Réinstaller deps
uv sync --all-extras
```

**Mypy erreurs après ajout nouvelle lib** :
```bash
# Ajouter override dans pyproject.toml
[[tool.mypy.overrides]]
module = ["nouvelle_lib.*"]
ignore_missing_imports = true
```

**Docker build lent** :
```bash
# Utiliser build cache
docker build --cache-from flight-search-api:latest -t flight-search-api .
```

---

## 🧪 Tests

### Stratégie Tests

**Approche TDD** (Test-Driven Development) :
1. Écrire tests d'abord (red)
2. Implémenter feature minimale (green)
3. Refactorer (refactor)

**Pyramide Tests** :
```
        /\
       /  \      10% - E2E (integration)
      /    \
     /------\    30% - Integration (API routes)
    /        \
   /----------\  60% - Unit (services, models, utils)
  /__________\
```

### Types de Tests

**1. Tests Unitaires** (`tests/unit/`)

**Caractéristiques** :
- Testent 1 fonction/classe isolée
- Utilisent mocks pour dépendances externes
- Rapides (<1s pour 100 tests)
- Coverage minimum 80%

**Mocking Strategy** :
```python
# Mock Crawl4AI
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(
        html="<html>Mock HTML</html>",
        success=True
    )
    return crawler

# Mock Decodo Proxies
@pytest.fixture
def mock_proxy_config():
    return ProxyConfig(
        host="pr.decodo.com",
        port=8080,
        username="customer-XXX-country-FR",
        password="test_password"
    )

# Mock HTML Google Flights
@pytest.fixture
def mock_google_flights_html():
    return """
    <div class="flight-card">
        <span class="price-value">1250.00</span>
        <span class="airline-name">Air France</span>
        <time class="departure-time">2025-06-01T10:30:00</time>
    </div>
    """
```

**Exemples Tests** :
```python
# tests/unit/test_models.py
def test_search_request_validation():
    request = SearchRequest(
        destinations=["Paris", "Tokyo"],
        date_range=DateRange(start="2025-06-01", end="2025-06-15")
    )
    assert len(request.destinations) == 2

def test_search_request_invalid_dates():
    with pytest.raises(ValidationError):
        SearchRequest(
            destinations=["Paris"],
            date_range=DateRange(start="2025-06-15", end="2025-06-01")
        )

# tests/unit/test_crawler_service.py
@pytest.mark.asyncio
async def test_crawl_with_captcha_detection(mock_crawler, mock_proxy_config):
    html_with_captcha = "<html><div id='recaptcha'>Captcha</div></html>"
    mock_crawler.arun.return_value.html = html_with_captcha

    service = CrawlerService(crawler=mock_crawler, proxy_service=mock_proxy_config)
    with pytest.raises(CaptchaDetectedError):
        await service.crawl_google_flights("https://example.com")
```

**2. Tests Intégration** (`tests/integration/`)

**Caractéristiques** :
- Testent interactions entre composants
- Utilisent TestClient FastAPI
- Pas de mocks pour services internes
- Mocks uniquement pour Crawl4AI/Decodo (dépendances externes)

**Exemples Tests** :
```python
# tests/integration/test_api_routes.py
from fastapi.testclient import TestClient

def test_search_flights_endpoint(client: TestClient, mock_crawler):
    response = client.post("/api/v1/search-flights", json={
        "destinations": ["Paris", "Tokyo"],
        "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 10

def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**3. Tests End-to-End** (manuels, pas de CI)

**Caractéristiques** :
- Testent flow complet avec vraies dépendances
- Utilisent vraie clé Decodo (bandwidth coûteux)
- Exécutés manuellement avant release
- Pas dans CI (coût + lenteur)

**Exemple** :
```bash
# .env avec vraies clés
DECODO_USERNAME=customer-REAL_KEY-country-FR
DECODO_PASSWORD=real_password

# Run app
fastapi dev app/main.py

# Test manuel
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "destinations": ["Paris", "Tokyo"],
    "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
  }'

# Vérifier logs : captcha detection, proxy rotation, parsing success
```

### Commandes Pytest

**Exécution Tests** :
```bash
# Tests unitaires (rapides, CI)
pytest tests/unit/ -v

# Tests intégration (moyens, CI)
pytest tests/integration/ -v

# Tous les tests
pytest -v

# Tests parallèles (speedup 4x)
pytest -n auto -v

# Test spécifique
pytest tests/unit/test_models.py::test_search_request_validation -v

# Tests avec pattern
pytest -k "captcha" -v
```

**Coverage** :
```bash
# Coverage HTML (interactif)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Coverage terminal
pytest --cov=app --cov-report=term-missing

# Coverage avec seuil minimum
pytest --cov=app --cov-fail-under=80

# Coverage XML (pour CI/Codecov)
pytest --cov=app --cov-report=xml
```

**Options Utiles** :
```bash
# Stop au premier échec
pytest -x

# Verbose avec output complet
pytest -vv

# Afficher print() statements
pytest -s

# Reruns pour tests flaky
pytest --reruns 3

# Markers (catégories tests)
pytest -m "slow"  # Tests marqués @pytest.mark.slow
pytest -m "not slow"  # Exclure tests lents
```

### Configuration Pytest

**`pyproject.toml`** :
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=app",
    "--cov-report=term-missing:skip-covered",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
asyncio_mode = "auto"
```

### Fixtures Communs

**`tests/conftest.py`** (partagé entre tous les tests) :
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app

@pytest.fixture
def client():
    """TestClient FastAPI pour tests intégration."""
    return TestClient(app)

@pytest.fixture
def mock_crawler():
    """Mock AsyncWebCrawler."""
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(
        html="<html>Mock</html>",
        success=True
    )
    return crawler

@pytest.fixture
def mock_google_flights_html():
    """HTML Google Flights valide pour parsing."""
    return """
    <div class="flight-card">
        <span class="price-value">1250.00</span>
    </div>
    """
```

### Bonnes Pratiques

**Naming** :
- Fichiers : `test_*.py`
- Classes : `TestClassName`
- Fonctions : `test_descriptive_name`

**Structure Test** :
```python
def test_feature():
    # Arrange (setup)
    input_data = {"key": "value"}

    # Act (exécution)
    result = function_to_test(input_data)

    # Assert (vérification)
    assert result == expected_value
```

**Async Tests** :
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

**Parametrized Tests** (DRY) :
```python
@pytest.mark.parametrize("input,expected", [
    ("Paris", "PAR"),
    ("Tokyo", "TYO"),
    ("New York", "NYC"),
])
def test_city_to_code(input, expected):
    assert city_to_code(input) == expected
```

**Tests Exception** :
```python
def test_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        invalid_function()
    assert "error detail" in str(exc_info.value)
```

### CI Integration

**GitHub Actions** (`.github/workflows/ci.yml`) :
```yaml
- name: Run tests
  run: |
    pytest tests/unit/ --cov=app --cov-report=xml --cov-fail-under=80

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

**Règles** :
- ✅ Tests unitaires obligatoires (CI bloque si échec)
- ✅ Coverage minimum 80% (Phase 3+)
- ❌ Tests intégration en local uniquement (coût Decodo)
- ❌ Tests E2E manuels (pré-release)

---

## 🐳 Docker

### Dockerfile Multi-Stage

**Structure** (Phase 3.2) :

```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --no-dev

# Install Playwright via crawl4ai-setup
RUN uv run crawl4ai-setup

# Stage 2: Runtime
FROM python:3.13-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy deps from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application code
WORKDIR /app
COPY app/ ./app/

# Set user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run app
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Optimisations** :
- ✅ Multi-stage build (réduction taille image ~60%)
- ✅ Cache uv dependencies (build incrémentiel rapide)
- ✅ Non-root user (sécurité)
- ✅ Healthcheck natif
- ✅ Playwright installé via `crawl4ai-setup`

### Commandes Docker

**Build** :
```bash
# Build standard
docker build -t flight-search-api .

# Build avec cache
docker build --cache-from flight-search-api:latest -t flight-search-api .

# Build avec tag version
docker build -t flight-search-api:v1.0.0 .

# Build sans cache (clean build)
docker build --no-cache -t flight-search-api .
```

**Run** :
```bash
# Run avec .env file
docker run -p 8000:8000 --env-file .env flight-search-api

# Run avec env vars inline
docker run -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e DECODO_USERNAME=customer-XXX-country-FR \
  -e DECODO_PASSWORD=password \
  flight-search-api

# Run en background (detached)
docker run -d -p 8000:8000 --name flight-api flight-search-api

# Run avec volumes (développement)
docker run -p 8000:8000 -v $(pwd)/app:/app/app flight-search-api
```

**Gestion Containers** :
```bash
# Lister containers actifs
docker ps

# Logs container
docker logs flight-api

# Logs en temps réel
docker logs -f flight-api

# Stop container
docker stop flight-api

# Remove container
docker rm flight-api

# Remove image
docker rmi flight-search-api
```

**Debugging** :
```bash
# Shell interactif dans container
docker exec -it flight-api /bin/bash

# Health check manuel
docker exec flight-api curl http://localhost:8000/health

# Inspecter container
docker inspect flight-api
```

### Docker Compose (développement)

**`docker-compose.yml`** (optionnel, Phase 3+) :
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app:/app/app  # Hot-reload en dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Commandes** :
```bash
# Up
docker-compose up

# Up en background
docker-compose up -d

# Rebuild
docker-compose up --build

# Logs
docker-compose logs -f

# Down
docker-compose down
```

### Optimisations Avancées

**1. Layer Caching** :
```dockerfile
# COPY dependencies avant code (cache optimal)
COPY pyproject.toml ./
RUN uv sync --no-dev

# COPY code en dernier (changements fréquents)
COPY app/ ./app/
```

**2. Image Size Reduction** :
```dockerfile
# Utiliser alpine pour taille minimale (optionnel)
FROM python:3.13-alpine AS builder

# Multi-stage pour exclure build tools
# Runtime image contient uniquement .venv + code
```

**3. Security** :
```dockerfile
# Non-root user obligatoire
USER appuser

# Scan vulnérabilités
docker scan flight-search-api
```

**4. Build Args** (pour CI/CD) :
```dockerfile
ARG VERSION=dev
LABEL version=$VERSION

# Build
docker build --build-arg VERSION=v1.0.0 -t flight-search-api:v1.0.0 .
```

### Déploiement Dokploy

**Configuration Dokploy** :

1. **Connecter Repo GitHub** :
   - URL : `https://github.com/username/flight-search-api`
   - Branch : `master`
   - Auto-deploy sur push

2. **Variables Environnement** (UI Dokploy) :
   ```
   LOG_LEVEL=INFO
   DECODO_USERNAME=customer-XXX-country-FR
   DECODO_PASSWORD=***
   DECODO_PROXY_HOST=pr.decodo.com:8080
   PROXY_ROTATION_ENABLED=true
   CAPTCHA_DETECTION_ENABLED=true
   ```

3. **Build Settings** :
   - Dockerfile path : `./Dockerfile`
   - Port : `8000`
   - Health check : `/health`

4. **Resources** :
   - CPU : 1 vCPU
   - RAM : 1 GB (minimum pour Playwright)
   - Storage : 5 GB

**Logs Dokploy** :
```bash
# Via UI Dokploy
# Logs → flight-search-api → View Logs

# Filtrer par level
# Search: "levelname": "ERROR"

# Monitoring
# Métriques CPU/RAM/Network
```

### Troubleshooting Docker

**Erreur `crawl4ai-setup` échoue** :
```bash
# Vérifier espace disque dans container
docker exec flight-api df -h

# Augmenter ressources Docker Desktop
# Settings → Resources → Memory: 4GB minimum
```

**Image trop grosse** :
```bash
# Analyser layers
docker history flight-search-api

# Utiliser dive pour inspection détaillée
dive flight-search-api
```

**Build lent** :
```bash
# Utiliser BuildKit (plus rapide)
DOCKER_BUILDKIT=1 docker build -t flight-search-api .

# Cache externe (CI/CD)
docker buildx build --cache-from type=registry,ref=user/app:cache \
  --cache-to type=registry,ref=user/app:cache -t flight-search-api .
```

**Container crash au démarrage** :
```bash
# Logs détaillés
docker logs flight-api

# Override entrypoint pour debug
docker run -it --entrypoint /bin/bash flight-search-api
```

### Best Practices

**DO** :
- ✅ Multi-stage builds (réduction taille)
- ✅ Non-root user (sécurité)
- ✅ Health checks (monitoring)
- ✅ `.dockerignore` (exclure .git, tests, etc.)
- ✅ Layer caching optimal (deps avant code)

**DON'T** :
- ❌ Secrets hardcodés dans Dockerfile
- ❌ Root user en production
- ❌ Image sans health check
- ❌ Build sans cache (lenteur CI/CD)
- ❌ Image alpine pour Python (compatibilité)

---

## 📦 Git

### 1. Stratégie de Branches

**Modèle GitFlow simplifié** :

```
master (production)
  ↑
develop (intégration)
  ↑
feature/* (développement)
```

**Branches principales** :

- **`master`** : Code en production, stable, uniquement via merge de `develop`
  - Protégée : pas de push direct
  - Chaque merge = nouvelle version taggée (v1.0.0, v1.1.0, etc.)

- **`develop`** : Branche d'intégration, prête pour release
  - Merge depuis branches `feature/*` via Pull Requests
  - Tests CI doivent passer avant merge
  - Base pour créer nouvelles features

**Branches de travail** :

- **`feature/*`** : Développement de fonctionnalités
  - Nomenclature : `feature/nom-descriptif` (kebab-case)
  - Créées depuis `develop`
  - Mergées dans `develop` via PR
  - Supprimées après merge

**Exemples** :
```bash
# Créer feature depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/initial-setup

# Après développement : Push + PR vers develop
git push -u origin feature/initial-setup
# Créer PR sur GitHub/GitLab : feature/initial-setup → develop

# Après merge : Nettoyer
git checkout develop
git pull origin develop
git branch -d feature/initial-setup
```

**Workflow Release** :

**Dev Releases (v0.x.x-xxx)** :
1. Développement sur `feature/*`
2. Merge `feature/*` → `develop` (via PR)
3. Tag version sur `develop` (ex: `v0.2.0-structure`)
4. GitHub Actions crée Release automatiquement (marquée `prerelease`)

**Production Releases (v1.x.x+)** :
1. Développement sur `feature/*`
2. Merge `feature/*` → `develop` (via PR)
3. Quand `develop` prête : Merge `develop` → `master` (via PR)
4. Tag version sur `master` (ex: `v1.0.0`)
5. GitHub Actions crée Release automatiquement (release stable)

---

### 2. Conventional Commits

**Format obligatoire** :

```
<type>(<scope>): <description>

[body optionnel]

[footer optionnel]
```

**Types standards** :

- **`feat`** : Nouvelle fonctionnalité
  - Exemple : `feat(api): add multi-city search endpoint`
  - Incrémente version MINOR (v0.1.0 → v0.2.0)

- **`fix`** : Correction de bug
  - Exemple : `fix(parser): handle missing price field`
  - Incrémente version PATCH (v0.1.0 → v0.1.1)

- **`docs`** : Documentation uniquement
  - Exemple : `docs: add crawl4ai usage examples`
  - Pas d'impact version (dev phases)

- **`refactor`** : Refactoring sans changement fonctionnel
  - Exemple : `refactor(crawler): extract proxy config to separate class`

- **`test`** : Ajout/modification tests
  - Exemple : `test(parser): add edge cases for date parsing`

- **`chore`** : Maintenance (deps, config, build)
  - Exemple : `chore: update dependencies`

- **`ci`** : Modifications CI/CD
  - Exemple : `ci: add caching for uv dependencies`

- **`perf`** : Amélioration performance
  - Exemple : `perf(crawler): reduce memory usage in batch processing`

**Règles projet** :

✅ **Description impérative** : "add feature" (pas "added" ou "adds")
✅ **Minuscules** : `feat(api):` (pas `Feat(API):`)
✅ **Scope optionnel** : Composant affecté (api, parser, crawler, docs)
✅ **Max 72 caractères** pour la première ligne
✅ **Breaking changes** : Ajouter `!` après type/scope + footer `BREAKING CHANGE:`

**Exemples validés** :

```bash
# Feature simple
git commit -m "feat(api): add flight search endpoint"

# Fix avec scope
git commit -m "fix(parser): handle null departure time"

# Breaking change
git commit -m "feat(api)!: change response format to include metadata

BREAKING CHANGE: Response structure changed from flat array to object with metadata field"

# Documentation
git commit -m "docs(plan): add Phase 0.3 CHANGELOG update"

# Refactoring
git commit -m "refactor(crawler): extract retry logic to decorator"
```

**Anti-patterns** :

❌ `git commit -m "fixed bug"` (pas de type)
❌ `git commit -m "Feat: Added feature"` (majuscule, past tense)
❌ `git commit -m "update code"` (trop vague)
❌ `git commit -m "feat(api): added new endpoint for searching flights with multiple destinations and returning top 10 results"` (trop long)

---

### 3. Pre-commit Checks

**Exécution avant chaque commit** :

```bash
# Exécuter manuellement (recommandé pendant dev)
ruff check . && ruff format . && mypy app/ && pytest tests/unit/

# Si succès → commit autorisé
# Si échec → corriger avant commit
```

**Checks obligatoires** :

1. **Ruff Lint** : `ruff check .`
   - Vérifie erreurs code (pycodestyle, pyflakes, naming, etc.)
   - Auto-fix disponible : `ruff check . --fix`
   - Doit passer sans erreur (warnings tolérés selon config)

2. **Ruff Format** : `ruff format .`
   - Formate code selon standards (line length 88, quotes doubles)
   - Auto-applique formatage (pas juste check)
   - Doit passer sans changement après formatage

3. **Mypy Type Check** : `mypy app/`
   - Vérifie cohérence types (strict mode)
   - Détecte erreurs potentielles à runtime
   - Doit passer sans erreur (0 issues)

4. **Tests Unitaires** : `pytest tests/unit/`
   - Exécute tests rapides (pas d'intégration)
   - Coverage minimum 80% (Phase 3+)
   - Doit passer 100% des tests

**Workflow local** :

```bash
# 1. Développer feature
# ... édition code ...

# 2. Avant commit : Exécuter checks
ruff check . --fix          # Auto-fix lint
ruff format .               # Auto-format
mypy app/                   # Type check
pytest tests/unit/          # Tests rapides

# 3. Si tous passent : Commit
git add .
git commit -m "feat(api): add endpoint"

# 4. Push
git push origin feature/ma-feature
```

**Automation (Phase 3.6+)** :

- **CI GitHub Actions** : Exécute automatiquement sur PR
- **Bloque merge** si checks échouent
- **Pas de pre-commit hook local** (éviter friction dev)
- **Responsabilité développeur** : Exécuter avant push

**Gestion erreurs** :

```bash
# Ruff lint échoue
ruff check .
# → Corriger manuellement OU
ruff check . --fix  # Auto-fix si possible

# Mypy échoue
mypy app/
# → Corriger annotations types
# → Vérifier imports manquants

# Tests échouent
pytest tests/unit/ -v
# → Debug test spécifique
# → Corriger régression
```

**Règles projet** :

✅ Exécuter checks **avant chaque commit** (discipline)
✅ Ne **jamais** commit si checks échouent
✅ Utiliser `--fix` pour ruff (gain temps)
✅ CI bloque PR si checks échouent (safety net)
❌ Ne **pas** forcer commit avec `--no-verify` (sauf urgence justifiée)

---

### 4. Workflow Pull Request

**Processus complet** :

```
1. Développement local (feature/*)
   ↓
2. Push branche
   ↓
3. Créer Pull Request → develop
   ↓
4. CI GitHub Actions (lint, format, typecheck, tests)
   ↓
5. Review (optionnel pour solo dev)
   ↓
6. Merge squash → develop
   ↓
7. Supprimer branche feature
```

**Étapes détaillées** :

**1. Créer Pull Request** :

```bash
# Après push feature
git push -u origin feature/initial-setup

# Sur GitHub/GitLab :
# - Base : develop
# - Compare : feature/initial-setup
# - Titre : Même convention que commit (ex: "feat(api): add search endpoint")
# - Description : Lister changements principaux
```

**Template PR recommandé** :

```markdown
## Description

Implémente endpoint de recherche multi-destinations

## Changements

- ✅ Ajout route POST /api/v1/flights/search
- ✅ Validation Pydantic SearchRequest
- ✅ Intégration AsyncWebCrawler
- ✅ Tests unitaires (12 tests, 95% coverage)

## Checklist

- [x] Tests passent localement
- [x] Ruff lint + format OK
- [x] Mypy type check OK
- [x] Documentation mise à jour

## Testing

```bash
pytest tests/unit/test_search.py -v
```

## Related Issues

Closes #123
```

**2. CI Validation automatique** :

- **Déclenché par** : Ouverture PR + chaque push sur branche
- **Jobs exécutés** :
  - `lint` : ruff check
  - `format` : ruff format --check
  - `typecheck` : mypy app/
  - `test` : pytest tests/unit/ --cov
- **Statut visible** : ✅ ou ❌ sur PR
- **Merge bloqué** si CI échoue

**3. Review (optionnel)** :

- **Solo dev** : Auto-review rapide (vérifier diff)
- **Team** : Assigner reviewer, attendre approval
- **Critères** :
  - Code respecte standards projet
  - Tests couvrent cas principaux
  - Pas de régression
  - Documentation à jour

**4. Merge Strategy** :

**Squash Merge (recommandé)** :

```
# Tous commits feature → 1 commit sur develop
# Commit message = titre PR
# Historique develop propre
```

**Workflow GitHub** :
1. Cliquer "Squash and merge"
2. Vérifier message commit (convention respectée)
3. Confirmer merge
4. Branche feature supprimée automatiquement

**Après merge** :

```bash
# Revenir sur develop local
git checkout develop
git pull origin develop

# Supprimer branche locale (si pas auto)
git branch -d feature/initial-setup

# Créer nouvelle feature
git checkout -b feature/next-task
```

**Gestion conflits** :

```bash
# Si develop a avancé pendant dev feature
git checkout feature/ma-feature
git fetch origin
git rebase origin/develop

# Résoudre conflits si nécessaire
# ... édition manuelle ...
git add .
git rebase --continue

# Force push (rebase réécrit historique)
git push --force-with-lease origin feature/ma-feature
```

**Règles projet** :

✅ **1 PR = 1 feature logique** (pas de mega-PR)
✅ **Titre PR = Conventional Commit** format
✅ **CI doit passer** avant merge (obligatoire)
✅ **Squash merge** pour historique propre
✅ **Supprimer branche** après merge (cleanup)
❌ **Jamais merge** si CI échoue
❌ **Jamais commit** directement sur develop/master

**Cas particuliers** :

- **Hotfix urgent** : Créer `hotfix/*` depuis master, merge direct master + cherry-pick develop
- **Documentation seule** : `docs/*` peut skip certains tests
- **WIP PR** : Préfixer titre `WIP:` pour indiquer travaux en cours (draft PR)