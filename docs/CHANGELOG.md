---
title: "CHANGELOG - Historique Versions"
description: "Historique complet des modifications du projet par version (format Keep a Changelog). Consulter pour suivre évolution features, bugfixes, breaking changes par release."
date: "2025-11-17"
keywords: ["changelog", "versions", "history", "releases", "semver", "keep-a-changelog", "features", "bugfixes", "breaking-changes"]
scope: ["docs"]
technologies: []
---

# Historique Versions

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [v0.0.0-setup] - 2025-11-16

### Added

**Infrastructure & Documentation Initiale**
- Structure documentation modulaire dans `docs/` :
  - `REFERENCES.md` : Index références techniques avec lien vers `github-actions.md`
  - `ARCHITECTURE.md` : Diagrammes et ADR (prêt pour complétion Phase 1)
  - `VERSIONS.md` : Matrice compatibilité (prêt pour complétion Phase 1)
  - `CHANGELOG.md` : Historique modifications (format Keep a Changelog)
- Standards développement dans `.claude/CLAUDE.md` :
  - Stratégie branches Git (master/develop/feature, GitFlow simplifié)
  - Conventional Commits (feat, fix, docs, refactor, test, chore, ci, perf)
  - Pre-commit checks (ruff, mypy, pytest)
  - Workflow Pull Request (squash merge, CI validation)
- Référence technique `docs/references/github-actions.md` :
  - Syntaxe complète GitHub Actions (on, jobs, steps, runs-on)
  - Workflow examples (CI Quality Checks, Release Automation)
  - Secrets management (GITHUB_TOKEN, custom secrets)
  - Triggers (push, pull_request, tags)
- Workflow CI/CD `.github/workflows/release.yml` :
  - Trigger automatique sur tags `v*`
  - Création GitHub Release avec extraction CHANGELOG.md
  - Support prerelease (versions avec `-` comme v0.1.0-alpha)

**Git Setup**
- Branche `develop` créée comme branche d'intégration
- Branche `master` (production, protégée)
- Convention nommage branches : `feature/nom-descriptif` (kebab-case)

### Notes

**Phase** : Setup Infrastructure
**Branche** : `feature/initial-setup`
**Objectif** : Établir fondations Git, CI/CD et documentation avant développement

**Pas de tag** : Les versions démarrent en Phase 1 (v0.1.0-research)

**Prochaine étape** : Phase 1 - Recherche & Documentation

---

## [v0.1.0-research] - 2025-11-16

### Added

**Documentation Technique Complète**
- Matrice de compatibilité des versions (Python 3.13, FastAPI 0.121.2+, Pydantic 2.12.4+, Crawl4AI 0.7.7+, Tenacity 9.1.2+)
- Documentation modulaire des références techniques dans `docs/references/` :
  - `fastapi.md` : Dependency Injection, routes async, TestClient
  - `pydantic-v2.md` : Settings, validation, field_validator
  - `crawl4ai.md` : AsyncWebCrawler, BrowserConfig, JsonCssExtractionStrategy
  - `decodo-proxies.md` : Residential rotation, France targeting, authentication
  - `google-flights.md` : Multi-city params, date formats, currency/locale
  - `anti-detection.md` : Stealth mode Crawl4AI, user-agent rotation
  - `captcha-detection.md` : Patterns HTML (reCAPTCHA, hCaptcha), retry strategy
  - `tenacity.md` : @retry decorator, wait strategies, async support
  - `dokploy.md` : Dockerfile best practices, env vars
- Index `docs/REFERENCES.md` pour navigation centralisée

**Standards de Développement**
- Standards Python modernes dans `.claude/CLAUDE.md` :
  - Type hints PEP 695 (Python 3.13)
  - Configuration Ruff (linter & formatter)
  - Configuration Mypy strict mode
  - Patterns async (crawl4ai, error handling)
  - Structured logging (JSON, contexte)
  - Docstrings pragmatiques (PEP 257 : 1 ligne par défaut)
  - Anti-pattern : commentaires inline interdits

**Architecture & Décisions**
- Diagrammes architecture (composants, séquence) dans `docs/ARCHITECTURE.md`
- 6 ADR (Architecture Decision Records) documentés :
  - ADR #001 : Crawl4AI+Proxies vs SerpAPI
  - ADR #002 : Decodo vs Oxylabs (proxies résidentiels)
  - ADR #003 : Top 10 en mémoire (pas de DB)
  - ADR #004 : Tenacity pour retry logic
  - ADR #005 : Captcha handling strategy (MVP : détection only)
  - ADR #006 : JsonCssExtractionStrategy vs LLMExtractionStrategy

