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

**Séparation** : `api/` (HTTP), `core/` (config), `models/` (Pydantic), `services/` (métier), `utils/` (helpers)

**Documentation** : `docs/references/` modulaire (10 fichiers) → Économie tokens ~44%

**Tests miroir** : `tests/` reflète `app/` (`unit/` mocks, `integration/` TestClient)

**Config centralisée** : `pyproject.toml` (deps + tools), `.env.example` (template), `.github/workflows/` (CI/CD)

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

### Règle 1 : Imports au niveau module (WHERE)

**Principe** : Déclarer TOUS les imports en haut du fichier, jamais dans les fonctions.

**Exceptions** (avec commentaire POURQUOI obligatoire) :
- Circular imports → `TYPE_CHECKING`
- Dépendances optionnelles (ex: `import openpyxl` si format Excel)
- Imports coûteux (ex: `import tensorflow` uniquement dans fonction ML)

---

### Règle 2 : Imports via `__init__.py` (HOW)

**Principe** : Toujours importer via `__init__.py` des packages, jamais modules internes.

```python
# ✅ Correct
from app.models import DateRange, SearchRequest, Flight
from app.services import CrawlerService, SearchService

# ❌ Incorrect
from app.models.request import DateRange
from app.services.crawler_service import CrawlerService
```

**Avantages** : Cohérence, refactoring facile, encapsulation

**Structure `__init__.py`** :
```python
from app.models.request import DateRange, SearchRequest
__all__ = ["DateRange", "SearchRequest"]
```

**Note** : `__init__.py` dans `tests/` restent vides (convention pytest).

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

**Règle** : ❌ AUCUN commentaire inline (code self-explanatory : noms explicites, types, docstrings)

**Exceptions** : User demande, TODO/FIXME temporaires, type hints complexes, justification imports

**Conséquence** : PR rejetée si commentaires non justifiés

---

# 6. 🧪 Tests

## 6.1 Stratégie Tests & TDD

### Cycle TDD (Test-Driven Development)

1. **Red** : Écrire test qui échoue
2. **Green** : Implémenter code minimal pour faire passer
3. **Refactor** : Améliorer sans casser tests

**Règles strictes** :
- ✅ Tests unitaires AVANT implémentation
- ✅ Tests intégration APRÈS tous tests unitaires story
- ✅ Commit si TOUS tests passent (coverage ≥ 80%)
- ❌ JAMAIS skipper tests ou commencer intégration si unitaires échouent

---

### Workflow Story (3 Phases)

**Phase 1 - TDD Composants** : Pour chaque composant → Tests (red) → Code (green) → Refactor → Répéter

**Phase 2 - Intégration** : Tests end-to-end (TestClient si API route)

**Phase 3 - Validation** : Test manuel curl/Postman → Commit

**Pyramide** : 60% Unit / 30% Integration / 10% E2E

---

### Formats Tests

**AAA (Arrange/Act/Assert)** - Unitaires
**Given/When/Then (BDD)** - Intégration

---

## 6.2 Types de Tests

### 1. Tests Unitaires (`tests/unit/`)
- Testent 1 fonction/classe isolée, mocks dépendances externes
- Rapides (<1s pour 100 tests), coverage ≥ 80%
- Patterns : `AsyncMock`, `pytest.raises(Error)`, `@pytest.mark.asyncio`

### 2. Tests Intégration (`tests/integration/`)
- Testent interactions composants, TestClient FastAPI
- Mocks uniquement Crawl4AI/Decodo (externes), pas services internes

### 3. Tests E2E (manuels, hors CI)
- Flow complet avec vraies dépendances (proxy provider)
- Manuels avant release (coût bandwidth)

---

## 6.3 Fixtures & Factories

**Organisation** : `tests/fixtures/` → `factories.py` (Pydantic objects), `mocks.py` (services), `helpers.py` (constantes)

**Règles DRY** :
- ✅ 1 constante/factory par concept (ex: `TEMPLATE_URL`)
- ✅ Factory pattern flexible (`as_dict`, `num_flights`, `past`)
- ❌ Jamais valeurs hardcodées répétées

**Nommage** : `*_factory` (callable), `mock_*` (objet), `get_*`/`assert_*` (helpers), `UPPER_CASE` (constantes)

**Chargement** : `tests/conftest.py` → `pytest_plugins = ["tests.fixtures.factories", ...]`

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

