---
title: "GitHub Actions - CI/CD Automation"
description: "Référence complète GitHub Actions pour CI/CD : syntaxe workflows, triggers (push, PR, tags), jobs parallèles/séquentiels, secrets management (GITHUB_TOKEN), workflows projet (ci.yml quality checks, release.yml automation). Consulter pour configuration pipelines, debugging, best practices."
date: "2025-17-11"
keywords: ["github-actions", "ci-cd", "ci", "workflows", "automation", "triggers", "jobs", "steps", "secrets", "github-token", "deployment", "release", "testing", "lint", "actions-marketplace"]
scope: ["deploy", "code"]
technologies: ["github-actions"]
---

# Syntaxe de Base

## Description

GitHub Actions utilise des fichiers YAML pour définir des workflows automatisés. Un workflow est composé de déclencheurs (`on`), de jobs (tâches parallèles ou séquentielles), et de steps (commandes ou actions réutilisables). Les workflows s'exécutent dans des environnements isolés (runners) et peuvent être déclenchés par des événements Git ou planifiés.

## Exemple minimal

```yaml
name: Nom du Workflow

on:
  push:
    branches: [develop, master]
  pull_request:
    branches: [develop]

jobs:
  nom-du-job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run command
        run: echo "Hello World"
```

## Points clés

- **`name`** : Nom affiché dans l'interface GitHub (optionnel mais recommandé)
- **`on`** : Événements déclencheurs (push, pull_request, schedule, etc.)
- **`jobs`** : Ensemble de tâches à exécuter (parallèles par défaut)
- **`runs-on`** : Environnement d'exécution (ubuntu-latest, windows-latest, macos-latest)
- **`steps`** : Liste d'actions séquentielles dans un job
- **`uses`** : Utilise une action réutilisable du marketplace ou custom
- **`run`** : Exécute une commande shell directement

# Triggers (Déclencheurs)

## Description

Les triggers définissent quand un workflow s'exécute. GitHub Actions supporte les événements Git (push, pull_request, tags), les déclenchements manuels (workflow_dispatch), et les planifications cron. Les filtres (branches, paths, types) permettent un contrôle fin sur l'exécution.

## Exemple minimal

```yaml
on:
  push:
    branches:
      - develop
      - master
    paths:
      - 'app/**'
      - 'tests/**'
  pull_request:
    branches:
      - develop
    types: [opened, synchronize, reopened]
  push:
    tags:
      - 'v*'           # Tous tags commençant par v
  workflow_dispatch:    # Déclenchement manuel
  schedule:
    - cron: '0 2 * * *'  # Tous les jours à 2h UTC
```

## Points clés

- **`branches`** : Filtrer par branches (push, pull_request)
- **`paths`** : Déclencher uniquement si fichiers spécifiques modifiés
- **`types`** : Types d'événements PR (opened, synchronize, reopened, closed)
- **`tags`** : Patterns pour release automation (`v*`, `v[0-9]+.*`)
- **`workflow_dispatch`** : Permet déclenchement manuel depuis GitHub UI
- **`schedule`** : Cron syntax pour planifications (UTC timezone)
- **Combinaisons** : Plusieurs triggers possibles dans un même workflow

# Jobs & Steps

## Description

Les jobs sont des unités de travail qui s'exécutent par défaut en parallèle. Chaque job tourne dans un environnement isolé (runner). Les steps sont des commandes ou actions séquentielles dans un job. La directive `needs` permet de créer des dépendances entre jobs pour une exécution séquentielle.

## Exemple minimal

**Jobs parallèles** :
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: ruff check .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test
        run: pytest
```

**Jobs séquentiels** :
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."

  test:
    needs: build  # Attend que build se termine
    runs-on: ubuntu-latest
    steps:
      - run: echo "Testing..."

  deploy:
    needs: [build, test]  # Attend build ET test
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

**Fail-fast strategy** :
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Continue même si un job échoue
    steps:
      - run: pytest
```

## Points clés