### Changed

- Structure documentation organisée en fichiers modulaires pour optimisation tokens (~44% économie)
- VERSIONS.md : Ajout checklist validation compatibilité

### Notes

**Phase** : Recherche & Documentation
**Branche** : `feature/research-stack`
**Objectif** : Établir base de connaissance technique avant développement MVP

**Prochaine étape** : Phase 2 - Setup Environnement Python

---

## [v0.2.0-structure] - 2025-11-17

### Added

**Structure Projet Complète**
- Arborescence complète du projet :
  - Fichiers racine : `README.md`, `.gitignore`, `.dockerignore`, `Dockerfile`, `pyproject.toml`, `.env.example`
  - Structure `app/` avec tous les modules :
    - `app/api/` : Routes FastAPI
    - `app/core/` : Configuration et logging
    - `app/models/` : Schémas Pydantic (request/response)
    - `app/services/` : Logique métier (crawler, parser, proxy, search, combination_generator)
    - `app/utils/` : Helpers génériques
    - `app/main.py` : FastAPI app entry point
  - Structure `tests/` miroir de `app/` :
    - `tests/unit/` : Tests unitaires avec mocks
    - `tests/integration/` : Tests end-to-end avec TestClient
  - Docstrings TODO dans tous fichiers Python pour complétion Phase 5

**Configuration Système**
- `.gitignore` complet : Python, tests, IDEs, environnements, Docker, OS
- `.dockerignore` : Exclusion fichiers inutiles pour build
- `.env.example` : Template variables environnement :
  - Logging : LOG_LEVEL
  - Decodo Proxies : DECODO_USERNAME, DECODO_PASSWORD, DECODO_PROXY_HOST
  - Features : PROXY_ROTATION_ENABLED, CAPTCHA_DETECTION_ENABLED

**Documentation Standards**
- `.claude/CLAUDE.md` complété avec nouvelles sections :
  - Organisation fichiers : Arborescence détaillée, principes séparation responsabilités
  - Workflow développement : Installation, commandes dev, feature development, variables env, debugging, troubleshooting
  - Tests : Stratégie TDD, types de tests (unit/intégration/E2E), commandes pytest, configuration, fixtures, bonnes pratiques, CI integration
  - Docker : Dockerfile multi-stage, commandes build/run, Docker Compose, optimisations avancées, déploiement Dokploy, troubleshooting, best practices

### Notes

**Phase** : Architecture & Squelette
**Branche** : `feature/project-structure`
**Objectif** : Créer la structure complète du projet (prête pour implémentation Phase 3+)

**Prochaine étape** : Phase 3 - Configuration & Build (pyproject.toml, Dockerfile, app minimale)

---

## [v0.3.0-build] - 2025-11-18

### Added

**Configuration Projet**
- `pyproject.toml` complet :
  - Metadata projet (name, version, description, authors)
  - Dependencies principales : FastAPI 0.121.2+, Pydantic 2.12.4+, Crawl4AI 0.7.7+, Tenacity 9.1.2+, Uvicorn, python-dotenv
  - Dependencies développement : pytest, pytest-asyncio, pytest-cov, ruff, mypy
  - Configuration ruff (linter & formatter) : line-length 88, target py313, select rules (E/F/I/N/UP/B/C4/SIM/RUF)
  - Configuration mypy strict mode : python_version 3.13, strict=true, overrides pour tests et crawl4ai
  - Configuration pytest : testpaths, asyncio_mode auto, coverage, markers (slow, integration)

**Docker & Build**
- Dockerfile multi-stage optimisé pour production :
  - Stage Builder : Python 3.13 slim, installation uv, `uv sync --frozen`, `crawl4ai-setup` (installe Playwright automatiquement)
  - Stage Runtime : Python 3.13 slim, non-root user (appuser), WORKDIR /app, healthcheck natif GET /health
  - Optimisations Dokploy : .dockerignore (exclut .git, tests, docs, cache), réduction taille image via multi-stage

**Application Minimale**
- FastAPI app minimale dans `app/main.py` :
  - Initialisation FastAPI avec metadata (title, version, description)
  - Endpoint GET `/health` retournant JSON `{"status": "ok"}`
