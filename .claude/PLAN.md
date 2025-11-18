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

### 0.3 Mise à jour CHANGELOG
- [x] Ajouter entrée v0.0.0-setup dans `docs/CHANGELOG.md`
- [x] Commit : `docs: update changelog for setup phase`

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

**Avantages structure modulaire** :
- Chargement ciblé des références nécessaires (~44% économie tokens)
- Navigation rapide dans IDE
- Meilleure gestion Git (historique, conflits)

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

### 1.5 Mise à jour CHANGELOG
- [x] Ajouter entrée v0.1.0-research dans `docs/CHANGELOG.md`
- [x] Commit : `docs: update changelog for research phase`

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

### 2.4 Mise à jour CHANGELOG
- [x] Ajouter entrée v0.2.0-structure dans `docs/CHANGELOG.md`
- [x] Commit : `docs: update changelog for structure phase`

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

### 3.6 Mise à jour CHANGELOG
- [x] Ajouter entrée v0.3.0-build dans `docs/CHANGELOG.md`
- [x] Commit : `docs: update changelog for build phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.3.0-build sur master

---

## Phase 4 : Spécifications MVP (User Stories)

**Objectif** : Écrire specs détaillées par user story (business + technique)

**Branche** : `feature/technical-specs` (continuer branche actuelle)

**Structure** : `docs/specs/epic-X/story-Y.md` (1 fichier par story)

**Process** : Pour chaque story → Remplir template TEMPLATE_SPECS.md

---

### Epic 1: API Foundation (v0.5.0)

#### Story 1: Health check endpoint

- [ ] Specs : Route GET /health, healthcheck logic
- [ ] Contexte business : Monitoring production ready
- [ ] Tests : 3 unitaires + 2 intégration
- [ ] Ajouter à `docs/specs/epic-1-api-foundation/story-1-health-check.md`
- [ ] Commit : `docs(specs): add story 1 specifications`

📝 **Output** : Story 1 specs complètes (2 story points)

#### Story 2: Configuration & Logging

- [ ] Specs : Settings (Pydantic BaseSettings), Logger (JSON structuré)
- [ ] Contexte business : Config sécurisée (.env), monitoring logs
- [ ] Tests : 6 unitaires (3 Settings + 3 Logger)
- [ ] Ajouter à `docs/specs/epic-1-api-foundation/story-2-config-logging.md`
- [ ] Commit : `docs(specs): add story 2 specifications`

📝 **Output** : Story 2 specs complètes (3 story points)

#### Story 3: Search endpoint basique (mock)

- [x] Specs : Models (SearchRequest, SearchResponse) ← **DÉJÀ FAIT ✅**
- [ ] Specs : SearchService (mock data), Route POST /search-flights
- [ ] Contexte business : API testable client, contrat validé
- [ ] Tests : 38 tests (21 Models + 5 Service + 8 Route + 4 intégration)
- [ ] Ajouter à `docs/specs/epic-1-api-foundation/story-3-search-endpoint.md`
- [ ] Commit : `docs(specs): complete story 3 specifications`

📝 **Output** : Story 3 specs complètes (8 story points)

**Note** : SearchStats corrigé → `captcha_detected` retiré (Phase 7 post-MVP uniquement)

---

### Epic 2: Google Flights Integration (v0.6.0)

#### Story 4: Crawler + Parser (1 destination)

- [ ] Specs : CrawlerService (Crawl4AI + AsyncWebCrawler)
- [ ] Specs : FlightParser (JsonCssExtractionStrategy, sélecteurs CSS)
- [ ] Contexte business : Vraies données Google Flights (proof of concept)
- [ ] Tests : 22 tests (10 Crawler + 8 Parser + 4 intégration)
- [ ] Ajouter à `docs/specs/epic-2-google-flights/story-4-crawler-parser.md`
- [ ] Commit : `docs(specs): add story 4 specifications`

📝 **Output** : Story 4 specs complètes (8 story points)

#### Story 5: Multi-destinations (CombinationGenerator)

- [ ] Specs : CombinationGenerator (itertools.product, permutations multi-city)
- [ ] Specs : SearchService orchestration (multiple crawls)
- [ ] Specs : Top 10 ranking (tri prix + limite 10 résultats)
- [ ] Contexte business : Feature MVP complète (2-10 destinations)
- [ ] Tests : 17 tests (8 Generator + 6 Service + 3 intégration)
- [ ] Ajouter à `docs/specs/epic-2-google-flights/story-5-multi-destinations.md`
- [ ] Commit : `docs(specs): add story 5 specifications`

📝 **Output** : Story 5 specs complètes (5 story points)

#### Story 6: Proxies Decodo (anti-détection)

- [ ] Specs : ProxyService (Decodo config, residential FR)
- [ ] Specs : Rotation proxies (round-robin ou random)
- [ ] Contexte business : Anti-détection Google, coûts optimisés
- [ ] Tests : 11 tests (8 unitaires + 3 intégration)
- [ ] Ajouter à `docs/specs/epic-2-google-flights/story-6-proxies.md`
- [ ] Commit : `docs(specs): add story 6 specifications`

📝 **Output** : Story 6 specs complètes (5 story points)

---

### Epic 3: Production Ready (v0.7.0)

#### Story 7: Retry + Error handling

- [ ] Specs : Tenacity retry logic (exponential backoff + jitter)
- [ ] Specs : Error handling (5xx retry, 4xx non-retry)
- [ ] Specs : Logging before_sleep callback
- [ ] Contexte business : Robustesse production, SLA garantis
- [ ] Tests : 15 tests (10 unitaires + 5 intégration)
- [ ] Ajouter à `docs/specs/epic-3-production-ready/story-7-retry.md`
- [ ] Commit : `docs(specs): add story 7 specifications`

📝 **Output** : Story 7 specs complètes (5 story points)

---

### Finalisation Phase 4

- [ ] Vérifier cohérence globale (7 stories, metadata complètes)
- [ ] Vérifier dépendances entre stories
- [ ] Vérifier total tests estimés (~103 tests)
- [ ] Mettre à jour `docs/SPECS.md` (index avec liens vers stories)
- [ ] Mise à jour CHANGELOG : v0.4.0-specs
- [ ] Commit : `docs(changelog): update for specs phase`

📝 **Output** : 7 stories spécifiées, 36 story points, ~103 tests estimés

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.4.0-specs sur master

---

## Phase 5 : Implémentation MVP (TDD par Story)

**Objectif** : Développer stories avec TDD strict (unitaires → intégration → validation)

**Branche** : `feature/story-X` (1 branche par story)

**Workflow TDD** : Voir `.claude/CLAUDE.md` - Section Tests / Workflow TDD par story

**Process** :
1. **TDD Phase 1** : Tests unitaires composant 1 → Implémentation → Tests passent ✅
2. **TDD Phase 2** : Tests unitaires composant 2 → Implémentation → Tests passent ✅
3. **TDD Phase 3** : Tests intégration end-to-end → Validation ✅
4. **Validation manuelle** : curl/Postman + logs
5. **Commit** + **PR** → develop

---

### Epic 1: API Foundation (v0.5.0)

#### Story 1: Health check endpoint

**Branche** : `feature/story-1-health-check`

- [ ] **RAPPEL : Réactiver step "Tests with coverage" dans `.github/workflows/ci.yml`** (décommenter lignes 46-47)
- [ ] **TDD** : Tests unitaires → Implémentation route GET /health
- [ ] **Tests intégration** : TestClient end-to-end (2 tests)
- [ ] **Validation manuelle** : `curl http://localhost:8000/health` → `{"status": "ok"}`
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(api): add health check endpoint`
- [ ] **PR** : feature/story-1 → develop

📝 **Output** : Story 1 complétée (2 story points, ~5 tests)

#### Story 2: Configuration & Logging

**Branche** : `feature/story-2-config-logging`

- [ ] **TDD Phase 1** : Tests unitaires Settings → Implémentation Settings
- [ ] **TDD Phase 2** : Tests unitaires Logger → Implémentation Logger
- [ ] **Validation manuelle** : App lit .env, logs JSON structurés avec extra context
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(core): add config and structured logging`
- [ ] **PR** : feature/story-2 → develop

