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

**Règles obligatoires** :
- ✅ Utiliser PEP 695 partout : `class Response[T]:`, `def process[T](items: list[T]) -> T:`
- ✅ Annoter TOUTES les signatures (args + return)
- ✅ Utiliser `list[T]`, `dict[K, V]` (pas `List[T]`, `Dict[K, V]`)
- ✅ Préférer `X | None` à `Optional[X]`
- ✅ Type alias : `type JsonDict = dict[str, str | int | float | bool | None]`
- ✅ Bounds : `class Container[T: (str, int)]:` ou `class Processor[T: BaseModel]:`

Exemples détaillés → `docs/references/fastapi.md`, `pydantic-v2.md`

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

**Règles projet** :
- ✅ TOUJOURS utiliser `async with` pour AsyncWebCrawler
- ✅ Retry logic avec tenacity (exponential backoff + jitter)
- ✅ Timeouts explicites : `httpx.AsyncClient(timeout=10)`
- ✅ Capturer exceptions spécifiques (pas `except Exception:`)
- ✅ Logger avant retry (`before_sleep` callback tenacity)

**Anti-patterns** :
- ❌ Bloquer event loop avec code sync dans routes async
- ❌ Retry sur 404 (erreur client, pas serveur)
- ❌ Pas de timeout → risque hang

Exemples complets → `docs/references/crawl4ai.md`, `tenacity.md`

---

### 5. Structured Logging (JSON, contexte)

**Règles projet** :
- ✅ Format JSON structuré avec `pythonjsonlogger`
- ✅ TOUJOURS ajouter `extra={}` avec contexte métier (search_id, destinations, proxy_used, etc.)
- ✅ Niveaux : DEBUG (dev), INFO (prod), WARNING (retry), ERROR (fail)
- ✅ Logger : captcha detection, proxy rotation, parsing errors, Top 10 résultats
- ✅ Pas de secrets dans logs (masquer API keys, passwords)

Configuration complète → `app/core/logger.py`

---

### 6. Docstrings Pragmatiques (PEP 257)

**Règle : 1 ligne par défaut** (90% des cas) :
```python
def parse_price(html: str) -> float:
    """Extrait le prix depuis le HTML Google Flights."""
```

**Format complet si nécessaire** :
- ✅ Comportement non-évident (side-effects, mutations)
- ✅ Exceptions importantes levées
- ✅ Algorithmes complexes
- ✅ API publiques (routes FastAPI)

**Règles** :
- ✅ 1 ligne suffit si signature explicite
- ✅ Focus sur **POURQUOI**, pas **QUOI**
- ❌ Pas de verbosité (ne pas répéter ce que le type dit)

---

### 7. Fichiers __init__.py

**Code applicatif (`app/`)** :
```python
# Exports explicites avec __all__
from app.main import app
__all__ = ["app"]
```
- ✅ Définir `__all__` (API publique du package)
- ✅ Facilite imports : `from app import app`

**Tests (`tests/`)** :
```python
# Vides (juste docstring)
"""Tests package."""
```
- ✅ Fichiers présents (marque package Python)
- ❌ Pas d'exports ni `__all__` (convention pytest)

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
│   ├── specs/              # Documentation specs modulaire
│   ├── ARCHITECTURE.md     # Architecture + ADR
│   ├── CHANGELOG.md        # Historique versions
│   ├── SPECS.md            # Spécifications techniques détaillées (Phase 4)
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
uv run crawl4ai-setup
```

**Note** : `crawl4ai-setup` installe automatiquement Playwright et ses dépendances système. Pas besoin d'installation manuelle de Playwright.

**Alternative exécution commandes** :

Deux méthodes équivalentes pour exécuter les outils (`ruff`, `mypy`, `pytest`, etc.) :

**Méthode 1 : Environnement virtuel activé** (workflow local standard)
```bash
# Activer venv une fois
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/macOS

# Puis utiliser commandes directement
ruff check .
mypy app/
pytest tests/
```

**Méthode 2 : uv run** (CI/CD + local sans activation venv)
```bash
# Pas besoin d'activer venv manuellement
uv run ruff check .
uv run mypy app/
uv run pytest tests/
```

**Quand utiliser `uv run`** :
- ✅ **Obligatoire en CI/CD** (GitHub Actions) : venv non activé automatiquement
- ✅ **Optionnel en local** : si venv non activé ou scripts automation
- ❌ **Pas nécessaire** : si venv déjà activé dans terminal/IDE

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
  /____________\
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

### Workflow TDD par story

Pour chaque story (Phase 5) :

```
┌─────────────────────────────────────────┐
│ PHASE 1: TDD Tests Unitaires            │
├─────────────────────────────────────────┤
│ Pour chaque composant:                  │
│ 1. Écrire tests composant (red)        │
│ 2. Implémenter composant (green)       │
│ 3. Tests passent ✅                     │
│ 4. Refactor (si nécessaire)            │
│                                         │
│ Répéter pour tous composants story      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ PHASE 2: Tests Intégration              │
├─────────────────────────────────────────┤
│ 5. Écrire tests end-to-end              │
│    (TestClient si API route)            │
│ 6. Tests intégration passent ✅         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ PHASE 3: Validation Manuelle            │
├─────────────────────────────────────────┤
│ 7. Test manuel (curl/Postman)          │
│ 8. Valider UX réelle                    │
│ 9. Commit si OK                         │
└─────────────────────────────────────────┘
```

**Règles TDD strictes** :
- ✅ Tests unitaires AVANT implémentation (red → green → refactor)
- ✅ Tests intégration APRÈS tous tests unitaires de la story
- ✅ Commit seulement si TOUS les tests passent (unitaires + intégration)
- ❌ Ne JAMAIS commencer intégration si tests unitaires échouent
- ❌ Ne JAMAIS skipper tests (coverage minimum 80%)

**Quand faire tests intégration** :
- Après tous les tests unitaires de la story
- Avant le commit final
- Si story inclut API route → TestClient FastAPI obligatoire

**Formats recommandés** :

**AAA (Arrange/Act/Assert)** - Tests unitaires :
```python
def test_exemple():
    # Arrange: Setup initial
    input_data = {"key": "value"}

    # Act: Exécuter fonction
    result = fonction(input_data)

    # Assert: Vérifier résultat
    assert result == expected
