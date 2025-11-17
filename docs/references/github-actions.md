---
title: "GitHub Actions - CI/CD Automation"
description: "Référence complète GitHub Actions pour CI/CD : syntaxe workflows, triggers (push, PR, tags), jobs parallèles/séquentiels, secrets management (GITHUB_TOKEN), workflows projet (ci.yml quality checks, release.yml automation). Consulter pour configuration pipelines, debugging, best practices."
date: "2025-17-11"
keywords: ["github-actions", "ci-cd", "ci", "workflows", "automation", "triggers", "jobs", "steps", "secrets", "github-token", "deployment", "release", "testing", "lint", "actions-marketplace"]
scope: ["deploy", "code"]
technologies: ["github-actions"]
---

# 1. Syntaxe de Base

## Structure d'un Workflow

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

**Éléments principaux** :

- **`name`** : Nom affiché dans l'interface GitHub
- **`on`** : Événements déclencheurs (triggers)
- **`jobs`** : Ensemble de tâches à exécuter
- **`runs-on`** : Environnement d'exécution (ubuntu-latest, windows-latest, macos-latest)
- **`steps`** : Liste d'actions séquentielles

# 2. Triggers (on)

## Push & Pull Request

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
```

**Options** :
- `branches` : Filtrer par branches
- `paths` : Déclencher uniquement si fichiers spécifiques modifiés
- `types` : Types d'événements PR (opened, synchronize, etc.)

## Tags (Release Automation)

```yaml
on:
  push:
    tags:
      - 'v*'           # Tous tags commençant par v
      - 'v[0-9]+.*'    # Tags versionnés (v1.0.0, v2.1.3)
```

**Usage projet** : Workflow Release déclenché sur tag `v*.*.*`

## Événements Multiples

```yaml
on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]
  workflow_dispatch:  # Déclenchement manuel
  schedule:
    - cron: '0 2 * * *'  # Tous les jours à 2h UTC
```

# 3. Jobs & Steps

## Jobs Parallèles

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

**Par défaut** : Jobs s'exécutent en parallèle (gain de temps)

## Jobs Séquentiels (avec dépendances)

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

## Fail-Fast Strategy

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Continue même si un job échoue
    steps:
      - run: pytest
```

**Usage projet** : CI quality checks (lint, format, typecheck, test) avec `fail-fast: false` pour voir toutes les erreurs

# 4. Actions Réutilisables (uses)

## Actions Officielles

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
```

**Actions courantes** :
- `actions/checkout` : Clone repository
- `actions/setup-python` : Installer Python
- `actions/cache` : Cache dépendances (accélère CI)
- `actions/upload-artifact` : Sauvegarder fichiers entre jobs

## Actions Tierces

```yaml
steps:
  # Upload coverage to Codecov
  - name: Upload coverage
    uses: codecov/codecov-action@v4
    with:
      files: ./coverage.xml
      flags: unittests
```

# 5. Secrets Management

## Secrets GitHub

**Configuration** : Settings → Secrets and variables → Actions

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
```

**Secrets disponibles** :

- **User-defined** : `secrets.NOM_SECRET` (configurés manuellement)
- **`GITHUB_TOKEN`** : Token auto-généré par GitHub (permissions limitées)

## GITHUB_TOKEN

```yaml
steps:
  - name: Create Release
    uses: actions/create-release@v1
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    with:
      tag_name: ${{ github.ref }}
      release_name: Release ${{ github.ref }}
```

**Permissions** :
- Lire/écrire repository
- Créer releases, issues, PRs
- **Pas d'accès** : Secrets, Settings

**Usage projet** : Workflow Release utilise `GITHUB_TOKEN` pour créer release automatiquement

# 6. Workflows Projet

## CI Quality Checks (ci.yml)

**Fichier** : `.github/workflows/ci.yml`

**Trigger** : PR + push sur develop/master

**Jobs** :
1. **Lint** : `ruff check`
2. **Format** : `ruff format --check`
3. **Typecheck** : `mypy app/`
4. **Test** : `pytest tests/unit/ --cov`

**Configuration** :
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

## Release Automation (release.yml)

**Fichier** : `.github/workflows/release.yml`

**Trigger** : Tag `v*` (ex: v1.0.0, v0.2.1)

**Job** : Créer GitHub Release avec contenu CHANGELOG.md

**Configuration** :
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
          # Extraire section correspondante de CHANGELOG.md
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

**Workflow** :
1. Developer tag version : `git tag v1.0.0 && git push origin v1.0.0`
2. Workflow déclenché automatiquement
3. Release créée sur GitHub avec notes extraites de CHANGELOG.md

# 7. Contexte & Variables

## Variables Prédéfinies

```yaml
steps:
  - name: Show context
    run: |
      echo "Branch: ${{ github.ref }}"
      echo "Commit: ${{ github.sha }}"
      echo "Actor: ${{ github.actor }}"
      echo "Event: ${{ github.event_name }}"
```

**Variables utiles** :
- `github.ref` : Référence complète (refs/heads/develop, refs/tags/v1.0.0)
- `github.sha` : Hash commit
- `github.event_name` : Type événement (push, pull_request, etc.)
- `runner.os` : OS de l'environnement (Linux, Windows, macOS)

## Outputs entre Steps

```yaml
steps:
  - name: Set output
    id: step1
    run: echo "VALUE=hello" >> $GITHUB_OUTPUT

  - name: Use output
    run: echo "Got: ${{ steps.step1.outputs.VALUE }}"
```

# 8. Best Practices

## ✅ Recommandations

1. **Cache dependencies** : Utiliser `actions/cache` pour uv/pip (gain 30-60s)
2. **Fail-fast: false** : Voir toutes erreurs CI en un run
3. **Matrix strategy** : Tester plusieurs versions Python si nécessaire
4. **Secrets sécurisés** : Jamais hardcoder API keys dans workflows
5. **Workflow minimal** : Garder jobs rapides (<5min idéal)

## ❌ Anti-Patterns

- ❌ Installer dépendances sans cache (lent)
- ❌ Exécuter tests intégration sur chaque PR (coût proxies)
- ❌ Workflows complexes imbriqués (debugging difficile)
- ❌ Secrets dans logs (GitHub masque automatiquement mais éviter prints)

# 9. Debugging

## Logs

```yaml
steps:
  - name: Debug
    run: |
      echo "Current directory: $(pwd)"
      echo "Files: $(ls -la)"
      env  # Afficher toutes variables environnement
```

## Re-run Jobs

- Interface GitHub : Bouton "Re-run jobs" sur workflow échoué
- Utile pour erreurs transitoires (network timeout, etc.)

## Act (local testing)

```bash
# Installer act (https://github.com/nektos/act)
brew install act  # macOS
choco install act  # Windows

# Exécuter workflow localement
act pull_request  # Simule PR
act push          # Simule push
```

**Limitation** : Pas 100% identique à GitHub (secrets, caching)

# Ressources

## Documentation Officielle

- **GitHub Actions Documentation** : https://docs.github.com/en/actions
- **GitHub Actions Toolkit** : https://github.com/actions/toolkit

## Ressources Complémentaires

- **Marketplace actions** : https://github.com/marketplace?type=actions
- **Awesome Actions** : https://github.com/sdras/awesome-actions