- Tests integration pour health endpoint (`tests/integration/test_health.py`) :
  - TestClient FastAPI, test status 200, validation format réponse JSON

**CI/CD Quality Checks**
- Workflow GitHub Actions `.github/workflows/ci.yml` :
  - Triggers : pull_request + push sur branches develop/master
  - Setup : Python 3.13, cache uv dependencies (actions/cache avec key hashFiles pyproject.toml)
  - Installation : `uv sync --all-extras` + `crawl4ai-setup`
  - Jobs : lint (`ruff check .`), format (`ruff format . --check`), typecheck (`mypy app/`)
  - Tests unitaires temporairement désactivés (commentés) - À réactiver Phase 5.1+
  - Fail-fast : false (exécute tous jobs même si l'un échoue)
  - Coverage optionnelle : `pytest --cov=app --cov-report=xml` (upload codecov commenté)
- Badge CI status ajouté dans `README.md`

**Vérifications Locales**
- Installation complète validée : `uv sync --all-extras` + `crawl4ai-setup`
- Application locale fonctionnelle : `fastapi dev app/main.py` + test `curl http://localhost:8000/health`
- Tests integration passent : `pytest tests/integration/test_health.py -v`
- Quality checks passent : `ruff check .`, `ruff format . --check`, `mypy app/`
- Docker build réussi : `docker build -t flight-search-api .`
- Container Docker opérationnel : `docker run -p 8000:8000` + healthcheck fonctionnel

### Notes

**Phase** : Configuration & Build
**Branche** : `feature/config-build`
**Objectif** : Projet runnable avec configuration minimale (build local + Docker + CI/CD)

**Note importante** : Step "Tests with coverage" temporairement désactivé dans CI workflow (aucun test unitaire n'existe encore). À réactiver lors de Phase 5.1 (implémentation TDD services).

**Prochaine étape** : Phase 4 - Spécifications Techniques Détaillées (SPECS.md avec specs services, models, API)

---

## [v0.4.0-specs] - 2025-11-19

### Added

**Documentation Spécifications Techniques MVP**
- Structure documentation specs dans `docs/specs/` :
  - `docs/specs/epic-1-api-foundation/` : Stories 1-3 (Foundation API)
  - `docs/specs/epic-2-google-flights/` : Stories 4-6 (Intégration Google Flights)
  - `docs/specs/epic-3-production-ready/` : Story 7 (Robustesse production)
- Index centralisé `docs/SPECS.md` :
  - Vue d'ensemble MVP (36 story points, 7 stories, 3 epics)
  - Navigation vers specs Epic/Story spécifique
  - Statistiques projet (releases v0.5.0, v0.6.0, v0.7.0 → v1.0.0)
  - Process Phase 4 à 7 (Specs → TDD → Production → Captcha optionnel)

**Epic 1 : API Foundation (v0.5.0) - 13 story points**
- [Story 1 : Health check endpoint](specs/epic-1-api-foundation/story-1-health-check.md) - 2 pts
  - Tests GET /health (status 200, format JSON)
  - Configuration TestClient FastAPI
  - Validation contrat API minimal
- [Story 2 : Configuration & Logging](specs/epic-1-api-foundation/story-2-config-logging.md) - 3 pts
  - Pydantic Settings v2 (BaseSettings, Field, SettingsConfigDict)
  - Structured logging JSON (pythonjsonlogger, extra contexte métier)
  - Variables environnement (.env, validation types)
- [Story 3 : Search endpoint (mock)](specs/epic-1-api-foundation/story-3-search-endpoint.md) - 8 pts
  - POST /api/v1/search-flights (SearchRequest → SearchResponse)
  - Models Pydantic : SearchRequest, SearchResponse, FlightResult, SearchStats, Flight, DateRange
  - SearchService mock (données hardcodées Top 10)
  - Tests intégration TestClient (validation contrat)

**Epic 2 : Google Flights Integration (v0.6.0) - 18 story points**
- [Story 4 : Crawler + Parser](specs/epic-2-google-flights/story-4-crawler-parser.md) - 8 pts
  - CrawlerService : AsyncWebCrawler + BrowserConfig stealth
  - FlightParser : JsonCssExtractionStrategy (extraction prix, compagnie, horaires, durée depuis HTML Google Flights)
  - Captcha detection (patterns reCAPTCHA, hCaptcha) + CaptchaDetectedError
  - Tests unitaires avec mocks (HTML Google Flights simulé)
- [Story 5 : Multi-destinations](specs/epic-2-google-flights/story-5-multi-destinations.md) - 5 pts
  - CombinationGenerator : Génération permutations multi-city (Paris → Tokyo → Paris)
  - URLBuilder : Construction URLs Google Flights multi-city (format f=CDG&t=NRT&d=2025-06-01)
  - SearchService orchestration (crawl + parse + ranking Top 10 par prix)
  - Tests combinaisons complexes (3-5 destinations, 15-30 jours)
- [Story 6 : Proxies Decodo](specs/epic-2-google-flights/story-6-proxies.md) - 5 pts
  - ProxyService : Configuration Decodo (residential, France targeting)
  - Proxy rotation (1 IP par recherche, authentication via username/password)
  - Integration AsyncWebCrawler (proxy_config param)
  - Tests mock proxies (validation format credentials, rotation logic)

**Epic 3 : Production Ready (v0.7.0) - 5 story points**
- [Story 7 : Retry + Error handling](specs/epic-3-production-ready/story-7-retry.md) - 5 pts
  - Tenacity retry logic : wait_exponential (min 1s, max 10s) + jitter + stop_after_attempt(3)
  - Error handling : CaptchaDetectedError (retry + rotation), NetworkError (retry), ParsingError (fail fast)
  - Logging structured : retry attempts, proxy used, parsing errors, search_id contexte
  - Tests scenarios échec (captcha détecté, timeout, parsing invalide)

### Notes

**Phase** : Spécifications Techniques Détaillées
**Branche** : `feature/technical-specs`
**Objectif** : Définir comportements MVP complets (models, services, API, tests) avant implémentation TDD Phase 5

**Specs** : 7 user stories documentées (36 story points) selon template `docs/TEMPLATE_SPECS.md` (signatures sans implémentation, tableaux tests descriptifs, critères acceptation SMART)

**Prochaine étape** : Phase 5 - Implémentation TDD Epic 1 (Stories 1-3) → Release v0.5.0

---

## [v0.5.0] - 2025-11-20

### Added

**Epic 1 : API Foundation (MVP) - 13 story points**

- **Story 1 : Health check endpoint** :
  - Endpoint GET `/health` retournant JSON `{"status": "ok"}`
  - Tests integration TestClient FastAPI (status 200, validation format réponse)
  - Configuration baseline pour tests API

- **Story 2 : Configuration & Logging** :
  - Configuration Pydantic Settings v2 (`app/core/config.py`)
  - Variables environnement validées (LOG_LEVEL, DECODO credentials, features flags)
  - Structured logging JSON avec pythonjsonlogger (`app/core/logger.py`)
  - Contexte métier dans logs (extra fields pour search_id, destinations, etc.)

- **Story 3 : Search endpoint (mock)** :
  - Endpoint POST `/api/v1/search-flights` (SearchRequest → SearchResponse)
  - Models Pydantic complets :
    - `SearchRequest` : destinations, date_range, passengers, cabin_class
    - `SearchResponse` : results (Top 10), total_combinations, stats
    - `FlightResult` : segments list, total_price, total_duration
    - `FlightSegment` : origin, destination, departure/arrival (datetime), airline, flight_number, duration, price
    - `DateRange` : start, end (validation end ≥ start, allow_single_day)
    - `SearchStats` : search_id, timestamp, destinations_count, etc.
  - SearchService mock avec données hardcodées (10 résultats réalistes)
  - Tests unitaires models (21 tests) : validation, edge cases, single-day dates
  - Tests unitaires SearchService (5 tests) : ranking, format, cohérence
  - Tests unitaires routes (8 tests) : validation request, status codes, error handling
  - Tests integration endpoint (4 tests) : end-to-end flow, contrat API

### Notes

**Phase** : Implémentation TDD Epic 1
**Branche** : `feature/story-3-search-endpoint` (dernière story Epic 1)
**Objectif** : Foundation API complète (health, config, logging, search mock) pour release v0.5.0

**Coverage** : 38 tests (34 unitaires + 4 intégration), coverage ≥ 80%

**Prochaine étape** : Phase 6 - Implémentation TDD Epic 2 (Stories 4-6) → Release v0.6.0 (Intégration Google Flights réelle)

---

# Ressources

## Documentation Officielle

- **Keep a Changelog** : https://keepachangelog.com/
- **Semantic Versioning** : https://semver.org/
- **Conventional Commits** : https://www.conventionalcommits.org/