📝 **Output** : Story 2 complétée (3 story points, 6 tests)

#### Story 3: Search endpoint basique (mock)

**Branche** : `feature/story-3-search-endpoint`

- [ ] **TDD Phase 1 : Models**
  - Écrire 21 tests unitaires (test_models.py)
  - Implémenter Models (request.py, response.py)
  - Tests Models passent ✅
- [ ] **TDD Phase 2 : SearchService mock**
  - Écrire 5 tests unitaires (test_search_service.py)
  - Implémenter SearchService mock (retourne 3 résultats aléatoires)
  - Tests Service passent ✅
- [ ] **TDD Phase 3 : Route**
  - Écrire 8 tests unitaires (test_api_routes.py)
  - Implémenter Route POST /search-flights
  - Tests Route passent ✅
- [ ] **Tests intégration** : 4 tests end-to-end (TestClient)
- [ ] **Validation manuelle** : `curl -X POST http://localhost:8000/api/v1/search-flights`
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(api): add search endpoint with mock data`
- [ ] **PR** : feature/story-3 → develop

📝 **Output** : Story 3 complétée (8 story points, 38 tests)

**Fin Epic 1** : Merge develop → master → Tag v0.5.0 → GitHub Release (workflow automatique)

---

### Epic 2: Google Flights Integration (v0.6.0)

#### Story 4: Crawler + Parser (1 destination)

**Branche** : `feature/story-4-crawler-parser`

- [ ] **TDD Phase 1** : Tests unitaires CrawlerService → Implémentation
- [ ] **TDD Phase 2** : Tests unitaires FlightParser → Implémentation
- [ ] **TDD Phase 3** : Intégrer dans SearchService (remplacer mock)
- [ ] **Tests intégration** : 4 tests end-to-end (vraies données 1 destination)
- [ ] **Validation manuelle** : Vraies données Google Flights, logs parsing success
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add crawler and parser with real Google Flights data`
- [ ] **PR** : feature/story-4 → develop

