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
1. Développement sur `feature/*`
2. Merge `feature/*` → `develop` (via PR)
3. Quand `develop` prête : Merge `develop` → `master`
4. Tag version sur `master` (ex: `v1.0.0`)
5. GitHub Actions crée Release automatiquement

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