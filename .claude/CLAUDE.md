# Table des Matières

1. [📋 Contexte Projet](#1-contexte-projet)
2. [📁 Organisation Fichiers](#2-organisation-fichiers)
   - [2.1 Structure Arborescence](#21-structure-arborescence)
   - [2.2 Principes Organisation](#22-principes-organisation)
3. [🐍 Standards Python](#3-standards-python)
   - [3.1 Type Hints Modernes (PEP 695)](#31-type-hints-modernes-pep-695)
   - [3.2 Standards Imports](#32-standards-imports)
   - [3.3 Docstrings Pragmatiques (PEP 257)](#33-docstrings-pragmatiques-pep-257)
   - [3.4 Patterns Async](#34-patterns-async-crawl4ai-error-handling)
   - [3.5 Fichiers __init__.py](#35-fichiers-__init__py)
4. [🔧 Tooling](#4-tooling)
   - [4.1 Ruff - Linter & Formatter](#41-ruff---linter--formatter)
   - [4.2 Mypy - Type Checking Strict](#42-mypy---type-checking-strict)
   - [4.3 Structured Logging](#43-structured-logging-json-contexte)
5. [🚫 Anti-Patterns](#5-anti-patterns)
   - [5.1 Commentaires Inline Interdits](#51-commentaires-inline-interdits)
6. [🧪 Tests](#6-tests)
   - [6.1 Stratégie Tests & TDD](#61-stratégie-tests--tdd)
   - [6.2 Types de Tests](#62-types-de-tests)
   - [6.3 Fixtures & Factories](#63-fixtures--factories)
   - [6.4 Configuration & Commandes](#64-configuration--commandes)
7. [🔄 Workflow Développement](#7-workflow-développement)
   - [7.1 Installation & Setup](#71-installation--setup)
   - [7.2 Commandes Quotidiennes](#72-commandes-quotidiennes)
   - [7.3 Feature Development avec TDD](#73-feature-development-avec-tdd)
   - [7.4 Debugging & Troubleshooting](#74-debugging--troubleshooting)
8. [📦 Git](#8-git)
   - [8.1 Stratégie de Branches](#81-stratégie-de-branches)
   - [8.2 Conventional Commits](#82-conventional-commits)
   - [8.3 Pre-commit Checks](#83-pre-commit-checks)
   - [8.4 Workflow Pull Request](#84-workflow-pull-request)
9. [🐳 Docker](#9-docker)

---

# 1. 📋 Contexte Projet

**Nom** : flight-search-api

**Description** : API FastAPI pour recherche de vols multi-destinations via Google Flights (scraping avec Crawl4AI + proxy provider)

**Stack Technique** :
- Python 3.13.1+
- FastAPI 0.121.2+
- Pydantic v2.12.4+ (Settings)
- Crawl4AI 0.7.7+ (AsyncWebCrawler + Playwright intégré)
- Tenacity 9.1.2+ (retry logic async)
- Proxy Provider (résidentiels, France targeting)

**Architecture** : API async, scraping stealth, extraction CSS (pas de LLM), Top 10 résultats en mémoire (pas de DB)

**Approche Captcha** :
- **MVP (Phase 5-6)** : Détection uniquement (logging), pas de résolution
- **Post-MVP (Phase 7 optionnel)** : 2Captcha si monitoring montre >5% blocages

---

# 2. 📁 Organisation Fichiers

## 2.1 Structure Arborescence

```
flight-search-api/
├── .claude/           # Standards (CLAUDE.md) + Plan (PLAN.md) + Commandes
├── .github/           # CI/CD workflows
├── docs/              # Documentation modulaire (references/, specs/, *.md)
├── app/               # Code applicatif
│   ├── api/           # Routes FastAPI
│   ├── core/          # Config + Logger
│   ├── models/        # Schémas Pydantic (request, response)
│   ├── services/      # Logique métier (crawler, parser, search, proxy)
│   ├── utils/         # Helpers réutilisables
│   └── main.py        # Entry point
├── tests/             # Structure miroir app/
│   ├── integration/   # Tests end-to-end (TestClient FastAPI)
│   ├── unit/          # Tests isolés avec mocks
│   └── fixtures/      # Factories + Mocks + Helpers
├── pyproject.toml     # Dependencies + tooling config
├── Dockerfile         # Multi-stage optimisé
└── .env.example       # Template variables environnement
```

## 2.2 Principes Organisation

### Séparation des responsabilités

- `app/api/` : Couche HTTP (routes, validation)
- `app/core/` : Configuration et logging
- `app/models/` : Schémas Pydantic (request/response)
- `app/services/` : Logique métier (scraping, parsing, orchestration)
- `app/utils/` : Helpers réutilisables

### Documentation modulaire

- `docs/references/` : Docs techniques par technologie (10 fichiers)
- `docs/REFERENCES.md` : Index léger avec liens
- Avantage : Chargement ciblé (~44% économie tokens)

### Tests miroir

- Structure `tests/` reflète `app/`
- `unit/` : Tests isolés avec mocks
- `integration/` : Tests end-to-end avec TestClient

### Configuration centralisée

- `pyproject.toml` : Dependencies + ruff + mypy + pytest
- `.env.example` : Template variables (jamais committer `.env`)
- `.github/workflows/` : CI/CD automation

---

# 3. 🐍 Standards Python

## 3.1 Type Hints Modernes (PEP 695)

### Règles obligatoires

- ✅ Utiliser PEP 695 partout : `class Response[T]:`, `def process[T](items: list[T]) -> T:`
- ✅ Annoter TOUTES les signatures (args + return)
- ✅ Utiliser `list[T]`, `dict[K, V]` (pas `List[T]`, `Dict[K, V]`)
- ✅ Préférer `X | None` à `Optional[X]`
- ✅ Ajouter `model_config = ConfigDict(extra="forbid")` sur tous les models Pydantic (rejette champs inconnus)
- ✅ Type alias : `type JsonDict = dict[str, str | int | float | bool | None]`
- ✅ Bounds : `class Processor[T: BaseModel]:` (upper bound) ou utiliser `TypeVar('T', str, int)` pour contraintes

Exemples détaillés → `docs/references/fastapi.md`, `pydantic-v2.md`

---

## 3.2 Standards Imports

Cette section définit **OÙ** et **COMMENT** organiser les imports.

### Règle 1 : Imports au niveau module (WHERE)

**Principe** : Déclarer TOUS les imports en haut du fichier, jamais dans les fonctions/méthodes.

**✅ Correct** :
```python
# En haut du fichier
from datetime import datetime
from typing import TYPE_CHECKING

from app.models import SearchRequest, DateRange
from app.services import CrawlerService

if TYPE_CHECKING:
    from app.services import ProxyService


def process_search(request: SearchRequest) -> None:
    crawler = CrawlerService()
    timestamp = datetime.now()
```

**❌ Incorrect** :
```python
def process_search(request):
    from datetime import datetime  # Import dans fonction
    from app.services import CrawlerService  # Import dans fonction

    crawler = CrawlerService()
    timestamp = datetime.now()
```

### Exceptions autorisées

1. **Circular imports** (résolution de dépendances circulaires) :
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services import ProxyService  # Évite circular import


def configure_proxy(proxy: "ProxyService") -> None:
    pass
```

2. **Imports conditionnels runtime** (dépendances optionnelles) :
```python
def export_data(format: str) -> None:
    if format == "excel":
        import openpyxl  # Import seulement si format Excel demandé
        # ... logique export Excel
```

3. **Imports coûteux** (optimisation chargement initial) :
```python
def train_model() -> None:
    import tensorflow as tf  # Import lourd seulement si fonction appelée
    # ... logique ML
```

**Justification requise** : Toute exception doit avoir un commentaire expliquant POURQUOI.

---

### Règle 2 : Imports via `__init__.py` (HOW)

**Principe** : Toujours importer via les fichiers `__init__.py` des packages, jamais directement depuis les modules internes.

**✅ Correct** :
```python
# Imports via __init__.py (API publique)
from app.models import DateRange, SearchRequest, Flight
from app.services import CrawlerService, SearchService
from app.utils import build_google_flights_url
```

**❌ Incorrect** :
```python
# Imports directs (contourne l'API publique)
from app.models.request import DateRange, SearchRequest
from app.models.flight import Flight
from app.services.crawler_service import CrawlerService
from app.services.search_service import SearchService
from app.utils.url_builder import build_google_flights_url
```

### Avantages

- ✅ **Cohérence** : Un seul endroit définit l'API publique
- ✅ **Refactoring facile** : Renommer/déplacer fichiers sans casser imports
- ✅ **Lisibilité** : Imports concis et clairs
- ✅ **Encapsulation** : Cache détails implémentation interne

### Structure recommandée

```python
# app/models/__init__.py
"""Models package - Pydantic schemas."""

from app.models.request import DateRange, SearchRequest, Flight
from app.models.response import SearchResponse, FlightResult, SearchStats

__all__ = [
    "DateRange",
    "SearchRequest",
    "Flight",
    "SearchResponse",
    "FlightResult",
    "SearchStats",
]
```

**Note** : Fichiers `__init__.py` dans `tests/` restent vides (convention pytest).

---

## 3.3 Docstrings Pragmatiques (PEP 257)

**Règle : 1 ligne par défaut** (90% des cas) :
```python
def parse_price(html: str) -> float:
    """Extrait le prix depuis le HTML Google Flights."""
```

### Format complet si nécessaire

- ✅ Comportement non-évident (side-effects, mutations)
- ✅ Exceptions importantes levées
- ✅ Algorithmes complexes
- ✅ API publiques (routes FastAPI)

### Règles

- ✅ 1 ligne suffit si signature explicite
- ✅ Focus sur **POURQUOI**, pas **QUOI**
- ❌ Pas de verbosité (ne pas répéter ce que le type dit)

---

## 3.4 Patterns Async (crawl4ai, error handling)

### Règles projet

- ✅ TOUJOURS utiliser `async with` pour AsyncWebCrawler
- ✅ Retry logic avec tenacity (exponential backoff + jitter)
- ✅ Timeouts explicites : `httpx.AsyncClient(timeout=10)`
- ✅ Capturer exceptions spécifiques (pas `except Exception:`)
- ✅ Logger avant retry (`before_sleep` callback tenacity)

### Anti-patterns

- ❌ Bloquer event loop avec code sync dans routes async
- ❌ Retry sur 404 (erreur client, pas serveur)
- ❌ Pas de timeout → risque hang

Exemples complets → `docs/references/crawl4ai.md`, `tenacity.md`

---

## 3.5 Fichiers __init__.py

### Code applicatif (`app/`)

```python
# Exports explicites avec __all__
from app.main import app
__all__ = ["app"]
```
- ✅ Définir `__all__` (API publique du package)
- ✅ Facilite imports : `from app import app`

### Tests (`tests/`)

```python
# Vides (juste docstring)
"""Tests package."""
```
- ✅ Fichiers présents (marque package Python)
- ❌ Pas d'exports ni `__all__` (convention pytest)

---

# 4. 🔧 Tooling

## 4.1 Ruff - Linter & Formatter

### Configuration

**Source** : `pyproject.toml` → sections `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]`

**Règles clés** :
- Line length 88 (cohérence Black), Python 3.13 target
- Linters : pycodestyle (E), pyflakes (F), isort (I), pep8-naming (N), bugbear (B), simplify (SIM)
- Tests : assertions autorisées (`S101` ignored in `tests/**`)
- Format : double quotes, spaces (pas tabs)

### Commandes

```bash
ruff check . --fix && ruff format .    # Pre-commit standard
ruff check .                           # Lint uniquement
ruff format . --check                  # Check format sans modifier
```

### Workflow

- ✅ **Pre-commit** : `ruff check . --fix && ruff format .` (obligatoire)
- ✅ **CI bloque** si ruff échoue
- ✅ Imports triés automatiquement (isort intégré)

---

## 4.2 Mypy - Type Checking Strict

### Configuration

**Source** : `pyproject.toml` → section `[tool.mypy]` + overrides

**Règles clés** :
- `strict = true` sur `app/` (tous flags strictness activés)
- Relax sur `tests/` (`disallow_untyped_defs = false`)
- Ignore libs sans stubs : `crawl4ai.*`

**Commande** :
```bash
mypy app/    # Type check strict
```

### Workflow

- ✅ **Strict mode OBLIGATOIRE** sur `app/` (10 flags activés automatiquement)
- ✅ **CI bloque** si mypy échoue
- ✅ **Aucun `# type: ignore`** sans justification commentée

---

## 4.3 Structured Logging (JSON, contexte)

### Règles projet

- ✅ Format JSON structuré avec `pythonjsonlogger`
- ✅ TOUJOURS ajouter `extra={}` avec contexte métier (search_id, destinations, proxy_used, etc.)
- ✅ Niveaux : DEBUG (dev), INFO (prod), WARNING (retry), ERROR (fail)
- ✅ Logger : captcha detection, proxy rotation, parsing errors, Top 10 résultats
- ✅ Pas de secrets dans logs (masquer API keys, passwords)

Configuration complète → `app/core/logger.py`

---

# 5. 🚫 Anti-Patterns

## 5.1 Commentaires Inline Interdits

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
- ✅ Justification imports exceptionnels (circular, conditional)

**Conséquence** : PR rejetée si commentaires inline non justifiés

---

# 6. 🧪 Tests

## 6.1 Stratégie Tests & TDD

### Approche TDD (Test-Driven Development)

**Cycle Red-Green-Refactor** :
1. **Red** : Écrire test qui échoue
2. **Green** : Implémenter code minimal pour faire passer le test
3. **Refactor** : Améliorer code sans casser les tests

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

**Règles TDD strictes** :
- ✅ Tests unitaires AVANT implémentation (red → green → refactor)
- ✅ Tests intégration APRÈS tous tests unitaires de la story
- ✅ Commit seulement si TOUS les tests passent (unitaires + intégration)
- ❌ Ne JAMAIS commencer intégration si tests unitaires échouent
- ❌ Ne JAMAIS skipper tests (coverage minimum 80%)

---

### Workflow TDD par Story

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

**Quand faire tests intégration** :
- Après tous les tests unitaires de la story
- Avant le commit final
- Si story inclut API route → TestClient FastAPI obligatoire

---

### Formats Recommandés

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

---

### Exemple Story Complète

**Story 3 (Search endpoint mock)** :

**Phase 1 - TDD Composants** :
1. Models (21 tests) → Implémentation → Tests passent ✅
2. SearchService mock (5 tests) → Implémentation → Tests passent ✅
3. Route POST /search (8 tests) → Implémentation → Tests passent ✅

**Phase 2 - Tests Intégration** :
1. End-to-end API (4 tests) → Tests passent ✅

**Phase 3 - Validation** :
1. Test manuel `curl -X POST http://localhost:8000/api/v1/search-flights`
2. Vérifier response JSON valide
3. Commit : `feat(api): add search endpoint with mock data`

**Total Story 3** : 38 tests (34 unitaires + 4 intégration), coverage ≥ 80%

---

## 6.2 Types de Tests

### 1. Tests Unitaires (`tests/unit/`)

**Caractéristiques** :
- Testent 1 fonction/classe isolée
- Utilisent mocks pour dépendances externes
- Rapides (<1s pour 100 tests)
- Coverage minimum 80%

**Exemple Mocking** :
```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(html="<html>Mock</html>", success=True)
    return crawler
```

**Exemple Test** :
```python
def test_search_request_validation():
    request = SearchRequest(destinations=["Paris", "Tokyo"], date_range=DateRange(...))
    assert len(request.destinations) == 2

@pytest.mark.asyncio
async def test_crawl_with_captcha(mock_crawler):
    service = CrawlerService(crawler=mock_crawler)
    with pytest.raises(CaptchaDetectedError):
        await service.crawl_google_flights("https://example.com")
```

---

### 2. Tests Intégration (`tests/integration/`)

**Caractéristiques** :
- Testent interactions entre composants
- Utilisent TestClient FastAPI
- Pas de mocks pour services internes
- Mocks uniquement pour Crawl4AI/Decodo (dépendances externes)

**Exemple Test** :
```python
def test_search_flights_endpoint(client: TestClient, mock_crawler):
    response = client.post("/api/v1/search-flights", json={...})
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 10
```

---

### 3. Tests End-to-End (manuels, pas de CI)

**Caractéristiques** :
- Testent flow complet avec vraies dépendances
- Utilisent vraie clé proxy provider (bandwidth coûteux)
- Exécutés manuellement avant release
- Pas dans CI (coût + lenteur)

**Exemple** : Lancer l'app avec vraies clés proxy dans `.env`, puis tester manuellement via `curl` et vérifier logs (captcha detection, proxy rotation, parsing success).

---

## 6.3 Fixtures & Factories

### Organisation (`tests/fixtures/`)

```
tests/fixtures/
├── __init__.py     # Vide (marker package)
├── factories.py    # Factories objets Pydantic
├── mocks.py        # Mocks services/composants
└── helpers.py      # Constantes + helpers dates
```

**Règles strictes** :
- ✅ **DRY** : 0 duplication (1 constante/factory pour 1 concept)
- ✅ **Factory pattern** : Paramètres flexibles (`as_dict`, `num_flights`, `past`)
- ✅ **Constantes** : `TEMPLATE_URL` dans `helpers.py` (single source of truth)
- ✅ **Délégation** : Fixtures wrapper délèguent aux factories
- ❌ **Pas de hardcoded** : Jamais de valeurs en dur répétées

---

**Exemple Factory** :
```python
@pytest.fixture
def date_range_factory():
    def _create(start_offset=1, duration=6, as_dict=False):
        start, end = get_date_range(start_offset, duration)
        return {"start": start.isoformat(), "end": end.isoformat()} if as_dict else DateRange(...)
    return _create
```

---

### Chargement

**`tests/conftest.py`** :
```python
pytest_plugins = [
    "tests.fixtures.factories",
    "tests.fixtures.mocks",
    "tests.fixtures.helpers",
]
```

**Nommage** :
- Factories → `*_factory` (retourne callable)
- Mocks → `mock_*` (retourne objet mocké)
- Helpers → `get_*`, `assert_*` (fonctions utilitaires)
- Constantes → `UPPER_CASE`

---

**Exemple Fixtures** (`tests/conftest.py`) :
```python
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(html="<html>Mock</html>", success=True)
    return crawler
```

---

## 6.4 Configuration & Commandes

### Configuration & Commandes

**Config** : `pyproject.toml` → section `[tool.pytest.ini_options]`
- Testpaths : `tests/`, pattern `test_*.py`
- Markers : `slow`, `integration`
- Async mode : auto (`@pytest.mark.asyncio`)
- Options : `-v`, `--strict-markers`, `--cov=app`

**Commandes Essentielles** :
```bash
pytest tests/unit/ -v                  # Tests unitaires
pytest --cov=app --cov-report=html     # Coverage interactif
pytest -x                              # Stop au 1er échec
pytest -k "pattern"                    # Filtre par nom
```

**Patterns** : AAA (Arrange/Act/Assert), `@pytest.mark.asyncio`, `pytest.raises(Error)`

**CI** : Tests unitaires + coverage 80% minimum (bloque merge si échec)

---

# 7. 🔄 Workflow Développement

## 7.1 Installation & Setup

### Prérequis

- Python 3.13.1+
- [uv](https://github.com/astral-sh/uv) (package manager moderne)
- Docker (optionnel, pour build image)

---

### Installation Dépendances

```bash
# Installation projet + deps dev
uv sync --all-extras

# Post-install : Setup Playwright (automatique via crawl4ai-setup)
uv run crawl4ai-setup
```

**Note** : `crawl4ai-setup` installe automatiquement Playwright et ses dépendances système. Pas besoin d'installation manuelle de Playwright.

---

### Alternative Exécution Commandes

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

**Note** : Dans la suite de ce document, les commandes sont écrites sans `uv run` pour concision. Si votre venv n'est pas activé, préfixez toutes les commandes avec `uv run`.

---

## 7.2 Commandes Quotidiennes

### Lancer l'Application

```bash
# Mode développement (hot-reload)
fastapi dev app/main.py

# Mode production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### Quality Checks

**Voir section [Git > Pre-commit Checks](#83-pre-commit-checks) pour détails complets.**

```bash
# All-in-one pre-commit
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

---

### Tests

**Voir section [Tests > Configuration & Commandes](#64-configuration--commandes) pour liste complète.**

```bash
# Tests unitaires (quotidien)
pytest tests/unit/ -v

# Coverage
pytest --cov=app --cov-report=html
```

---

### Docker

```bash
# Build image
docker build -t flight-search-api .

# Run container
docker run -p 8001:8000 --env-file .env flight-search-api

# Run avec override env vars
docker run -p 8001:8000 -e LOG_LEVEL=DEBUG -e PROXY_USERNAME=customer-XXX-country-FR flight-search-api
```

---

## 7.3 Feature Development avec TDD

Ce workflow combine développement feature + approche TDD (voir section [Tests > Stratégie TDD](#61-stratégie-tests--tdd)).

### Étape 1 : Créer Branche Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nom-descriptif
```

---

### Étape 2 : Développer avec TDD

**Cycle Red-Green-Refactor pour chaque composant** (voir [Tests > Workflow TDD](#61-stratégie-tests--tdd) pour détails) :

```bash
# 1. RED : Écrire tests → doivent échouer
pytest tests/unit/test_nouveau_service.py -v

# 2. GREEN : Implémenter feature minimale → tests passent
pytest tests/unit/test_nouveau_service.py -v

# 3. REFACTOR : Améliorer code → tests passent toujours
```

**Répéter pour tous les composants de la story.**

---

### Étape 3 : Tests Intégration

Après tous les tests unitaires passés :

```bash
# Écrire tests intégration (si API route)
vim tests/integration/test_nouvelle_route.py

# Run tests intégration
pytest tests/integration/test_nouvelle_route.py -v
```

---

### Étape 4 : Vérifications Complètes

```bash
# Quality checks complets (voir section Git > Pre-commit Checks)
ruff check . --fix && ruff format . && mypy app/ && pytest -v

# Si tout passe → Commit
git add .
git commit -m "feat(services): add nouveau service"
```

---

### Étape 5 : Push + Pull Request

```bash
# Push branche
git push -u origin feature/nom-descriptif

# Créer PR sur GitHub : feature/nom-descriptif → develop
# CI s'exécute automatiquement (lint, format, typecheck, tests)
# Merger après validation CI
```

---

### Étape 6 : Cleanup Après Merge

```bash
git checkout develop
git pull origin develop
git branch -d feature/nom-descriptif
```

---

## 7.4 Debugging & Troubleshooting

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

# Proxy Provider
PROXY_USERNAME=customer-{api_key}-country-FR
PROXY_PASSWORD=your_password
PROXY_HOST=pr.decodo.com:8080

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

---

### Debugging

**Logs structurés** : Utiliser `logger.info("msg", extra={...})` pour contexte JSON. Activer DEBUG : `LOG_LEVEL=DEBUG fastapi dev app/main.py`

**Breakpoints** : `import debugpy; debugpy.listen(5678); debugpy.wait_for_client()`

---

### Troubleshooting Commun

**Erreur `crawl4ai-setup` échoue** :
- Vérifier connexion internet (télécharge Playwright browsers)
- Espace disque suffisant (~500MB)
- Permissions écriture dans cache directory

**Solutions rapides** :
- `ModuleNotFoundError` → `uv sync --all-extras`
- Mypy erreurs lib externe → Ajouter `ignore_missing_imports = true` dans `pyproject.toml`
- Docker build lent → Utiliser `--cache-from`

---

# 8. 📦 Git

## 8.1 Stratégie de Branches

**Modèle GitFlow simplifié** :

```
master (production)
  ↑
develop (intégration)
  ↑
feature/* (développement)
```

### Branches Principales

**`master`** : Code en production, stable, uniquement via merge de `develop`
- Protégée : pas de push direct
- Chaque merge = nouvelle version taggée (v1.0.0, v1.1.0, etc.)

**`develop`** : Branche d'intégration, prête pour release
- Merge depuis branches `feature/*` via Pull Requests
- Tests CI doivent passer avant merge
- Base pour créer nouvelles features

---

### Branches de Travail

**`feature/*`** : Développement de fonctionnalités
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

---

### Workflow Release

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

## 8.2 Conventional Commits

**Format obligatoire** :

```
<type>(<scope>): <description>

[body optionnel]

[footer optionnel]
```

**Types** : `feat` (MINOR), `fix` (PATCH), `docs`, `refactor`, `test`, `chore`, `ci`, `perf`

**Exemples** :
- `feat(api): add multi-city search endpoint`
- `fix(parser): handle missing price field`
- `refactor(crawler): extract proxy config`

---

### Règles Projet

✅ **Description impérative** : "add feature" (pas "added" ou "adds")
✅ **Minuscules** : `feat(api):` (pas `Feat(API):`)
✅ **Scope optionnel** : Composant affecté (api, parser, crawler, docs)
✅ **Max 72 caractères** pour la première ligne
✅ **Breaking changes** : Ajouter `!` après type/scope + footer `BREAKING CHANGE:`

---

**Anti-patterns** : ❌ Pas de type, majuscule, past tense, trop vague/long (>72 char)

---

## 8.3 Pre-commit Checks

### Exécution Avant Chaque Commit

```bash
# Exécuter manuellement (recommandé pendant dev)
ruff check . && ruff format . && mypy app/ && pytest tests/unit/

# Si succès → commit autorisé
# Si échec → corriger avant commit
```

---

### Checks Obligatoires

**1. Ruff Lint** : `ruff check .`
- Vérifie erreurs code (pycodestyle, pyflakes, naming, etc.)
- Auto-fix disponible : `ruff check . --fix`
- Doit passer sans erreur (warnings tolérés selon config)

**2. Ruff Format** : `ruff format .`
- Formate code selon standards (line length 88, quotes doubles)
- Auto-applique formatage (pas juste check)
- Doit passer sans changement après formatage

**3. Mypy Type Check** : `mypy app/`
- Vérifie cohérence types (strict mode)
- Détecte erreurs potentielles à runtime
- Doit passer sans erreur (0 issues)

**4. Tests Unitaires** : `pytest tests/unit/`
- Exécute tests rapides (pas d'intégration)
- Coverage minimum 80% (Phase 3+)
- Doit passer 100% des tests

---

### Workflow Local

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

---

### Automation (Phase 3.6+)

- **CI GitHub Actions** : Exécute automatiquement sur PR
- **Bloque merge** si checks échouent
- **Pas de pre-commit hook local** (éviter friction dev)
- **Responsabilité développeur** : Exécuter avant push

---

**Règles** : Exécuter checks avant commit, jamais commit si échec, utiliser `--fix`, CI bloque PR si échec

---

## 8.4 Workflow Pull Request

**Processus** : Push → Créer PR (format Conventional Commit) → CI passe → Squash merge → Supprimer branche

**Règles** : 1 PR = 1 feature, CI doit passer, squash merge, pas de commit direct sur develop/master

---

# 9. 🐳 Docker

**Dockerfile** : Disponible dans `/Dockerfile` (multi-stage, non-root user, healthcheck)

### Commandes Essentielles

```bash
# Build
docker build -t flight-search-api .

# Run avec .env
docker run -p 8001:8000 --env-file .env flight-search-api

# Run en background
docker run -d -p 8001:8000 --name flight-api flight-search-api

# Logs
docker logs -f flight-api

# Stop & Remove
docker stop flight-api && docker rm flight-api
```

---

### Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

### Best Practices

- ✅ Multi-stage builds (réduction taille ~60%)
- ✅ Non-root user (sécurité)
- ✅ Healthcheck natif
- ✅ `.dockerignore` (exclure .git, tests)
- ❌ Jamais hardcoder secrets dans Dockerfile

**Documentation complète** : `docs/references/dokploy.md` (Dockerfile détaillé, troubleshooting, déploiement Dokploy, optimisations avancées)