📝 **Output** : Story 4 complétée (8 story points, 22 tests)

#### Story 5: Multi-destinations (CombinationGenerator)

**Branche** : `feature/story-5-multi-destinations`

- [ ] **TDD Phase 1** : Tests unitaires CombinationGenerator → Implémentation
- [ ] **TDD Phase 2** : Tests unitaires SearchService orchestration → Implémentation
- [ ] **TDD Phase 3** : Tests unitaires Top 10 ranking → Implémentation
- [ ] **Tests intégration** : 3 tests end-to-end (3 destinations → Top 10 vols)
- [ ] **Validation manuelle** : 3 destinations, vérifier Top 10 triés par prix
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add multi-city search and top 10 ranking`
- [ ] **PR** : feature/story-5 → develop

📝 **Output** : Story 5 complétée (5 story points, 17 tests)

#### Story 6: Proxies Decodo (anti-détection)

**Branche** : `feature/story-6-proxies`

- [ ] **TDD Phase 1** : Tests unitaires ProxyService → Implémentation
- [ ] **TDD Phase 2** : Tests unitaires rotation proxies → Implémentation
- [ ] **TDD Phase 3** : Intégrer CrawlerService avec ProxyService
- [ ] **Tests intégration** : 3 tests end-to-end (vraies clés Decodo)
- [ ] **Validation manuelle** : Logs montrent proxies actifs + rotation
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add Decodo proxies with rotation`
- [ ] **PR** : feature/story-6 → develop

📝 **Output** : Story 6 complétée (5 story points, 11 tests)

**Fin Epic 2** : Merge develop → master → Tag v0.6.0 → GitHub Release (workflow automatique)

---

### Epic 3: Production Ready (v0.7.0)

#### Story 7: Retry + Error handling

**Branche** : `feature/story-7-retry`

