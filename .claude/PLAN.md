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

## Phase 4 : Spécifications techniques détaillées

**Objectif** : Écrire les specs précises avant de coder

**Branche** : `feature/technical-specs`

### 4.1 Spécifications Models
- [ ] Specs SearchRequest (Flight, DateRange, validation)
- [ ] Specs SearchResponse (FlightResult, SearchStats)
- [ ] Liste tests unitaires
- [ ] Ajouter à `docs/SPECS.md`

### 4.2 Spécifications Configuration & Logging
- [ ] Specs Settings class (Pydantic Settings)
- [ ] Specs logger setup (JSON structuré)
- [ ] Liste tests
- [ ] Ajouter à `docs/SPECS.md`

### 4.3 Spécifications Services
- [ ] Specs CombinationGenerator (algorithme itertools.product)
- [ ] Specs ProxyService (Decodo config, rotation strategy, bandwidth monitoring)
- [ ] Specs CrawlerService (Crawl4AI setup, stealth mode, captcha detection, retry logic)
- [ ] Specs FlightParserService (JsonCssExtractionStrategy, parsing vols/prix/horaires)
- [ ] Specs SearchService (orchestration : CombinationGenerator → CrawlerService → FlightParser → Top 10 ranking)
- [ ] Liste tests pour chaque service
- [ ] Ajouter à `docs/SPECS.md`

### 4.4 Spécifications API Routes
- [ ] Specs endpoint POST /api/v1/search-flights
- [ ] Validation request (Pydantic)
- [ ] Error handling (400, 500, 207)
- [ ] Tests intégration (happy path + errors)
- [ ] Ajouter à `docs/SPECS.md`

### 4.5 Stratégie tests
- [ ] Liste complète tests unitaires par composant
- [ ] Scénarios tests intégration
- [ ] Mocks strategy (Crawl4AI, Decodo proxies, HTML responses Google Flights)
- [ ] Tests captcha detection et retry logic
- [ ] Tests proxy rotation et fallback
- [ ] Coverage target : 80%
- [ ] Ajouter à `docs/SPECS.md`

### 4.6 Finalisation SPECS.md
- [ ] Vérifier cohérence globale
- [ ] Commit : `docs: add detailed technical specifications`

📝 **Output** : `docs/SPECS.md` ultra-détaillé

### 4.7 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.4.0-planning dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for planning phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.4.0-planning sur master

---

## Phase 5 : Implémentation MVP (TDD)

**Objectif** : Développer tous les composants avec approche TDD (sans résolution captcha)

**Branche** : `feature/implementation`

### 5.1 Models (Pydantic)
- [ ] **RAPPEL : Réactiver step "Tests with coverage" dans `.github/workflows/ci.yml`** (décommenter lignes 46-47)
- [ ] Écrire tests `tests/unit/test_models.py`
- [ ] Implémenter `app/models/request.py`
- [ ] Implémenter `app/models/response.py`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(models): add pydantic models with validation`

### 5.2 Configuration & Logging
- [ ] Écrire tests `tests/unit/test_config.py`
- [ ] Implémenter `app/core/config.py`
- [ ] Implémenter `app/core/logger.py`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(core): add config and structured logging`

### 5.3 CombinationGenerator
- [ ] Écrire tests `tests/unit/test_combination_generator.py`
- [ ] Implémenter `app/services/combination_generator.py`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add combination generator`

### 5.4 ProxyService
- [ ] Écrire tests `tests/unit/test_proxy_service.py`
- [ ] Implémenter `app/services/proxy_service.py` (Decodo config, rotation)
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add proxy service with Decodo integration`

### 5.5 CrawlerService + Captcha Detection
- [ ] Écrire tests `tests/unit/test_crawler_service.py` (avec mocks Crawl4AI)
- [ ] Implémenter `app/services/crawler_service.py` (retry avec tenacity)
- [ ] Implémenter détection captcha (logger uniquement, pas de résolution)
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add crawler service with captcha detection`

### 5.6 FlightParserService
- [ ] Écrire tests `tests/unit/test_flight_parser.py` (avec HTML fixtures)
- [ ] Implémenter `app/services/flight_parser.py` (JsonCssExtractionStrategy)
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add flight parser service`

### 5.7 SearchService
- [ ] Écrire tests `tests/unit/test_search_service.py`
- [ ] Implémenter `app/services/search_service.py`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(services): add search orchestration service`

### 5.8 API Routes
- [ ] Écrire tests `tests/integration/test_api_routes.py`
- [ ] Implémenter `app/api/routes.py`
- [ ] Intégrer dans `app/main.py`
- [ ] Vérifier tests passent
- [ ] Commit : `feat(api): add search endpoint`

### 5.9 Tests coverage
- [ ] Lancer `pytest --cov=app --cov-report=html`
- [ ] Vérifier >80% coverage
- [ ] Ajouter tests si nécessaire
- [ ] Commit : `test: ensure 80% coverage`

### 5.10 Vérifications finales
- [ ] Lint : `ruff check . && ruff format .`
- [ ] Type check : `mypy app/`
- [ ] Tests : `pytest -v`
- [ ] Build Docker : `docker build -t flight-search-api .`
- [ ] Test complet local avec vraie clé Decodo (1-2 recherches test)
- [ ] Vérifier logs : captcha detection, proxy rotation, parsing success
- [ ] Commit : `chore: final verifications before release`

### 5.11 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.5.0-mvp dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for MVP implementation`

📝 **Output** : API MVP complète et testée (sans résolution captcha)

**Fin de phase** : Push branche → PR → Merge develop → Merge develop→master → Tag v0.5.0-mvp sur master

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