- **Parallèle par défaut** : Jobs s'exécutent en parallèle (gain de temps)
- **`needs`** : Crée dépendances entre jobs (exécution séquentielle)
- **`runs-on`** : Environnement isolé par job
- **`fail-fast`** : Par défaut `true`, mettre `false` pour voir toutes les erreurs CI
- **Steps séquentiels** : Toujours exécutés dans l'ordre au sein d'un job
- **Usage projet** : CI quality checks (lint, format, typecheck, test) avec `fail-fast: false`

# Actions Réutilisables

## Description

GitHub Actions propose un marketplace d'actions réutilisables. Les actions officielles (`actions/*`) couvrent les besoins courants (checkout, setup environnement, cache). Les actions tierces étendent les fonctionnalités (upload coverage, notifications, déploiements). Utiliser `uses` pour appeler une action avec paramètres via `with`.

## Exemple minimal

```yaml
steps:
  # Checkout code
  - name: Checkout repository
    uses: actions/checkout@v4

  # Setup Python
  - name: Setup Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.13'

  # Cache dependencies
  - name: Cache uv dependencies
    uses: actions/cache@v4
    with:
      path: ~/.cache/uv
      key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}

  # Action tierce
  - name: Upload coverage
    uses: codecov/codecov-action@v4
    with:
      files: ./coverage.xml
      flags: unittests
```

## Points clés

- **Actions officielles** : `actions/checkout`, `actions/setup-python`, `actions/cache`, `actions/upload-artifact`
- **Versionning** : Toujours spécifier version (`@v4`, `@v5`) pour stabilité
- **`with`** : Passer paramètres à l'action (clés-valeurs)
- **Cache** : Accélère CI de 30-60s (dépendances, build artifacts)
- **Marketplace** : https://github.com/marketplace?type=actions
- **Custom actions** : Possibilité de créer ses propres actions (JavaScript, Docker, Composite)

# Secrets Management

## Description

GitHub Actions gère les secrets via l'interface GitHub (Settings → Secrets and variables → Actions). Les secrets sont injectés dans les workflows via `${{ secrets.NOM_SECRET }}` et jamais exposés dans les logs. Le token `GITHUB_TOKEN` est auto-généré pour chaque workflow avec permissions limitées au repository.

## Exemple minimal

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: ./deploy.sh
        env:
          API_KEY: ${{ secrets.DECODO_API_KEY }}
          DB_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}

  release:
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
```

## Points clés

- **Configuration** : Settings → Secrets and variables → Actions (interface GitHub)
- **User-defined** : `secrets.NOM_SECRET` (configurés manuellement)
- **`GITHUB_TOKEN`** : Auto-généré, permissions read/write repository
- **Permissions GITHUB_TOKEN** : Créer releases, issues, PRs (pas accès Secrets, Settings)
- **Masquage auto** : GitHub masque secrets dans logs
- **Environnements** : Secrets peuvent être scopés par environnement (production, staging)
- **Usage projet** : Workflow Release utilise `GITHUB_TOKEN` pour créer release automatiquement

# Contexte & Variables

## Description

GitHub Actions fournit des variables de contexte prédéfinies accessibles via `${{ }}`. Ces variables contiennent des informations sur le workflow, le repository, l'événement déclencheur et l'environnement d'exécution. Les steps peuvent également produire des outputs réutilisables dans les steps suivants.

## Exemple minimal

**Variables prédéfinies** :
```yaml
steps:
  - name: Show context
    run: |
      echo "Branch: ${{ github.ref }}"
      echo "Commit: ${{ github.sha }}"
      echo "Actor: ${{ github.actor }}"
      echo "Event: ${{ github.event_name }}"
```

**Outputs entre steps** :
```yaml
steps:
  - name: Set output
    id: step1
    run: echo "VALUE=hello" >> $GITHUB_OUTPUT

  - name: Use output
    run: echo "Got: ${{ steps.step1.outputs.VALUE }}"