- [ ] **TDD Phase 1** : Tests unitaires retry decorators (Tenacity) → Implémentation
- [ ] **TDD Phase 2** : Tests unitaires error handling + logging → Implémentation
- [ ] **TDD Phase 3** : Intégrer CrawlerService avec retry logic
- [ ] **Tests intégration** : 5 tests end-to-end (échecs simulés : timeouts, 5xx)
- [ ] **Validation manuelle** : Simuler échec, vérifier retry dans logs
- [ ] **Quality checks** : ruff + mypy + coverage ≥ 80%
- [ ] **Commit** : `feat(services): add retry logic and error handling`
- [ ] **PR** : feature/story-7 → develop

📝 **Output** : Story 7 complétée (5 story points, 15 tests)

**Fin Epic 3** : Merge develop → master → Tag v0.7.0 → GitHub Release (workflow automatique)

---

### Finalisation Phase 5 (Validation v0.7.0)

**Validation complète avant v1.0.0** :

- [ ] **Tests end-to-end complets** : Lancer 10+ recherches avec vraies clés Decodo
- [ ] **Démo client final** : Validation UX, performance, format JSON
- [ ] **Validation business** : Feedback client, acceptation MVP
- [ ] **Analyse logs** : Taux de succès, taux d'erreurs, temps réponse
- [ ] **Build Docker final** : `docker build -t flight-search-api:v0.7.0 .`
- [ ] **Tests Docker** : `docker run -p 8000:8000 --env-file .env flight-search-api:v0.7.0`

**Décision release v1.0.0** :

- **Si v0.7.0 OK sans bugs** :
  - Tag v1.0.0 sur même commit que v0.7.0
  - GitHub Release v1.0.0 (workflow automatique)
  - Pas de nouveau commit nécessaire

- **Si bugs trouvés** :
  - Fix bugs → Commit → Nouveau tag v1.0.0
  - GitHub Release v1.0.0 (workflow automatique)

📝 **Output** : MVP Production Ready (v0.7.0) → MVP Release (v1.0.0)

---

## Releases & Milestones

### v0.5.0 - Epic 1: API Foundation

**Date cible** : TBD après Story 3

**Stories incluses** :
- Story 1: Health check endpoint (2 pts)
- Story 2: Configuration & Logging (3 pts)
- Story 3: Search endpoint basique mock (8 pts)

**Total** : 13 story points, ~49 tests

**Déployable** : ✅ API testable (mock data), contrat validé

**Valeur business** : Client peut tester API, feedback UX format JSON

**Process release** :
1. Toutes stories Epic 1 mergées sur develop ✅
2. Merge develop → master : `git checkout develop && git pull && git checkout master && git merge develop --ff-only`
3. Tag v0.5.0 : `git tag v0.5.0 && git push origin master --tags`
4. GitHub Release auto-créée via workflow release.yml
5. Marquer "Pre-release" (version dev <1.0.0)

---

### v0.6.0 - Epic 2: Google Flights Integration

**Date cible** : TBD après Story 6

**Stories incluses** :
- Story 4: Crawler + Parser (8 pts)
- Story 5: Multi-destinations (5 pts)
- Story 6: Proxies Decodo (5 pts)

**Total** : 18 story points, ~50 tests

**Déployable** : ✅ Vraies données multi-destinations, feature MVP complète

**Valeur business** : Recherche multi-city fonctionne, Top 10 vols

**Process release** :
1. Toutes stories Epic 2 mergées sur develop ✅
2. Merge develop → master
3. Tag v0.6.0 : `git tag v0.6.0 && git push origin master --tags`
4. GitHub Release auto-créée
5. Marquer "Pre-release"

---

### v0.7.0 - Epic 3: Production Ready

**Date cible** : TBD après Story 7

**Story incluse** :
- Story 7: Retry + Error handling (5 pts)

**Total** : 5 story points, ~15 tests

**Déployable** : ✅ Production-ready, robuste, SLA garantis

**Valeur business** : Retry automatique, logs détaillés, monitoring

**Process release** :
1. Story 7 mergée sur develop ✅
2. Merge develop → master
3. Tag v0.7.0 : `git tag v0.7.0 && git push origin master --tags`
4. GitHub Release auto-créée
5. Marquer "Pre-release"

---

### v1.0.0 - MVP Release (Production)