**Prérequis** : Python 3.13.1+, [uv](https://github.com/astral-sh/uv), Docker (optionnel)

**Installation** :
```bash
uv sync --all-extras          # Deps + dev
uv run crawl4ai-setup         # Playwright auto
```

**Exécution commandes** :
- **Venv activé** : `ruff check .`, `mypy app/`, `pytest tests/`
- **Sans venv** : `uv run ruff check .`, `uv run mypy app/`

**Note** : Commandes ci-après sans `uv run` (préfixer si venv non activé)

---

## 7.2 Commandes Quotidiennes

### Développement
```bash
fastapi dev app/main.py    # Hot-reload
```

### Quality & Tests
```bash
# Pre-commit complet (voir sections 4.1, 4.2, 6.4)
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

**Détails** : [4.1 Ruff](#41-ruff), [4.2 Mypy](#42-mypy), [6.4 Tests](#64-configuration--commandes)

### Docker
```bash
# Commandes complètes : voir section 9. Docker
docker build -t flight-search-api . && docker run -p 8001:8000 --env-file .env flight-search-api
```

---

## 7.3 Feature Development avec TDD

**Workflow** (voir détails [6.1 TDD](#61-stratégie-tests--tdd)) :

1. **Branche** : `git checkout develop && git pull && git checkout -b feature/nom`
2. **TDD** : `pytest tests/unit/test_service.py -v` → RED → GREEN → REFACTOR (répéter)
3. **Intégration** : `pytest tests/integration/test_route.py -v`
4. **Quality** : `ruff check . --fix && ruff format . && mypy app/ && pytest -v`
5. **Commit** : `git add . && git commit -m "feat(scope): description"`
6. **PR** : `git push -u origin feature/nom` → Créer PR → CI passe → Merge
7. **Cleanup** : `git checkout develop && git pull && git branch -d feature/nom`

---

## 7.4 Debugging & Troubleshooting

**Variables `.env`** : `cp .env.example .env` → Configurer `LOG_LEVEL`, `PROXY_*`, `CAPTCHA_*`

**⚠️ Sécurité** : JAMAIS committer `.env` (secrets → Dokploy UI prod)

**Debugging** :
- Logs : `logger.info("msg", extra={...})` + `LOG_LEVEL=DEBUG`
- Breakpoints : `import debugpy; debugpy.listen(5678)`

**Troubleshooting** :
- `ModuleNotFoundError` → `uv sync --all-extras`
- `crawl4ai-setup` échoue → Connexion internet + espace disque ~500MB
- Mypy lib externe → `ignore_missing_imports = true` dans `pyproject.toml`

---

# 8. 📦 Git

## 8.1 Stratégie de Branches

**GitFlow simplifié** : `master` (prod) ← `develop` (intégration) ← `feature/*` (dev)

### Branches

**`master`** : Production stable, merges de `develop`, versions taggées (v1.0.0)
**`develop`** : Intégration, PRs depuis `feature/*`, CI obligatoire
**`feature/*`** : Fonctionnalités (kebab-case), depuis `develop`, supprimées après merge

### Workflow

**Story (sous-phase X.Y)** :
1. `/execute-plan-phase X.Y` → Commit + Push + PR auto → develop
2. Merge PR GitHub
3. Répéter story X.Y+1

**Epic (phase complète)** :
1. Stories mergées develop ✅
2. `git checkout master && git merge develop --ff-only`
3. `git tag {version} && git push origin master --tags`
4. Release auto `.github/workflows/release.yml`
5. **⚠️ SYNC** : `git checkout develop && git pull origin master && git push`

**Versions** : `v0.x.x-xxx` (pre-release) / `v1.x.x` (prod)

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

### Commande Obligatoire

```bash
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

**Si succès** → Commit autorisé
**Si échec** → Corriger avant commit

### Détails Checks

1. **Ruff** : Voir [4.1 Ruff](#41-ruff)
2. **Mypy** : Voir [4.2 Mypy](#42-mypy)
3. **Tests** : Voir [6.4 Tests](#64-configuration--commandes)

### CI/CD

- ✅ CI GitHub Actions exécute automatiquement sur PR
- ✅ **Bloque merge** si checks échouent
- ❌ Pas de pre-commit hook local (éviter friction)

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
