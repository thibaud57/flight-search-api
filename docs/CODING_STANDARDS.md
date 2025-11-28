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
7. [Sécurité & Secrets](#7-sécurité--secrets)
   - [7.1 Variables Environnement](#71-variables-environnement)
   - [7.2 Masquage Logs](#72-masquage-logs)
   - [7.3 Secrets CI/CD](#73-secrets-cicd)

---

## 1. Standards Python

### 1.1 Type Hints (PEP 695)

#### Règles Obligatoires

- ✅ **CRITICAL** : Utiliser PEP 695 partout (`class Response[T]:`, `def process[T](items: list[T]) -> T:`)
- ✅ **CRITICAL** : Annoter TOUTES les signatures (args + return)
- ✅ Utiliser `list[T]`, `dict[K, V]` (pas `List[T]`, `Dict[K, V]`)
- ✅ Préférer `X | None` à `Optional[X]`
- ✅ Ajouter `model_config = ConfigDict(extra="forbid")` sur tous les models Pydantic
- ✅ Type alias : `type JsonDict = dict[str, str | int | float | bool | None]`
- ✅ Bounds : `class Processor[T: BaseModel]:` (upper bound) ou `TypeVar('T', str, int)` pour contraintes

#### Exemples

```python
# Génériques PEP 695
class Response[T]:
    data: T
    status: int

def process[T](items: list[T]) -> T:
    return items[0]

# Union types (X | None, pas Optional[X])
def get_user(id: int | str) -> User | None:
    pass

# Pydantic ConfigDict
from pydantic import BaseModel, ConfigDict

class SearchRequest(BaseModel):
    destinations: list[str]
    model_config = ConfigDict(extra="forbid")  # Rejette champs inconnus
```

**❌ Ne pas utiliser** : `Generic[T]`, `TypeVar`, `Optional`, `Union` (ancienne syntaxe pré-Python 3.10)

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

```python
# 1. Circular imports → TYPE_CHECKING block
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services import ProxyService

# 2. Runtime conditionnels → if statement
if format == "excel":
    import openpyxl  # Import optionnel

# 3. Imports coûteux → lazy loading
def train_model():
    import tensorflow as tf  # Import lourd différé
```

**Justification requise** : Toute exception MUST have comment explaining WHY.

---

#### Règle 2 : Imports via `__init__.py` (HOW)

**RÈGLE CRITIQUE** : ❌ **NEVER import from internal modules** — Always use `__init__.py` public API.

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

- ✅ 1 ligne par défaut (focus sur **POURQUOI**, pas **QUOI**)
- ❌ Pas de verbosité (ne pas répéter ce que les types disent déjà)

```python
# ✅ Concis
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

- Line length 88, Python 3.13, linters : E/F/I/N/UP/B/C4/SIM/RUF
- Tests : `S101` (assert) autorisé, format : double quotes + spaces

**Configuration** : Voir `pyproject.toml` sections `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]`

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

- `strict = true` sur `app/` (10 flags activés), relax sur `tests/`, ignore libs sans stubs

**Configuration** : Voir `pyproject.toml` section `[tool.mypy]` + overrides

**Commande** : `mypy app/`

#### Workflow

- ✅ **Strict mode OBLIGATOIRE** sur `app/` (10 flags activés automatiquement)
- ✅ **CI bloque** si mypy échoue
- ✅ **MUST** : Aucun `# type: ignore` sans justification commentée

**Format requis type ignore** :
```python
# ✅ Correct
result = external_lib.call()  # type: ignore[no-untyped-call]  # Lib sans stubs

# ❌ INCORRECT - PR REJETÉE
result = external_lib.call()  # type: ignore
```

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
# ✅ Correct
logger.info("Search completed", extra={"search_id": "abc123", "destinations": [...], "duration_ms": 1234})

# ❌ Incorrect
logger.info("Search completed")  # Pas de contexte
```

**Configuration** : Voir `app/core/logger.py`

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

**Pyramide Tests** : 60% Unit (services, models) → 30% Integration (API routes) → 10% E2E (manuels)

**Règles TDD strictes** :
- ✅ **ALWAYS** : Tests unitaires AVANT implémentation (red → green → refactor)
- ✅ Tests intégration APRÈS tous tests unitaires de la story
- ✅ **NEVER** : Commit si tests échouent
- ❌ Ne JAMAIS commencer intégration si tests unitaires échouent
- ❌ **CRITICAL** : Coverage minimum 80% (CI bloque si inférieur)

#### Workflow TDD par Story

1. **Tests Unitaires** : Chaque composant (red → green → refactor) → Tous tests passent ✅
2. **Tests Intégration** : End-to-end TestClient (si API route) → Tests passent ✅
3. **Validation Manuelle** : curl/Postman → Commit si OK

**Formats** : AAA (Arrange/Act/Assert) pour unit, Given/When/Then pour integration, `@pytest.mark.asyncio` pour async

---

### 4.2 Types de Tests

#### 1. Tests Unitaires (`tests/unit/`)

- Testent 1 fonction/classe isolée avec mocks (AsyncMock, MagicMock)
- Rapides (<1s pour 100 tests), coverage minimum 80%

```python
@pytest.fixture
def mock_crawler():
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(html="<html>", success=True)
    return crawler

@pytest.mark.asyncio
async def test_crawl_with_captcha(mock_crawler):
    service = CrawlerService(crawler=mock_crawler)
    with pytest.raises(CaptchaDetectedError):
        await service.crawl_google_flights("https://example.com")
```

---

#### 2. Tests Intégration (`tests/integration/`)

- TestClient FastAPI, mocks externes uniquement (Crawl4AI/Decodo), pas services internes

```python
def test_search_flights_endpoint(client, mock_crawler):
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

- ✅ **DRY** : 0 duplication, factory pattern avec params flexibles
- ✅ Constantes centralisées (`helpers.py`), fixtures délèguent aux factories

```python
@pytest.fixture
def date_range_factory():
    def _create(start_offset=1, duration=6, as_dict=False):
        start, end = get_date_range(start_offset, duration)
        return {"start": start.isoformat(), "end": end.isoformat()} if as_dict else DateRange(...)
    return _create
```

**Chargement** : `tests/conftest.py` → `pytest_plugins = ["tests.fixtures.factories", "tests.fixtures.mocks", "tests.fixtures.helpers"]`

**Nommage** : `*_factory` (callable), `mock_*` (objet), `get_*`/`assert_*` (helpers), `UPPER_CASE` (constantes)

---

### 4.4 Configuration Pytest

- testpaths `tests/`, patterns `test_*.py`, coverage `--cov=app`, asyncio auto
- Markers : `slow`, `integration`

**Configuration** : Voir `pyproject.toml` section `[tool.pytest.ini_options]`

**Commandes** :
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

**Story (sous-phase)** : `/execute-plan-phase X.Y` → PR auto → Merger sur GitHub → Répéter

**Epic (phase complète)** :
1. Stories mergées sur develop ✅
2. `git checkout master && git merge develop --ff-only`
3. `git tag v1.x.x && git push origin master --tags` → Release auto via `.github/workflows/release.yml`
4. **Sync develop** : `git checkout develop && git pull origin master && git push`

**Versions** : `v0.x.x-xxx` (dev, pre-release) vs `v1.x.x` (prod, latest)

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

```bash
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

**Checks** : Lint → Format → Type check → Tests unitaires → Coverage ≥ 80%

**CI** : GitHub Actions bloque merge si échec, pas de hook local (friction dev)

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

---

## 7. Sécurité & Secrets

### 7.1 Variables Environnement

**RÈGLE CRITIQUE** : ❌ **NEVER commit `.env` to version control**

**Justification** :
- `.env` contient secrets sensibles (PROXY_PASSWORD, API keys, credentials)
- Déjà présent dans `.gitignore`
- Production : Secrets injectés via Dokploy UI (jamais dans code)

**Workflow Recommandé** :

```bash
# 1. Développement local
cp .env.example .env
vim .env  # Remplir avec vraies valeurs locales (JAMAIS commit)

# 2. Production (Dokploy UI - Variables Environment)
PROXY_USERNAME=customer-{api_key}-country-FR
PROXY_PASSWORD=***********
LOG_LEVEL=INFO
CAPTCHA_DETECTION_ENABLED=true

# 3. CI/CD (GitHub Secrets → Actions)
secrets.PROXY_USERNAME
secrets.PROXY_PASSWORD
```

**Anti-Patterns** :
- ❌ `git add .env` → Leak credentials publiquement
- ❌ Hardcoder secrets : `API_KEY = "sk-xxx-yyy"` → Code source exposé
- ❌ Partager `.env` via Slack/email → Insécure

**Vérification** : `.env` dans `.gitignore` (ligne déjà présente)

---

### 7.2 Masquage Logs

**Règle** : ✅ **ALWAYS mask sensitive data in structured logs**

**✅ Correct** :
```python
logger.info(
    "Proxy configured successfully",
    extra={
        "proxy_host": "pr.decodo.com",  # OK (public info)
        "country": "FR",                 # OK
    }
)
```

**❌ INCORRECT - LEAK SECRETS** :
```python
# ❌ Password visible dans logs production
logger.info(f"Proxy: {username}:{password}@pr.decodo.com")

# ❌ API key dans logs
logger.debug(f"Using API key: {api_key}")
```

**Référence** : §2.3 Structured Logging (L338-359) pour format complet `extra={}`

---

### 7.3 Secrets CI/CD

**GitHub Actions** : Utiliser GitHub Secrets (Settings → Secrets and variables → Actions)

**Exemple workflow** :
```yaml
env:
  PROXY_USERNAME: ${{ secrets.PROXY_USERNAME }}
  PROXY_PASSWORD: ${{ secrets.PROXY_PASSWORD }}
```

**Règles** :
- ✅ Secrets stockés dans GitHub UI (encrypted)
- ✅ Jamais exposer secrets dans logs CI (`echo $SECRET` → masqué auto)
- ❌ Jamais commit secrets dans `.github/workflows/*.yml`

**Référence** : `.github/workflows/ci.yml` (workflow existant)
