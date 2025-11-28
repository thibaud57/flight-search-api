# Coding Standards — flight-search-api

**Version** : 1.0
**Dernière mise à jour** : 2025-01-28

> **Note** : Ce document contient les standards détaillés du projet. Pour une référence rapide, voir `.claude/CLAUDE.md`.

---

## Table des Matières

1. [Standards Python](#1-standards-python)
   - [1.1 Type Hints (PEP 695)](#11-type-hints-pep-695)
   - [1.2 Imports](#12-imports)
   - [1.3 Docstrings (PEP 257)](#13-docstrings-pep-257)
   - [1.4 Patterns Async](#14-patterns-async)
   - [1.5 Fichiers __init__.py](#15-fichiers-__init__py)
2. [Tooling](#2-tooling)
   - [2.1 Ruff - Linter & Formatter](#21-ruff---linter--formatter)
   - [2.2 Mypy - Type Checking Strict](#22-mypy---type-checking-strict)
   - [2.3 Structured Logging](#23-structured-logging)
3. [Anti-Patterns](#3-anti-patterns)
4. [Tests](#4-tests)
   - [4.1 Stratégie TDD Complète](#41-stratégie-tdd-complète)
   - [4.2 Types de Tests](#42-types-de-tests)
   - [4.3 Fixtures & Factories](#43-fixtures--factories)
   - [4.4 Configuration Pytest](#44-configuration-pytest)
5. [Git & Workflow](#5-git--workflow)
   - [5.1 Stratégie Branches](#51-stratégie-branches)
   - [5.2 Conventional Commits](#52-conventional-commits)
   - [5.3 Pre-commit Checks](#53-pre-commit-checks)
6. [Docker](#6-docker)

---

## 1. Standards Python

### 1.1 Type Hints (PEP 695)

#### Règles Obligatoires

- ✅ Utiliser PEP 695 partout : `class Response[T]:`, `def process[T](items: list[T]) -> T:`
- ✅ Annoter TOUTES les signatures (args + return)
- ✅ Utiliser `list[T]`, `dict[K, V]` (pas `List[T]`, `Dict[K, V]`)
- ✅ Préférer `X | None` à `Optional[X]`
- ✅ Ajouter `model_config = ConfigDict(extra="forbid")` sur tous les models Pydantic
- ✅ Type alias : `type JsonDict = dict[str, str | int | float | bool | None]`
- ✅ Bounds : `class Processor[T: BaseModel]:` (upper bound) ou `TypeVar('T', str, int)` pour contraintes

#### Exemples

**Génériques PEP 695** :
```python
# ✅ Correct (PEP 695)
class Response[T]:
    data: T
    status: int

def process[T](items: list[T]) -> T:
    return items[0]

# ❌ Incorrect (ancienne syntaxe)
from typing import Generic, TypeVar

T = TypeVar('T')

class Response(Generic[T]):
    data: T
    status: int
```

**Union types** :
```python
# ✅ Correct
def get_user(id: int | str) -> User | None:
    pass

# ❌ Incorrect
from typing import Optional, Union

def get_user(id: Union[int, str]) -> Optional[User]:
    pass
```

**Pydantic ConfigDict** :
```python
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    destinations: list[str]
    date_range: DateRange

    model_config = ConfigDict(extra="forbid")  # Rejette champs inconnus
```

**Références** : `docs/references/fastapi.md`, `pydantic-v2.md`

---

### 1.2 Imports

#### Règle 1 : Imports au Niveau Module (WHERE)

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

#### Exceptions Autorisées

**1. Circular imports** (résolution de dépendances circulaires) :
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services import ProxyService  # Évite circular import


def configure_proxy(proxy: "ProxyService") -> None:
    pass
```

**2. Imports conditionnels runtime** (dépendances optionnelles) :
```python
def export_data(format: str) -> None:
    if format == "excel":
        import openpyxl  # Import seulement si format Excel demandé
        # ... logique export Excel
```

**3. Imports coûteux** (optimisation chargement initial) :
```python
def train_model() -> None:
    import tensorflow as tf  # Import lourd seulement si fonction appelée
    # ... logique ML
```

**Justification requise** : Toute exception doit avoir un commentaire expliquant POURQUOI.

---

#### Règle 2 : Imports via `__init__.py` (HOW)

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

#### Avantages

- ✅ **Cohérence** : Un seul endroit définit l'API publique
- ✅ **Refactoring facile** : Renommer/déplacer fichiers sans casser imports
- ✅ **Lisibilité** : Imports concis et clairs
- ✅ **Encapsulation** : Cache détails implémentation interne

#### Structure Recommandée

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

### 1.3 Docstrings (PEP 257)

**Règle : 1 ligne par défaut** (90% des cas) :
```python
def parse_price(html: str) -> float:
    """Extrait le prix depuis le HTML Google Flights."""
```

#### Format Complet Si Nécessaire

- ✅ Comportement non-évident (side-effects, mutations)
- ✅ Exceptions importantes levées
- ✅ Algorithmes complexes
- ✅ API publiques (routes FastAPI)

#### Règles

- ✅ 1 ligne suffit si signature explicite
- ✅ Focus sur **POURQUOI**, pas **QUOI**
- ❌ Pas de verbosité (ne pas répéter ce que le type dit)

**Exemple** :
```python
# ❌ Verbeux (répète le type)
def calculate_total(prices: list[float]) -> float:
    """
    Calculates the total of a list of prices.

    Args:
        prices: A list of float prices

    Returns:
        The sum of all prices as a float
    """
    return sum(prices)

# ✅ Concis (focus sur WHY)
def calculate_total(prices: list[float]) -> float:
    """Calcule le total pour affichage facture client."""
    return sum(prices)
```

---

### 1.4 Patterns Async

#### Règles Projet

- ✅ TOUJOURS utiliser `async with` pour AsyncWebCrawler
- ✅ Retry logic avec tenacity (exponential backoff + jitter)
- ✅ Timeouts explicites : `httpx.AsyncClient(timeout=10)`
- ✅ Capturer exceptions spécifiques (pas `except Exception:`)
- ✅ Logger avant retry (`before_sleep` callback tenacity)

#### Exemple Complet

```python
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from crawl4ai import AsyncWebCrawler
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def crawl_google_flights(url: str) -> str:
    """Crawl Google Flights URL avec retry automatique."""
    async with AsyncWebCrawler(timeout=10) as crawler:  # ALWAYS timeout explicite
        result = await crawler.arun(url=url)
        if not result.success:
            raise Exception(f"Crawl failed: {result.error_type}")
        return result.html
```

#### Anti-Patterns

- ❌ Bloquer event loop avec code sync dans routes async
- ❌ Retry sur 404 (erreur client, pas serveur)
- ❌ Pas de timeout → risque hang

**Références** : `docs/references/crawl4ai.md`, `tenacity.md`

---

### 1.5 Fichiers __init__.py

#### Code Applicatif (`app/`)

```python
# Exports explicites avec __all__
from app.main import app
__all__ = ["app"]
```
- ✅ Définir `__all__` (API publique du package)
- ✅ Facilite imports : `from app import app`

#### Tests (`tests/`)

```python
# Vides (juste docstring)
"""Tests package."""
```
- ✅ Fichiers présents (marque package Python)
- ❌ Pas d'exports ni `__all__` (convention pytest)

---

## 2. Tooling

### 2.1 Ruff - Linter & Formatter

#### Configuration

**Source** : `pyproject.toml` → sections `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]`

**Règles clés** :
- Line length 88 (cohérence Black), Python 3.13 target
- Linters : pycodestyle (E), pyflakes (F), isort (I), pep8-naming (N), bugbear (B), simplify (SIM)
- Tests : assertions autorisées (`S101` ignored in `tests/**`)
- Format : double quotes, spaces (pas tabs)

**Configuration complète** :
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

#### Commandes

```bash
ruff check .              # Lint
ruff check . --fix        # Auto-fix
ruff format .             # Format
ruff format . --check     # Check sans modifier
```

#### Workflow

- ✅ **Pre-commit** : `ruff check . --fix && ruff format .` (obligatoire)
- ✅ **CI bloque** si ruff échoue
- ✅ Imports triés automatiquement (isort intégré)

---

### 2.2 Mypy - Type Checking Strict

#### Configuration

**Source** : `pyproject.toml` → section `[tool.mypy]` + overrides

**Règles clés** :
- `strict = true` sur `app/` (tous flags strictness activés)
- Relax sur `tests/` (`disallow_untyped_defs = false`)
- Ignore libs sans stubs : `crawl4ai.*`

**Configuration complète** :
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

#### Commande

```bash
mypy app/    # Type check strict
```

#### Workflow

- ✅ **Strict mode OBLIGATOIRE** sur `app/` (10 flags activés automatiquement)
- ✅ **CI bloque** si mypy échoue
- ✅ **Aucun `# type: ignore`** sans justification commentée

---

### 2.3 Structured Logging

#### Règles Projet

- ✅ Format JSON structuré avec `pythonjsonlogger`
- ✅ TOUJOURS ajouter `extra={}` avec contexte métier (search_id, destinations, proxy_used, etc.)
- ✅ Niveaux : DEBUG (dev), INFO (prod), WARNING (retry), ERROR (fail)
- ✅ Logger : captcha detection, proxy rotation, parsing errors, Top 10 résultats
- ✅ Pas de secrets dans logs (masquer API keys, passwords)

#### Exemple

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Correct : contexte structuré
logger.info(
    "Search completed successfully",
    extra={
        "search_id": "abc123",
        "destinations": ["Paris", "Tokyo"],
        "results_count": 10,
        "proxy_used": "pr.decodo.com",
        "duration_ms": 1234,
    }
)

# ❌ Incorrect : pas de contexte
logger.info("Search completed")
```

**Configuration complète** → `app/core/logger.py`

---

## 3. Anti-Patterns

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
- ✅ Justification imports exceptionnels (circular, conditional)

**Conséquence** : PR rejetée si commentaires inline non justifiés

---

## 4. Tests

### 4.1 Stratégie TDD Complète

#### Approche TDD (Test-Driven Development)

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

#### Workflow TDD par Story

Pour chaque story (Phase 5) :

**PHASE 1: TDD Tests Unitaires**
Pour chaque composant:
1. Écrire tests composant (red)
2. Implémenter composant (green)
3. Tests passent ✅
4. Refactor (si nécessaire)

Répéter pour tous composants story

**PHASE 2: Tests Intégration**
5. Écrire tests end-to-end (TestClient si API route)
6. Tests intégration passent ✅

**PHASE 3: Validation Manuelle**
7. Test manuel (curl/Postman)
8. Valider UX réelle
9. Commit si OK

**Quand faire tests intégration** :
- Après tous les tests unitaires de la story
- Avant le commit final
- Si story inclut API route → TestClient FastAPI obligatoire

#### Formats Recommandés

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

#### Exemple Story Complète

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

### 4.2 Types de Tests

#### 1. Tests Unitaires (`tests/unit/`)

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

#### 2. Tests Intégration (`tests/integration/`)

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

#### 3. Tests End-to-End (manuels, pas de CI)

**Caractéristiques** :
- Testent flow complet avec vraies dépendances
- Utilisent vraie clé proxy provider (bandwidth coûteux)
- Exécutés manuellement avant release
- Pas dans CI (coût + lenteur)

**Exemple** : Lancer l'app avec vraies clés proxy dans `.env`, puis tester manuellement via `curl` et vérifier logs (captcha detection, proxy rotation, parsing success).

---

### 4.3 Fixtures & Factories

#### Organisation (`tests/fixtures/`)

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

**Exemple Factory** :
```python
@pytest.fixture
def date_range_factory():
    def _create(start_offset=1, duration=6, as_dict=False):
        start, end = get_date_range(start_offset, duration)
        return {"start": start.isoformat(), "end": end.isoformat()} if as_dict else DateRange(...)
    return _create
```

#### Chargement

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

### 4.4 Configuration Pytest

**Source** : `pyproject.toml` → section `[tool.pytest.ini_options]`

**Configuration Complète** :
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

**Commandes Essentielles** :
```bash
pytest tests/unit/ -v                  # Tests unitaires
pytest tests/integration/ -v           # Tests intégration
pytest --cov=app --cov-report=html     # Coverage interactif
pytest -x                              # Stop au 1er échec
pytest -k "pattern"                    # Filtre par nom
pytest -n auto                         # Parallèle (speedup 4x)
```

**Patterns** : AAA (Arrange/Act/Assert), `@pytest.mark.asyncio`, `pytest.raises(Error)`

**CI** : Tests unitaires + coverage 80% minimum (bloque merge si échec)

---

## 5. Git & Workflow

### 5.1 Stratégie Branches

**Modèle GitFlow simplifié** :

```
master (production)
  ↑
develop (intégration)
  ↑
feature/* (développement)
```

#### Branches Principales

**`master`** : Code en production, stable, uniquement via merge de `develop`
- Protégée : pas de push direct
- Chaque merge = nouvelle version taggée (v1.0.0, v1.1.0, etc.)

**`develop`** : Branche d'intégration, prête pour release
- Merge depuis branches `feature/*` via Pull Requests
- Tests CI doivent passer avant merge
- Base pour créer nouvelles features

#### Branches de Travail

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

#### Workflow Release

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

### 5.2 Conventional Commits

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

#### Règles Projet

✅ **Description impérative** : "add feature" (pas "added" ou "adds")
✅ **Minuscules** : `feat(api):` (pas `Feat(API):`)
✅ **Scope optionnel** : Composant affecté (api, parser, crawler, docs)
✅ **Max 72 caractères** pour la première ligne
✅ **Breaking changes** : Ajouter `!` après type/scope + footer `BREAKING CHANGE:`

**Anti-patterns** : ❌ Pas de type, majuscule, past tense, trop vague/long (>72 char)

---

### 5.3 Pre-commit Checks

#### Commande Obligatoire

```bash
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

**Si succès** → Commit autorisé
**Si échec** → Corriger avant commit

#### Détails Checks

1. **Ruff Lint** : `ruff check .`
   - Vérifie erreurs code (pycodestyle, pyflakes, naming, etc.)
   - Auto-fix disponible : `ruff check . --fix`
   - Doit passer sans erreur

2. **Ruff Format** : `ruff format .`
   - Formate code selon standards (line length 88, quotes doubles)
   - Auto-applique formatage
   - Doit passer sans changement après formatage

3. **Mypy Type Check** : `mypy app/`
   - Vérifie cohérence types (strict mode)
   - Détecte erreurs potentielles à runtime
   - Doit passer sans erreur (0 issues)

4. **Tests Unitaires** : `pytest tests/unit/`
   - Exécute tests rapides (pas d'intégration)
   - Coverage minimum 80% (Phase 3+)
   - Doit passer 100% des tests

#### CI/CD

- ✅ CI GitHub Actions exécute automatiquement sur PR
- ✅ **Bloque merge** si checks échouent
- ❌ Pas de pre-commit hook local (éviter friction)

**Règles** : Exécuter checks avant commit, jamais commit si échec, CI bloque PR si échec

---

## 6. Docker

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

### Docker Compose

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Best Practices

- ✅ Multi-stage builds (réduction taille ~60%)
- ✅ Non-root user (sécurité)
- ✅ Healthcheck natif
- ✅ `.dockerignore` (exclure .git, tests)
- ❌ Jamais hardcoder secrets dans Dockerfile

**Documentation complète** : `docs/references/dokploy.md` (Dockerfile détaillé, troubleshooting, déploiement Dokploy, optimisations avancées)