**Date cible** : TBD après validation complète v0.7.0

**Prérequis** :
- ✅ v0.7.0 mergé sur master
- ✅ Tests end-to-end complets (10+ recherches vraies clés Decodo)
- ✅ Démo client final (validation UX, performance)
- ✅ Validation business (feedback client, acceptation)

**Process release** :

**Cas 1 : v0.7.0 parfait (aucun bug trouvé)** :
1. Tag v1.0.0 sur **même commit** que v0.7.0 :
   ```bash
   git checkout master
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. GitHub Release auto-créée via workflow
3. Marquer "Latest release" (enlever Pre-release)
4. Pas de nouveau commit nécessaire

**Cas 2 : Bugs trouvés après v0.7.0** :
1. Créer branche hotfix : `git checkout -b hotfix/v1.0.0`
2. Fix bugs → Commits
3. PR hotfix → master
4. Merge hotfix sur master
5. Tag v1.0.0 sur nouveau commit :
   ```bash
   git checkout master
   git tag v1.0.0
   git push origin v1.0.0
   ```
6. GitHub Release auto-créée
7. Marquer "Latest release"

**Valeur business** : MVP validé en production, clients peuvent utiliser API

**Distinction versions** :
- **v0.x.x-xxx** : Dev releases (Pre-release GitHub)
- **v1.0.0** : Production release (Latest release GitHub)
- Détection auto dans workflow : `contains(github.ref, '-')`

---

## Phase 6 : Documentation finale & Release MVP

**Objectif** : README professionnel et release v1.0.0

**Branche** : `feature/documentation`

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

### 6.2 CHANGELOG v1.0.0
- [ ] Consolider toutes les entrées précédentes
- [ ] Créer section v1.0.0 avec features complètes
- [ ] Commit : `docs: release v1.0.0 changelog`

📝 **Output** : CHANGELOG.md complet

### 6.3 Release v1.0.0
- [ ] Push branche : `git push origin feature/documentation`
- [ ] Créer Pull Request sur GitHub : `feature/documentation` → `develop`
- [ ] (Manuel) Merger la PR sur GitHub
- [ ] Pull develop en local : `git checkout develop && git pull`
- [ ] Créer Pull Request sur GitHub : `develop` → `master` (Release v1.0.0)
- [ ] (Manuel) Merger la PR sur GitHub
- [ ] Pull master en local : `git checkout master && git pull`
- [ ] Tag : `git tag v1.0.0 && git push origin v1.0.0` (déclenche workflow release.yml)

📝 **Output** : Release v1.0.0 publique sur GitHub (automatique via workflow)

---

## Déploiement Dokploy

**Objectif** : Déployer MVP en production

### Déploiement
- [ ] Configurer Dokploy : connecter repo GitHub
- [ ] Ajouter env vars dans UI Dokploy :
      - LOG_LEVEL
      - DECODO_USERNAME
      - DECODO_PASSWORD
      - DECODO_PROXY_HOST
      - PROXY_ROTATION_ENABLED
      - CAPTCHA_DETECTION_ENABLED
- [ ] Déclencher build automatique (push sur master)
- [ ] Vérifier deployment : `curl https://ton-domaine.com/health`
- [ ] Tester endpoint complet avec n8n
- [ ] Monitorer logs : captcha rate, proxy costs, success rate

📝 **Output** : API MVP en production avec monitoring actif

---

## Phase 7 : Captcha Solving (Post-MVP - Optionnelle)

**Objectif** : Ajouter résolution automatique captchas **uniquement si monitoring Phase 6 montre trop de blocages**

**Pré-requis** : 
- ✅ MVP déployé et monitoring actif
- ✅ Logs captcha rate analysés sur 1-2 semaines minimum
- ✅ Décision data-driven basée sur métriques réelles

**Branche** : `feature/captcha-solving`