```

## Points clés

- **`github.ref`** : Référence complète (refs/heads/develop, refs/tags/v1.0.0)
- **`github.sha`** : Hash commit (40 caractères)
- **`github.event_name`** : Type événement (push, pull_request, workflow_dispatch)
- **`runner.os`** : OS de l'environnement (Linux, Windows, macOS)
- **`github.actor`** : Utilisateur ayant déclenché le workflow
- **Outputs** : `echo "KEY=value" >> $GITHUB_OUTPUT` pour partager entre steps
- **`$GITHUB_ENV`** : Définir variables d'environnement persistantes

# Workflows Projet

## Description

Le projet utilise deux workflows : `ci.yml` pour quality checks (lint, format, typecheck, tests) et `release.yml` pour release automation. Le workflow CI s'exécute sur PR et push (develop/master), le workflow Release se déclenche sur tags vX.X.X.

## Exemple - CI Quality Checks

**Fichier** : `.github/workflows/ci.yml`

```yaml
name: CI Quality Checks

on:
  push:
    branches: [develop, master]
  pull_request:
    branches: [develop]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Exécuter tous checks même si l'un échoue
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Cache uv dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras
          crawl4ai-setup  # Installe Playwright

      - name: Lint
        run: ruff check .

      - name: Format
        run: ruff format --check

      - name: Typecheck
        run: mypy app/

      - name: Tests
        run: pytest tests/unit/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

**Exemple - Release Automation** :

**Fichier** : `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Extract changelog
        id: changelog
        run: |
          VERSION=${{ steps.version.outputs.VERSION }}
          sed -n "/## \[$VERSION\]/,/## \[/p" docs/CHANGELOG.md | sed '$d' > release_notes.md

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ steps.version.outputs.VERSION }}
          body_path: release_notes.md
          draft: false
          prerelease: false
```

## Points clés

- **CI Trigger** : PR + push sur develop/master
- **CI Jobs** : Lint, Format, Typecheck, Test (parallèle avec fail-fast: false)
- **CI Cache** : uv dependencies (gain 30-60s)
- **Release Trigger** : Tag `v*` (ex: v1.0.0, v0.2.1)
- **Release Job** : Extrait version + changelog → Créer GitHub Release
- **Workflow** : `git tag v1.0.0 && git push origin v1.0.0` → Release automatique

# Best Practices & Debugging

## Description

Les bonnes pratiques GitHub Actions incluent le caching des dépendances, l'utilisation de fail-fast: false pour les quality checks, la sécurisation des secrets, et des workflows rapides (<5min). Le debugging passe par les logs GitHub, le re-run de jobs échoués, et l'outil `act` pour tests locaux.

## Exemple - Debugging

```yaml
steps:
  - name: Debug
    run: |
      echo "Current directory: $(pwd)"
      echo "Files: $(ls -la)"
      env  # Afficher toutes variables environnement
```

**Act (local testing)** :
```bash
# Installer act (https://github.com/nektos/act)
brew install act  # macOS
choco install act  # Windows

# Exécuter workflow localement
act pull_request  # Simule PR
act push          # Simule push
```

## Points clés

**✅ Recommandations** :
- **Cache dependencies** : Utiliser `actions/cache` pour uv/pip (gain 30-60s)
- **Fail-fast: false** : Voir toutes erreurs CI en un run
- **Matrix strategy** : Tester plusieurs versions Python si nécessaire
- **Secrets sécurisés** : Jamais hardcoder API keys dans workflows
- **Workflow minimal** : Garder jobs rapides (<5min idéal)

**❌ Anti-Patterns** :
- Installer dépendances sans cache (lent)
- Exécuter tests intégration sur chaque PR (coût proxies)
- Workflows complexes imbriqués (debugging difficile)
- Secrets dans logs (GitHub masque automatiquement mais éviter prints)

**Debugging** :
- **Logs** : Interface GitHub → Actions → Workflow run
- **Re-run** : Bouton "Re-run jobs" sur workflow échoué
- **Act** : Tests locaux (limitation : pas 100% identique à GitHub)

# Ressources

## Documentation Officielle

- **GitHub Actions Documentation** : https://docs.github.com/en/actions
- **GitHub Actions Toolkit** : https://github.com/actions/toolkit

## Ressources Complémentaires

- **Marketplace actions** : https://github.com/marketplace?type=actions
- **Awesome Actions** : https://github.com/sdras/awesome-actions
