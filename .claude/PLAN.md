# Plan d'action complet - flight-search-api

## Phase 0 : Setup Documentation & Git

**Objectif** : Initialiser la structure documentation et conventions Git

**Branche** : `feature/initial-setup`

**Prérequis (DÉJÀ FAIT)** :
- ✅ Repo GitHub créé et cloné
- ✅ Remote configuré
- ✅ Créer dossier .claude (où figure le plan)

### 0.1 Structure documentation vide
- [x] Créer `docs/`
- [x] Créer `docs/references/` (pour les fichiers de doc technique selon contexte projet)
- [x] Créer `.claude/CLAUDE.md`
- [x] Créer `docs/ARCHITECTURE.md`
- [x] Créer `docs/SPECS.md`
- [x] Créer `docs/REFERENCES.md` (index léger)
- [x] Créer `docs/VERSIONS.md`
- [x] Créer `docs/CHANGELOG.md`
- [x] Commit : `docs: create documentation structure`
- [x] Créer branche develop et push

📝 **Output** : Structure docs modulaire prête à remplir

### 0.2 Conventions Git & Release Workflow
- [x] Documenter stratégie branches (master/develop/feature)
- [x] Documenter Conventional Commits (feat, fix, docs, etc.)
- [x] Documenter pre-commit checks (ruff, mypy, pytest)
- [x] Documenter workflow Pull Request
- [x] Compléter `.claude/CLAUDE.md` - Section Git
- [x] Créer `docs/references/github-actions.md` :
      - Syntaxe GitHub Actions (on, jobs, steps, runs-on)
      - Workflow examples (CI/CD, Release automation)
      - Secrets management (GITHUB_TOKEN, custom secrets)
      - Triggers (push, pull_request, tags)
      → https://docs.github.com/en/actions
- [x] Compléter `docs/REFERENCES.md` comme index avec lien vers fichier modulaire
- [x] Créer `.github/workflows/release.yml` :
      - Trigger : tag v*
      - Auto-create GitHub Release
      - Include CHANGELOG.md content
- [x] Commit : `docs: add git conventions and release workflow`

📝 **Output** : `.claude/CLAUDE.md` (Git), `docs/references/github-actions.md`, `.github/workflows/release.yml`