### 7.1 Analyse & décision
- [ ] Analyser logs monitoring : calculer taux de captcha (nombre captchas / nombre total requêtes) sur 1-2 semaines minimum
- [ ] Calculer impact business : % de recherches échouées à cause captchas
- [ ] Décider si 2Captcha nécessaire (seuil recommandé : >5% blocages)
- [ ] Si taux < 5%, STOP ici (pas besoin de Phase 7)
- [ ] Si taux ≥ 5%, continuer Phase 7
- [ ] Documenter décision dans ADR #007 : "2Captcha Integration Decision"

📝 **Output** : Décision documentée (GO ou NO-GO Phase 7)

### 7.2 Recherche 2Captcha
- [ ] Documentation 2Captcha : API, pricing, types captchas supportés
      → https://2captcha.com/2captcha-api
- [ ] Estimation coûts : nombre captchas/mois × $0.001-0.003
- [ ] Comparer avec coût des recherches perdues
- [ ] Valider ROI positif
- [ ] Créer `docs/references/2captcha.md` et mettre à jour l'index REFERENCES.md

### 7.3 Intégration 2Captcha
- [ ] Ajouter `2captcha-python` à pyproject.toml
- [ ] Créer `app/services/captcha_solver.py`
- [ ] Écrire tests `tests/unit/test_captcha_solver.py` (avec mocks)
- [ ] Modifier `CrawlerService` pour fallback 2Captcha si détection captcha
- [ ] Ajouter env vars :
      - TWOCAPTCHA_API_KEY
      - CAPTCHA_SOLVING_ENABLED (default: false)
- [ ] Mettre à jour `.env.example`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add 2captcha fallback for captcha solving`

### 7.4 Tests & validation
- [ ] Tests intégration avec mock 2Captcha
- [ ] Test complet local avec vraie clé 2Captcha
- [ ] Vérifier coûts réels par captcha résolu
- [ ] Vérifier temps résolution acceptable (<30s)
- [ ] Coverage >80%
- [ ] Commit : `test: add captcha solver integration tests`

### 7.5 Monitoring coûts
- [ ] Logger coûts 2Captcha par recherche
- [ ] Ajouter métriques Prometheus/Grafana :
      - Nombre captchas résolus/jour
      - Coût 2Captcha/jour
      - Taux de succès résolution
      - Temps moyen résolution
- [ ] Dashboard monitoring dédié
- [ ] Documentation ROI : coût captcha vs perte de données
- [ ] Commit : `feat(monitoring): add 2captcha cost tracking`

### 7.6 Documentation
- [ ] Mettre à jour README : section Captcha Solving
- [ ] Mettre à jour SPECS.md : stratégie captcha complète
- [ ] Ajouter ADR #007 dans ARCHITECTURE.md
- [ ] Commit : `docs: add captcha solving documentation`

### 7.7 Mise à jour CHANGELOG
- [ ] Ajouter entrée v1.1.0-captcha dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for captcha solving phase`

### 7.8 Release v1.1.0
- [ ] Push branche : `git push origin feature/captcha-solving`
- [ ] Créer Pull Request sur GitHub : `feature/captcha-solving` → `develop`
- [ ] (Manuel) Merger la PR sur GitHub
- [ ] Pull develop en local : `git checkout develop && git pull`
- [ ] Tests complets sur develop : `pytest -v && ruff check . && mypy app/`
- [ ] Créer Pull Request sur GitHub : `develop` → `master` (Release v1.1.0)
- [ ] (Manuel) Merger la PR sur GitHub
- [ ] Pull master en local : `git checkout master && git pull`
- [ ] Tag : `git tag v1.1.0 && git push origin v1.1.0` (déclenche workflow release.yml)

### 7.9 Déploiement
- [ ] Ajouter TWOCAPTCHA_API_KEY dans Dokploy
- [ ] Activer CAPTCHA_SOLVING_ENABLED=true
- [ ] Déployer v1.1.0
- [ ] Monitorer coûts et efficacité pendant 1 semaine
- [ ] Ajuster seuils si nécessaire

📝 **Output** : Captcha solving en production avec ROI positif

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
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── SPECS.md
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
    "pydantic>=2.10",
    "pydantic-settings>=2.0",
    "crawl4ai>=0.7",  # Inclut Playwright automatiquement
    "tenacity>=9.0",
    "uvicorn>=0.30",
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