```

**Given/When/Then** - Tests intégration (BDD) :
```python
def test_integration_exemple():
    # Given: État initial
    client = TestClient(app)
    request_data = {"key": "value"}

    # When: Action
    response = client.post("/endpoint", json=request_data)

    # Then: Résultat attendu
    assert response.status_code == 200
    assert response.json() == expected
```

**Exemple Story 3 (Search endpoint mock)** :

**Phase 1 - TDD Composants** :
1. Models (21 tests) → Implémentation → Tests passent ✅
2. SearchService mock (5 tests) → Implémentation → Tests passent ✅
3. Route POST /search (8 tests) → Implémentation → Tests passent ✅

**Phase 2 - Tests Intégration** :
4. End-to-end API (4 tests) → Tests passent ✅

**Phase 3 - Validation** :
5. Test manuel `curl -X POST http://localhost:8000/api/v1/search-flights`
6. Vérifier response JSON valide
7. Commit : `feat(api): add search endpoint with mock data`

**Total Story 3** : 38 tests (34 unitaires + 4 intégration), coverage ≥ 80%

---

## 🐳 Docker

**Dockerfile** : Disponible dans `/Dockerfile` (multi-stage, non-root user, healthcheck)

**Commandes essentielles** :
```bash
# Build
docker build -t flight-search-api .

# Run avec .env
docker run -p 8000:8000 --env-file .env flight-search-api

# Run en background
docker run -d -p 8000:8000 --name flight-api flight-search-api

# Logs
docker logs -f flight-api

# Stop & Remove
docker stop flight-api && docker rm flight-api
```

**Docker Compose** :
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

**Best Practices** :
- ✅ Multi-stage builds (réduction taille ~60%)
- ✅ Non-root user (sécurité)
- ✅ Healthcheck natif
- ✅ `.dockerignore` (exclure .git, tests)
- ❌ Jamais hardcoder secrets dans Dockerfile

**Documentation complète** : `docs/references/dokploy.md` (Dockerfile détaillé, troubleshooting, déploiement Dokploy, optimisations avancées)

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

**Workflow Story (sous-phase)** :
1. Lancer story : `/execute-plan-phase X.Y`
   - Commit automatique selon PLAN.md
   - Push automatique branche feature
   - Création automatique PR → develop
   - Retourne URL de la PR
2. Merger PR sur GitHub (interface web)
3. Répéter pour stories suivantes (X.Y+1)

**Workflow Epic (phase complète)** :
1. Toutes stories mergées sur develop ✅
2. Aligner master avec develop :
   ```bash
   git checkout develop && git pull
   git checkout master && git merge develop --ff-only
   ```
3. Tag version sur `master` : `git tag {version} && git push origin master --tags`
4. Release automatique via `.github/workflows/release.yml`
5. **⚠️ SYNC develop avec master** (éviter décalages futurs) :
   ```bash
   git checkout develop && git pull origin master && git push origin develop
   ```

**Distinction versions** :
- **Dev releases** : `v0.x.x-xxx` (ex: `v0.3.0-build`) → Marquées "Pre-release" sur GitHub
- **Prod releases** : `v1.x.x` (ex: `v1.0.0`) → Marquées "Latest release" sur GitHub
- Détection automatique : `contains(github.ref, '-')` dans workflow release.yml

**Notes** :
- Story = sous-phase (ex: 3.1, 3.2) → 1 PR automatique → develop
- Epic = phase complète (ex: Phase 3) → merge develop→master → tag
- `/execute-plan-phase` gère automatiquement : commit, push, PR
- User gère : merge PR, tag final Epic

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

**Processus** :
1. Push branche feature
2. Créer PR → develop (titre = Conventional Commit format)
3. CI GitHub Actions (lint, format, typecheck, tests) → doit passer
4. Review (optionnel solo dev)
5. **Squash merge** → develop
6. Supprimer branche feature

**Créer PR** :
```bash
git push -u origin feature/initial-setup
# Sur GitHub : Base=develop, Titre="feat(api): add endpoint"
```

**CI Validation** :
- Jobs : lint, format, typecheck, test
- Merge bloqué si échec

**Après merge** :
```bash
git checkout develop
git pull origin develop
git branch -d feature/initial-setup
```

**Règles** :
- ✅ 1 PR = 1 feature logique
- ✅ Titre PR = Conventional Commit
- ✅ CI doit passer avant merge
- ✅ Squash merge pour historique propre
- ❌ Jamais merge si CI échoue
- ❌ Jamais commit direct sur develop/master