### 0.3 Mise à jour CHANGELOG et version
- [x] Ajouter entrée v0.0.0-setup dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.0.0"`
- [x] Commit : `chore: bump version to 0.0.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop (pas de tag - versions démarrent Phase 1)

---

## Phase 1 : Recherche & Documentation

**Objectif** : Construire la base de connaissance avant tout dev

**Branche** : `feature/research-stack`

### 1.1 Recherche versions & compatibilité
- [x] Python 3.13 stabilité et compatibilité écosystème
- [x] FastAPI 0.121.2 (breaking changes, Pydantic v2)
- [x] Pydantic v2.10+ (migration depuis v1)
- [x] tenacity 9.0+ (retry strategies)
- [x] crawl4ai 0.7+ (async crawler, stealth mode, Playwright intégré)
- [x] Vérification matrice compatibilité croisée
- [x] Compléter `docs/VERSIONS.md` avec tableau + notes
- [x] Commit : `docs: add versions compatibility matrix`

📝 **Output** : `docs/VERSIONS.md`

**Note** : Playwright est installé automatiquement par `crawl4ai-setup`, pas besoin de l'installer séparément.

### 1.2 Documentation technique ciblée
- [x] Créer fichiers de référence modulaires dans `docs/references/` :
- [x] `fastapi.md` : Dependency Injection, async routes, TestClient
      → https://fastapi.tiangolo.com/
- [x] `pydantic-v2.md` : Settings, validation, field_validator
      → https://docs.pydantic.dev/latest/
- [x] `crawl4ai.md` : AsyncWebCrawler, BrowserConfig, JsonCssExtractionStrategy (extraction CSS)
      → https://docs.crawl4ai.com/
- [x] `decodo-proxies.md` : Residential rotation, France targeting, authentication, bandwidth optimization
      → https://help.decodo.com/docs/introduction
        **Note** : Format auth = username: customer-{api_key}-country-FR, password: your_password
- [x] `google-flights.md` : Multi-city params, date formats, currency/locale (France)
      → (reverse engineering via browser DevTools)
- [x] `anti-detection.md` : Stealth mode Crawl4AI, user-agent rotation, proxy rotation
      → https://docs.crawl4ai.com/core/browser-config/
- [x] `captcha-detection.md` : Patterns HTML (reCAPTCHA, hCaptcha), retry strategy avec rotation IP
      → (patterns de détection, pas de résolution dans MVP)
- [x] `tenacity.md` : @retry decorator, wait strategies, async
      → https://tenacity.readthedocs.io/
- [x] `dokploy.md` : Dockerfile best practices, env vars
      → https://docs.dokploy.com/
- [x] Compléter `docs/REFERENCES.md` comme index avec liens vers fichiers modulaires
- [x] Commit : `docs: add technical references`

📝 **Output** : `docs/REFERENCES.md` (index) + `docs/references/*.md` (10 fichiers : 9 de Phase 1.2 + github-actions.md de Phase 0.2)

**Note** : Si features additionnelles nécessaires pendant l'implémentation, créer nouveau fichier dans `docs/references/` et mettre à jour l'index REFERENCES.md.

### 1.3 Standards Python modernes
- [x] Python 3.13 type hints (PEP 695)
- [x] Ruff configuration (rules, pyproject.toml)
- [x] Mypy strict mode
- [x] Async patterns (crawl4ai, error handling)
- [x] Structured logging (JSON, contexte)
- [x] Docstrings pragmatiques (PEP 257 : 1 ligne par défaut)
- [x] Compléter `.claude/CLAUDE.md` - Section Standards
- [x] Ajouter règle anti-pattern : commentaires inline interdits
- [x] Commit : `docs: add Python standards to CLAUDE.md`

📝 **Output** : `.claude/CLAUDE.md` - Section Standards

### 1.4 Architecture & Décisions (ADR)
- [x] Créer diagrammes (composants, séquence)
- [x] Documenter flow de données (Requête HTTP → Services internes → Response JSON)
- [x] Rédiger ADR #001 : Crawl4AI+Proxies vs SerpAPI (coût, flexibilité, maintenance)
- [x] Rédiger ADR #002 : Decodo vs Oxylabs (prix, pool IP, France targeting)
- [x] Rédiger ADR #003 : Top 10 en mémoire (pas de DB)
- [x] Rédiger ADR #004 : Tenacity pour retry
- [x] Rédiger ADR #005 : Captcha handling strategy (proxies rotation + detection, pas de résolution dans MVP)
- [x] Rédiger ADR #006 : JsonCssExtractionStrategy vs LLMExtractionStrategy (coût, performance)
- [x] Compléter `docs/ARCHITECTURE.md` avec ADR intégrés
- [x] Commit : `docs: add ARCHITECTURE and ADR`

📝 **Output** : `docs/ARCHITECTURE.md`

### 1.5 Mise à jour CHANGELOG et version
- [x] Ajouter entrée v0.1.0-research dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.1.0"`
- [x] Commit : `chore: bump version to 0.1.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.1.0-research sur master

---

## Phase 2 : Architecture & Squelette

**Objectif** : Créer la structure complète du projet

**Branche** : `feature/project-structure`

### 2.1 Création structure complète
- [x] Créer fichiers racine : `README.md`, `.gitignore`, `.dockerignore`, `Dockerfile`, `pyproject.toml`, `.env.example`
- [x] Créer structure `app/` avec tous dossiers et fichiers
- [x] Créer structure `tests/` avec unit/ et integration/
- [x] Ajouter docstrings TODO dans tous fichiers Python
- [x] Commit : `chore: create project structure skeleton`

📝 **Output** : Arborescence complète avec fichiers vides + TODO

### 2.2 Configuration fichiers système
- [x] Remplir `.gitignore` (Python, tests, IDEs, env, Docker, OS)
- [x] Remplir `.dockerignore`
- [x] Créer `.env.example` avec variables :
      - LOG_LEVEL=INFO
      - DECODO_USERNAME=customer-XXXX-country-FR
      - DECODO_PASSWORD=your_password
      - DECODO_PROXY_HOST=pr.decodo.com:8080
      - PROXY_ROTATION_ENABLED=true
      - CAPTCHA_DETECTION_ENABLED=true
- [x] Commit : `chore: add system configuration files`

📝 **Output** : Fichiers config système prêts

### 2.3 Compléter CLAUDE.md
- [x] Vérifier section Contexte projet
- [x] Vérifier section Standards (déjà fait Phase 1.3)
- [x] Ajouter section Organisation fichiers (arborescence)
- [x] Vérifier section Anti-patterns
- [x] Vérifier section Git (déjà fait Phase 0.2)
- [x] Ajouter section Workflow développement
- [x] Ajouter section Tests (pytest commands)
- [x] Ajouter section Docker (build/run)
- [x] Commit si modifs : `docs: finalize CLAUDE.md`

📝 **Output** : `.claude/CLAUDE.md` complet

### 2.4 Mise à jour CHANGELOG et version
- [x] Ajouter entrée v0.2.0-structure dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.2.0"`
- [x] Commit : `chore: bump version to 0.2.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.2.0-structure sur master

---

## Phase 3 : Configuration & Build

**Objectif** : Projet runnable avec config minimale

**Branche** : `feature/config-build`

### 3.1 pyproject.toml complet
- [x] Section [project] : metadata + dependencies (fastapi, pydantic, crawl4ai, tenacity)
- [x] Section [project.optional-dependencies] : dev tools
- [x] Section [tool.ruff] : linting rules + formatting
- [x] Section [tool.mypy] : strict mode + overrides
- [x] Section [tool.pytest.ini_options] : test config + coverage
- [x] Commit : `chore(config): add complete pyproject.toml`

📝 **Output** : `pyproject.toml` complet

### 3.2 Dockerfile multi-stage optimisé
- [x] Stage 1 Builder : install uv + dependencies + crawl4ai-setup
      **Note** : crawl4ai-setup installe automatiquement Playwright + dépendances système
- [x] Stage 2 Runtime : copy deps + code, non-root user, healthcheck
- [x] Optimisé pour Dokploy
- [x] Commit : `chore(docker): add optimized Dockerfile`

📝 **Output** : `Dockerfile` production-ready

### 3.3 App minimale + health endpoint
- [x] Implémenter `app/main.py` : FastAPI app basique
- [x] Implémenter endpoint GET `/health` → `{"status": "ok"}`
- [x] Implémenter `tests/integration/test_health.py`
- [x] Commit : `feat(api): add minimal app with health endpoint`

📝 **Output** : App minimale testable

### 3.4 Vérifications locales
- [x] Install deps : `uv sync --all-extras`
- [x] Run post-install : `crawl4ai-setup` (installe Playwright)
- [x] Run app : `fastapi dev app/main.py`
- [x] Test health : `curl http://localhost:8000/health`
- [x] Run tests : `pytest -v`
- [x] Lint : `ruff check . && ruff format . --check`
- [x] Type check : `mypy app/`
- [x] Build Docker : `docker build -t flight-search-api .`
- [x] Run Docker : `docker run -p 8000:8000 flight-search-api`
- [x] Test Docker health : `curl http://localhost:8000/health`
- [x] Commit : `chore: verify local and docker builds`

📝 **Output** : Vérification que tout fonctionne

### 3.5 CI Quality Checks
- [x] Créer `.github/workflows/ci.yml` :
      - Trigger : PR + push sur develop/master
      - Setup : Python 3.13, cache uv dependencies (actions/cache)
      - Install : uv sync --all-extras && crawl4ai-setup (installe Playwright)
      - Jobs : lint (ruff check), format (ruff format --check), typecheck (mypy), tests (pytest tests/unit/)
      - Coverage : pytest --cov=app --cov-report=xml
      - Fail-fast : false (exécuter tous les checks même si l'un échoue)
      - Upload coverage : codecov/codecov-action (optionnel)
- [x] Ajouter badge CI dans README.md
- [x] Tester workflow en local : `act pull_request` (optionnel)
- [x] Commit : `ci: add quality checks workflow`

📝 **Output** : Pipeline CI pour qualité code (tests unitaires uniquement, tests intégration manuels)

**Note** : Step "Tests with coverage" temporairement désactivé (commenté dans ci.yml) car aucun test n'existe encore. À réactiver en Phase 5.1+ lors de l'implémentation TDD.

### 3.6 Mise à jour CHANGELOG et version
- [x] Ajouter entrée v0.3.0-build dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.3.0"`
- [x] Commit : `chore: bump version to 0.3.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.3.0-build sur master

---

## Phase 4 : Spécifications MVP (User Stories)

**Objectif** : Écrire specs détaillées par user story (business + technique)

**Branche** : `feature/technical-specs`

### 4.1 Structure documentation specs
- [x] Créer structure des epics dans `docs/specs/epic-X/story-Y.md` (1 fichier par story)
- [x] Compléter `docs/SPECS.md` comme index avec liens vers fichiers modulaires
- [x] Commit : `docs: add specs references`

📝 **Output** : `docs/SPECS.md` (index) + `docs/specs/*.md` (? epics, ? stories)

**Note** : Si specs additionnelles nécessaires pendant l'implémentation, créer nouveau fichier dans `docs/specs/*` suivant l'epics et la story et mettre à jour l'index SPECS.md.

---

## Epic 1: API Foundation

### 4.2 Story 1: Health check endpoint
- [x] Specs : Route GET /health, healthcheck logic
- [x] Contexte business : Monitoring production ready
- [x] Tests : Tests unitaires + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-1-api-foundation/story-1-health-check.md`
- [x] Commit : `docs(specs): add story 1 specifications`

📝 **Output** : Story 1 specs complètes (2 story points)

### 4.3 Story 2: Configuration & Logging
- [x] Specs : Settings (Pydantic BaseSettings), Logger (JSON structuré)
- [x] Contexte business : Config sécurisée (.env), monitoring logs
- [x] Tests : Tests unitaires Settings + Logger (à spécifier)
- [x] Ajouter à `docs/specs/epic-1-api-foundation/story-2-config-logging.md`
- [x] Commit : `docs(specs): add story 2 specifications`

📝 **Output** : Story 2 specs complètes (3 story points)

### 4.4 Story 3: Search endpoint basique (mock)
- [x] Specs : Models (FlightSegment, SearchRequest avec segments, SearchResponse)
- [x] Specs : SearchService (mock data), Route POST /api/v1/search-flights
- [x] Contexte business : API itinéraires multi-segments avec dates flexibles par segment
- [x] Tests : Tests unitaires Models + Service + Route + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-1-api-foundation/story-3-search-endpoint.md`
- [x] Commit : `docs(specs): complete story 3 specifications`

📝 **Output** : Story 3 specs complètes (8 story points)

---

## Epic 2: Google Flights Integration

### 4.5 Story 4: Crawler + Parser (1 destination)
- [x] Specs : CrawlerService (Crawl4AI + AsyncWebCrawler)
- [x] Specs : FlightParser (JsonCssExtractionStrategy, sélecteurs CSS)
- [x] Contexte business : Vraies données Google Flights (proof of concept)
- [x] Tests : Tests unitaires Crawler + Parser + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-2-google-flights/story-4-crawler-parser.md`
- [x] Commit : `docs(specs): add story 4 specifications`

📝 **Output** : Story 4 specs complètes (8 story points)

### 4.6 Story 5: Proxies Decodo (anti-détection)
- [x] Specs : ProxyService (Decodo config, residential FR)
- [x] Specs : Rotation proxies (round-robin ou random)
- [x] Contexte business : Anti-détection Google, coûts optimisés
- [x] Tests : Tests unitaires ProxyService + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-2-google-flights/story-5-proxies.md`
- [x] Commit : `docs(specs): add story 5 specifications`

📝 **Output** : Story 5 specs complètes (5 story points)

### 4.7 Story 6: Multi-city Search (CombinationGenerator)
- [x] Specs : CombinationGenerator (itertools.product dates, ordre segments fixe)
- [x] Specs : SearchService orchestration (multiple crawls parallèles)
- [x] Specs : Top 10 ranking (tri prix + limite 10 résultats)
- [x] Contexte business : Itinéraires fixes multi-segments (2-5 segments max Google Flights)
- [x] Tests : Tests unitaires Generator + Service + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-2-google-flights/story-6-multi-city-search.md`
- [x] Commit : `docs(specs): add story 6 specifications`

📝 **Output** : Story 6 specs complètes (5 story points)

---

## Epic 3: Production Ready

### 4.8 Story 7: Retry + Error handling
- [x] Specs : Tenacity retry logic (exponential backoff + jitter)
- [x] Specs : Error handling (5xx retry, 4xx non-retry)
- [x] Specs : Logging before_sleep callback
- [x] Contexte business : Robustesse production, SLA garantis
- [x] Tests : Tests unitaires retry + error handling + intégration (à spécifier)
- [x] Ajouter à `docs/specs/epic-3-production-ready/story-7-retry.md`
- [x] Commit : `docs(specs): add story 7 specifications`

📝 **Output** : Story 7 specs complètes (5 story points)

---

### 4.9 Mise à jour CHANGELOG et version
- [x] Ajouter entrée v0.4.0-specs dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.4.0"`
- [x] Commit : `chore: bump version to 0.4.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.4.0-specs sur master

---

## Phase 5 : Implémentation MVP (TDD par Story)

**Objectif** : Développer stories avec TDD strict (unitaires → intégration → validation)

**Branche** : `feature/story-X` (1 branche par story)

**Workflow TDD** : Voir `.claude/CLAUDE.md` - Section "Workflow TDD par story"

**Workflow Release Epic** :
1. Toutes stories Epic mergées sur develop ✅
2. Mise à jour CHANGELOG (section dédiée par Epic)
3. Merge develop → master → Tag version → GitHub Release (workflow automatique)

**Note** : Si specs incomplètes détectées durant implémentation, compléter `docs/specs/epic-X/story-Y.md` puis continuer TDD

---

## Epic 1: API Foundation

### 5.1 Story 1: Health check endpoint

**Branche** : `feature/story-1-health-check`

- [x] **RAPPEL : Réactiver step "Tests with coverage" dans `.github/workflows/ci.yml`** (décommenter lignes 46-47)
- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-1-health-check.md
- [x] **Validation manuelle** : `curl http://localhost:8000/health` → `{"status": "ok"}`
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(api): add health check endpoint`
- [x] **PR** : feature/story-1 → develop

📝 **Output** : Story 1 complétée (2 story points)

### 5.2 Story 2: Configuration & Logging

**Branche** : `feature/story-2-config-logging`

- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-2-config-logging.md
- [x] **Validation manuelle** : App lit .env, logs JSON structurés avec extra context
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(core): add config and structured logging`
- [x] **PR** : feature/story-2 → develop

📝 **Output** : Story 2 complétée (3 story points)

### 5.3 Story 3: Search endpoint basique (mock)

**Branche** : `feature/story-3-search-endpoint`

- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-3-search-endpoint.md
- [x] **Validation manuelle** : `curl -X POST http://localhost:8000/api/v1/search-flights`
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(api): add search endpoint with mock data`
- [x] **PR** : feature/story-3 → develop

📝 **Output** : Story 3 complétée (8 story points)

---

### 5.4 Validation Epic 1 et mise à jour CHANGELOG

**🔍 Validation qualité** :

- [x] Lancer agent `reviewer` avec paramètres :
  - `epic_number`: "1"
  - `previous_version_tag`: "v0.4.0"
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit si refactor** : `chore(epic-1): refactor for standards compliance`

📝 **Output** : Epic 1 validé - stories 1-3 conformes aux standards

**📝 Mise à jour version** :

- [x] Ajouter entrée v0.5.0 dans `docs/CHANGELOG.md`
- [x] Mettre à jour version dans `app/main.py` : `version="0.5.0"`
- [x] **Commit** : `chore: bump version to 0.5.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin Epic 1** : Merge develop→master → Tag v0.5.0 → GitHub Release

---

## Epic 2: Google Flights Integration

### 5.5 Story 4: Crawler + Parser (1 destination)

**Branche** : `feature/story-4-crawler-parser`

- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-4-crawler-parser.md
- [x] **Validation manuelle** : Vraies données Google Flights, logs parsing success
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(services): add crawler and parser with real Google Flights data`
- [x] **PR** : feature/story-4 → develop

📝 **Output** : Story 4 complétée (8 story points)

### 5.6 Story 5: Proxies Decodo (anti-détection)

**Branche** : `feature/story-5-proxies`

- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-5-proxies.md
- [x] **Validation manuelle** : Logs montrent proxies actifs + rotation
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(services): add Decodo proxies with rotation`
- [x] **PR** : feature/story-5 → develop

📝 **Output** : Story 5 complétée (5 story points)

### 5.7 Story 6: Multi-city Search (CombinationGenerator)

**Branche** : `feature/story-6-multi-city-search`

- [x] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-6-multi-city-search.md
- [x] **Validation manuelle** : 3 segments avec dates flexibles, vérifier Top 10 triés par prix
- [x] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [x] **Commit** : `feat(services): add multi-segment search and top 10 ranking`
- [x] **PR** : feature/story-6 → develop

📝 **Output** : Story 6 complétée (5 story points)

---

### 5.8 Validation Epic 2 et mise à jour CHANGELOG

**🔍 Validation qualité** :

- [ ] Lancer agent `reviewer` avec paramètres :
  - `epic_number`: "2"
  - `previous_version_tag`: "v0.5.0"
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit si refactor** : `chore(epic-2): refactor for standards compliance`

📝 **Output** : Epic 2 validé - stories 4-6 conformes aux standards

**📝 Mise à jour version** :

- [ ] Ajouter entrée v0.6.0 dans `docs/CHANGELOG.md`
- [ ] Mettre à jour version dans `app/main.py` : `version="0.6.0"`
- [ ] **Commit** : `chore: bump version to 0.6.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin Epic 2** : Merge develop→master → Tag v0.6.0 → GitHub Release

---

## Epic 3: Production Ready

### 5.9 Story 7: Retry + Error handling

**Branche** : `feature/story-7-retry`

- [ ] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-7-retry.md
- [ ] **Validation manuelle** : Simuler échec, vérifier retry dans logs
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add retry logic and error handling`
- [ ] **PR** : feature/story-7 → develop

📝 **Output** : Story 7 complétée (5 story points)

---

### 5.10 Validation Epic 3 et mise à jour CHANGELOG

**🔍 Validation qualité** :

- [ ] Lancer agent `reviewer` avec paramètres :
  - `epic_number`: "3"
  - `previous_version_tag`: "v0.6.0"
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit si refactor** : `chore(epic-3): refactor for standards compliance`

📝 **Output** : Epic 3 validé - story 7 conforme aux standards

**📝 Mise à jour version** :

- [ ] Ajouter entrée v0.7.0 dans `docs/CHANGELOG.md`
- [ ] Mettre à jour version dans `app/main.py` : `version="0.7.0"`
- [ ] **Commit** : `chore: bump version to 0.7.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin Epic 3** : Merge develop→master → Tag v0.7.0 → GitHub Release

---

### 5.11 Validation complète MVP et CHANGELOG

**🔍 Validation qualité automatique** :

- [ ] Lancer agent `reviewer` avec paramètres :
  - `epic_number`: "1-2-3"
  - `previous_version_tag`: "v0.7.0"
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit si refactor** : `chore(mvp): refactor for standards compliance`

📝 **Output** : MVP validé - codebase complète conforme aux standards

**🔍 Audit spécifique MVP** (éléments non couverts par reviewer) :

- [ ] **Architecture (`docs/ARCHITECTURE.md`)** :
  - [ ] Diagrammes à jour (composants, séquence)
  - [ ] ADRs conformes implémentation réelle

**🧪 Tests end-to-end complets** :

- [ ] **Recherches multi-city avec vraies clés Decodo** :
  - [ ] 2 segments : Paris → Tokyo (7 jours) → New York (5 jours)
  - [ ] 3 segments : Paris → Tokyo → Sydney → Paris
  - [ ] 5 segments (max) : Tour du monde multi-stops
  - [ ] Vérifier Top 10 résultats triés par prix croissant
  - [ ] Vérifier structure JSON conforme `SearchResponse` schema

- [ ] **Analyse logs production** :
  - [ ] Taux de succès parsing ≥ 90%
  - [ ] Taux captcha détecté (baseline pour Phase 7 décision)
  - [ ] Temps réponse moyen < 15s par recherche multi-city
  - [ ] Proxy rotation active (logs montrent IPs différentes)
  - [ ] Structured JSON logs avec contexte (search_id, destinations, proxy_used)

- [ ] **Validation Docker** :
  - [ ] `docker build -t flight-search-api:v0.7.0 .` → Succès
  - [ ] `docker run -p 8000:8000 --env-file .env flight-search-api:v0.7.0` → App démarre
  - [ ] Health check : `curl http://localhost:8000/health` → `{"status": "ok"}`
  - [ ] Search endpoint : `curl -X POST http://localhost:8000/api/v1/search-flights` → 10 résultats

**📊 Validation business** :

- [ ] **Démo client** :
  - [ ] UX validée : Format JSON lisible, champs pertinents (price, airline, departure_date, segments)
  - [ ] Performance acceptable : Temps réponse < 15s pour 2-3 segments
  - [ ] Feedback client positif : Acceptation MVP

- [ ] **Monitoring coûts** :
  - [ ] Bandwidth Decodo : ~200KB par recherche (optimisations actives)
  - [ ] Coût estimé : ~0.0008€ par recherche (~$4/GB Decodo)
  - [ ] Pas de coûts LLM (extraction CSS uniquement)

**📚 Documentation synchronisée** :

- [ ] **CHANGELOG.md** : Entrées v0.5.0, v0.6.0, v0.7.0 complètes
- [ ] **ARCHITECTURE.md** : ADRs à jour avec implémentation réelle
- [ ] **SPECS.md** : Index complet (stories 1-6)
- [ ] **REFERENCES.md** : Index à jour (10 fichiers références techniques)
- [ ] **VERSIONS.md** : Matrice compatibilité conforme dépendances installées

**✅ Décision Phase 6** :

- **Si v0.7.0 OK sans bugs critiques** : ✅ Passer à Phase 6 (Documentation + Release v1.0.0)
- **Si bugs critiques trouvés** : ❌ Fix via hotfix → Nouveau tag v0.7.1 → Revalider

📝 **Output** : v0.7.0 validé, prêt pour Phase 6 (Documentation finale)

**Note** : Cette checklist exhaustive sert aussi de modèle pour validation futures versions majeures (v2.0.0, v3.0.0, etc.)

---

## Phase 6 : Documentation finale & Release MVP (v1.0.0)

**Objectif** : Documentation complète + Release production v1.0.0

**Branche** : `feature/documentation`

**Prérequis** : v0.7.0 validé en Phase 5.11 ✅

---

### 6.1 README.md complet
- [ ] Section Description projet
- [ ] Section Prérequis (Python 3.13, Docker, uv)
- [ ] Section Installation locale
- [ ] Section Configuration (env vars)
- [ ] Section Usage (exemples curl)
- [ ] Section Tests (commandes pytest)
- [ ] Section Déploiement Dokploy
- [ ] Section Limites connues (Decodo bandwidth costs, Google rate limits, captcha detection only)
- [ ] Section Monitoring (coûts proxies, taux de succès, captcha rate)
- [ ] Commit : `docs: add complete README`

📝 **Output** : README.md professionnel

---

### 6.2 CHANGELOG consolidé v1.0.0 et version
- [ ] Vérifier entrées v0.5.0, v0.6.0, v0.7.0 complètes dans CHANGELOG.md
- [ ] Créer section v1.0.0 avec résumé features MVP complètes
- [ ] Enrichir SPECS.md section Statistiques avec timeline releases
- [ ] Mettre à jour version dans `app/main.py` : `version="1.0.0"`
- [ ] Commit : `chore: bump version to 1.0.0 and update changelog`

📝 **Output** : CHANGELOG.md v1.0.0 complet + SPECS.md enrichi avec releases

---

### 6.3 Release v1.0.0 Production
- [ ] Push branche : `git push origin feature/documentation`
- [ ] Créer Pull Request sur GitHub : `feature/documentation` → `develop`
- [ ] (Manuel) Merger la PR sur GitHub
- [ ] Pull develop en local : `git checkout develop && git pull`
- [ ] Merge develop → master : `git checkout master && git merge develop --ff-only`
- [ ] Tag v1.0.0 : `git tag v1.0.0 && git push origin master --tags` (déclenche workflow release.yml)
- [ ] Vérifier GitHub Release auto-créée
- [ ] Marquer "Latest release" (pas Pre-release)

📝 **Output** : v1.0.0 Production release sur GitHub

**Distinction versions** :
- **v0.x.x** : Dev releases (Pre-release GitHub)
- **v1.0.0** : Production release (Latest release GitHub)
- Workflow détecte automatiquement : `contains(github.ref, '-')` → Pre-release

---

## 6.4 Déploiement Dokploy

**Objectif** : Déployer MVP en production avec logs structurés fichier + header traçabilité

### Logs Fichier & Rotation
- [ ] Configurer RotatingFileHandler dans `app/core/logger.py` :
      - Créer dossier `logs/` si absent
      - Ajouter handler fichier avec rotation (10MB max, 5 backups)
      - Formatter JSON identique au stdout
      - Logger dans `logs/app.log`
- [ ] Ajouter header traçabilité `X-Search-ID` dans `app/api/routes.py` :
      - Générer UUID unique par recherche
      - Retourner dans header response (pas dans body JSON)
      - Logger search_id dans extra context de tous les logs
- [ ] Créer script cleanup logs dans `app/utils/cleanup.py` :
      - Fonction `cleanup_old_logs(retention_days=30)`
      - Parcourir dossier `logs/`
      - Supprimer fichiers modifiés il y a plus de 30 jours
      - Logger nombre fichiers supprimés
- [ ] Commit : `feat(logs): add file logging with rotation and cleanup`

### Déploiement
- [ ] Configurer Dokploy : connecter repo GitHub
- [ ] Ajouter env vars dans UI Dokploy :
      - LOG_LEVEL=INFO
      - DECODO_USERNAME
      - DECODO_PASSWORD
      - DECODO_PROXY_HOST
      - PROXY_ROTATION_ENABLED=true
      - CAPTCHA_DETECTION_ENABLED=true
- [ ] Déclencher build automatique (push sur master)
- [ ] Vérifier deployment : `curl https://ton-domaine.com/health`
- [ ] Tester endpoint complet avec n8n : vérifier header `X-Search-ID` dans response
- [ ] Monitorer logs Dokploy UI (stdout) : captcha rate, proxy costs, success rate
- [ ] Vérifier logs fichiers sur VPS : `docker exec <container_id> ls -lh logs/`

### Scheduled Task Cleanup (Dokploy UI)
- [ ] Créer Schedule Job via UI Dokploy :
      - Nom : "Log Cleanup"
      - Cron expression : `0 3 * * *` (tous les jours à 3h du matin)
      - Commande : `python -c "from app.utils.cleanup import cleanup_old_logs; cleanup_old_logs(30)"`
      - Activer logs exécution
- [ ] Tester manuellement : exécuter via bouton "Run Now" dans UI
- [ ] Vérifier logs Schedule Job : confirmer suppression fichiers > 30 jours

📝 **Output** : API MVP en production avec monitoring actif + logs fichiers rotatifs + traçabilité X-Search-ID

**Notes** :
- Dokploy capture stdout automatiquement (logs JSON visibles dans UI)
- Logs fichiers stockés dans container : `/app/logs/app.log`
- Rotation automatique : 10MB × 5 backups = 50MB max
- Cleanup automatique : Dokploy Schedule Jobs exécute `cleanup_old_logs()` chaque nuit à 3h
- Header `X-Search-ID` permet de corréler logs sans polluer response JSON
- Pas besoin de volume Docker persistant : logs rotatifs suffisants pour debugging (50MB max)

---

## Phase 7A : Analyse & Spécifications Captcha (Post-MVP - Optionnel)

**Objectif** : Décision data-driven + spécifications techniques si GO

**Pré-requis** :
- ✅ MVP v1.0.0 déployé (Phase 6.4) et monitoring actif
- ✅ Logs captcha rate analysés sur 1-2 semaines minimum
- ✅ Décision basée sur métriques réelles

**Branche** : `feature/technical-specs-captcha`

---

### 7A.1 Analyse & Décision GO/NO-GO
- [ ] Analyser logs monitoring : calculer taux captcha (nombre captchas / total requêtes) sur 1-2 semaines
- [ ] Calculer impact business : % recherches échouées à cause captchas
- [ ] Décider si 2Captcha nécessaire (seuil recommandé : >5% blocages)
- [ ] Si taux < 5% : STOP ici (pas besoin Phase 7)
- [ ] Si taux ≥ 5% : Documenter décision ADR #007 "2Captcha Integration Decision"
- [ ] Commit : `docs: add captcha decision ADR`

📝 **Output** : Décision GO/NO-GO documentée

---

### 7A.2 Recherche & Documentation 2Captcha
- [ ] Documentation 2Captcha : API, pricing, types captchas supportés (https://2captcha.com/2captcha-api)
- [ ] Estimation coûts : captchas/mois × $0.001-0.003
- [ ] Comparer avec coût recherches perdues
- [ ] Valider ROI positif
- [ ] Créer `docs/references/2captcha.md`
- [ ] Mettre à jour `docs/REFERENCES.md` (index)
- [ ] Commit : `docs: add 2captcha technical reference`

📝 **Output** : Documentation technique 2Captcha complète

---

## Epic 4: Captcha Solving

### 7A.3 Story 8: Captcha Solver (spécifications)
- [ ] Créer structure : `docs/specs/epic-4-captcha-solving/story-8-captcha-solver.md`
- [ ] Specs : CaptchaSolverService (2Captcha integration, fallback logic)
- [ ] Specs : Intégration CrawlerService (détection → résolution)
- [ ] Specs : Monitoring coûts (métriques, ROI tracking)
- [ ] Contexte business : Réduction blocages, ROI positif
- [ ] Tests : Tests unitaires + intégration (à spécifier)
- [ ] Commit : `docs(specs): add story 8 captcha solver specifications`

📝 **Output** : Story 8 specs complètes

---

### 7A.4 Mise à jour CHANGELOG et version
- [ ] Ajouter entrée v0.8.0-specs dans `docs/CHANGELOG.md`
- [ ] Mettre à jour version dans `app/main.py` : `version="0.8.0"`
- [ ] Commit : `chore: bump version to 0.8.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.8.0-specs sur master

---

## Phase 7B : Implémentation Captcha Solving

**Objectif** : Implémenter story 8 avec TDD

**Branche** : `feature/story-8-captcha-solver`

**Workflow TDD** : Voir `.claude/CLAUDE.md` - Section "Workflow TDD par story"

**Note** : Si specs incomplètes détectées durant implémentation, compléter `docs/specs/epic-4-captcha-solving/story-8-captcha-solver.md` puis continuer TDD

---

## Epic 4: Captcha Solving

### 7B.1 Story 8: Captcha Solver (implémentation)

**Branche** : `feature/story-8-captcha-solver`
- [ ] **Implémentation TDD** : Suivre workflow CLAUDE.md + specs story-8-captcha-solver.md
- [ ] **Validation manuelle** : Test avec vraie clé 2Captcha, vérifier coûts/temps résolution
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add 2captcha solver integration`
- [ ] **PR** : feature/story-8 → develop

📝 **Output** : Story 8 complétée

---

### 7B.2 Validation Epic 4 et mise à jour CHANGELOG

**🔍 Validation qualité** :

- [ ] Lancer agent `reviewer` avec paramètres :
  - `epic_number`: "4"
  - `previous_version_tag`: "v1.0.0"
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit si refactor** : `chore(epic-4): refactor for standards compliance`

📝 **Output** : Epic 4 validé - story 8 conforme aux standards

**📝 Mise à jour version** :

- [ ] Ajouter entrée v1.1.0 dans `docs/CHANGELOG.md`
- [ ] Mettre à jour version dans `app/main.py` : `version="1.1.0"`
- [ ] Commit : `chore: bump version to 1.1.0 and update changelog`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin Epic 4** : Push branche → PR → Merge develop → Merge develop→master → Tag v1.1.0 sur master → GitHub Release (workflow automatique)

---

### 7B.3 Déploiement Dokploy v1.1.0
- [ ] Ajouter TWOCAPTCHA_API_KEY dans Dokploy UI
- [ ] Activer CAPTCHA_SOLVING_ENABLED=true
- [ ] Déployer v1.1.0 sur production
- [ ] Monitorer coûts et efficacité pendant 1 semaine
- [ ] Ajuster seuils si nécessaire

📝 **Output** : v1.1.0 en production avec monitoring ROI actif

---

## Notes importantes

### Docstrings (règle pragmatique)
- **1 ligne par défaut** : Suffit pour 90% des cas
- **Format complet** : Uniquement si comportement non-évident, side-effects, ou exceptions importantes
- **Pas de verbosité** : Ne pas répéter ce que la signature dit déjà

### Commentaires inline
- **❌ Interdits** sauf demande explicite user
- Code doit être self-explanatory

### Tests
- **Unitaires** : Avec mocks (Crawl4AI, Decodo proxies, HTML Google Flights)
- **Tests captcha** : Mock détection + retry scenarios
- **Intégration** : TestClient FastAPI
- **Coverage** : Minimum 80%

### Git workflow
- Toujours travailler sur feature branches
- Workflow Pull Requests (documenté en Phase 0.2)
- Release : develop → master avec tag via PR

### Stack Crawl4AI + Proxies

**Architecture scraping** :
- **Crawl4AI** : AsyncWebCrawler avec stealth mode (Playwright intégré automatiquement)
- **Extraction** : JsonCssExtractionStrategy (pas de coûts API LLM)
- **Decodo Proxies** : Residential rotation automatique (France), ~$4/GB
- **Anti-détection** : Stealth mode natif Crawl4AI, user-agent rotation

**Captcha handling (approche progressive)** :

**Phase MVP (Phase 5-6)** :
- Proxies résidentiels Decodo (évite 95%+ des captchas)
- Stealth mode Crawl4AI (anti-détection native)
- Retry avec rotation IP (contourne captchas temporaires)
- **Détection captcha** : Log uniquement, pas de résolution
- **Monitoring** : Taux de captcha, impact business

**Phase Post-MVP (Phase 7 - Optionnelle si monitoring montre >5% blocages)** :
- Intégration 2Captcha en fallback
- Coût additionnel : ~$0.001-0.003 par captcha résolu
- Décision data-driven après analyse logs production
- ROI validé avant implémentation

**Optimisations bandwidth** :
- Désactiver images, CSS, ads, scripts inutiles dans Crawl4AI
- Économie attendue : ~90% vs scraping full page
- Coût estimé : 0.0008€ par recherche (~200KB/recherche)

**Pas de coûts LLM** :
- Pas d'API key OpenAI/Anthropic/Claude nécessaire
- Extraction pure CSS selectors (gratuit)
- LLM optionnel uniquement si structure HTML imprévisible (hors scope MVP)

**Monitoring requis** :
- Taux de captcha par recherche (décision Phase 7)
- Bandwidth consommé (GB/jour)
- Coût proxies mensuel
- Taux de succès parsing
- (Si Phase 7) Coût 2Captcha mensuel

### Structure finale
```
flight-search-api/
├── .claude/
│   ├── commands/
│   │   └── execute-plan-phase.md
│   ├── CLAUDE.md      # Standards, conventions
│   └── PLAN.md        # Ce plan
├── .github/
│   └── workflows/
│       ├── ci.yml          # Quality checks (Phase 3.6)
│       └── release.yml     # Release automation (Phase 0.2)
├── docs/
│   ├── references/     # Documentation technique modulaire
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
│   ├── specs/          # Spécifications détaillées par story (Phase 4)
│   │   ├── epic-1-api-foundation/
│   │   │   ├── story-1-health-check.md
│   │   │   ├── story-2-config-logging.md
│   │   │   └── story-3-search-endpoint.md
│   │   ├── epic-2-google-flights/
│   │   │   ├── story-4-crawler-parser.md
│   │   │   ├── story-5-proxies.md
│   │   │   └── story-6-multi-city-search.md
│   │   └── epic-3-production-ready/
│   │       └── story-7-retry.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── SPECS.md        # Index specs (liens vers stories)
│   ├── REFERENCES.md   # Index léger avec liens
│   └── VERSIONS.md
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── models/
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── combination_generator.py
│   │   ├── crawler_service.py
│   │   ├── flight_parser.py
│   │   ├── proxy_service.py
│   │   ├── search_service.py
│   │   └── (captcha_solver.py - Phase 7 optionnelle)
│   ├── utils/
│   └── main.py
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
│       └── (test_captcha_solver.py - Phase 7)
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Dépendances principales
```toml
[project]
dependencies = [
    "fastapi>=0.121.2",
    "pydantic>=2.12.4",
    "pydantic-settings>=2.0",
    "crawl4ai>=0.7.7",  # Inclut Playwright automatiquement
    "tenacity>=9.1.2",
    "uvicorn>=0.30",
    "httpx>=0.27",
    "python-json-logger>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.6",
    "mypy>=1.11",
]

# Si Phase 7 activée :
# captcha = [
#     "2captcha-python>=1.4",
# ]
```