# Plan d'action complet - flight-search-api

## Phase 0 : Setup Documentation & Git

**Objectif** : Initialiser la structure documentation (Git déjà connecté)

**Prérequis (DÉJÀ FAIT)** :
- ✅ Repo GitHub créé et cloné
- ✅ Remote configuré
- ✅ Créer dossier .claude (où figure le plan)

### 0.1 Structure documentation vide
- [ ] Créer `docs/`
- [ ] Créer `.claude/CLAUDE.md`
- [ ] Créer `docs/architecture.md`
- [ ] Créer `docs/PLANNING.md`
- [ ] Créer `docs/REFERENCES.md`
- [ ] Créer `docs/VERSIONS.md`
- [ ] Créer `docs/CHANGELOG.md`
- [ ] Commit : `docs: create documentation structure`
- [ ] Push main et créer branche develop

📝 **Output** : Structure docs prête à remplir

---

## Phase 1 : Recherche & Documentation

**Objectif** : Construire la base de connaissance avant tout dev

**Branche** : `feature/research-stack`

### 1.1 Recherche versions & compatibilité
- [ ] Python 3.13 stabilité et compatibilité écosystème
- [ ] FastAPI 0.121.2 (breaking changes, Pydantic v2)
- [ ] Pydantic v2.10+ (migration depuis v1)
- [ ] tenacity 9.0+ (retry strategies)
- [ ] crawl4ai 0.7+ (async crawler, stealth mode, Playwright intégré)
- [ ] Vérification matrice compatibilité croisée
- [ ] Créer `docs/VERSIONS.md` avec tableau + notes
- [ ] Commit : `docs: add versions compatibility matrix`

📝 **Output** : `docs/VERSIONS.md`

**Note** : Playwright est installé automatiquement par `crawl4ai-setup`, pas besoin de l'installer séparément.

### 1.2 Documentation technique ciblée
- [ ] FastAPI : Dependency Injection, async routes, TestClient
      → https://fastapi.tiangolo.com/
- [ ] Pydantic v2 : Settings, validation, field_validator
      → https://docs.pydantic.dev/latest/
- [ ] Crawl4AI : AsyncWebCrawler, BrowserConfig, JsonCssExtractionStrategy (extraction CSS)
      → https://docs.crawl4ai.com/
- [ ] Decodo Proxies : Residential rotation, France targeting, authentication, bandwidth optimization
      → https://help.decodo.com/docs/introduction
        **Note** : Format auth = username: customer-{api_key}-country-FR, password: your_password
- [ ] Google Flights URL structure : Multi-city params, date formats, currency/locale (France)
      → (reverse engineering via browser DevTools)
- [ ] Anti-détection : Stealth mode Crawl4AI, user-agent rotation, proxy rotation
      → https://docs.crawl4ai.com/core/browser-config/
- [ ] Captcha detection : Patterns HTML (reCAPTCHA, hCaptcha), retry strategy avec rotation IP
      → (patterns de détection, pas de résolution dans MVP)
- [ ] Tenacity : @retry decorator, wait strategies, async
      → https://tenacity.readthedocs.io/
- [ ] Dokploy : Dockerfile best practices, env vars
      → https://docs.dokploy.com/
- [ ] Créer `docs/REFERENCES.md` avec extraits + liens
- [ ] Commit : `docs: add technical references`

📝 **Output** : `docs/REFERENCES.md`

**Note** : Si features additionnelles nécessaires pendant l'implémentation, les documenter dans un ADR et mettre à jour REFERENCES.md.

### 1.3 Standards Python modernes
- [ ] Python 3.13 type hints (PEP 695)
- [ ] Ruff configuration (rules, pyproject.toml)
- [ ] Mypy strict mode
- [ ] Async patterns (crawl4ai, error handling)
- [ ] Structured logging (JSON, contexte)
- [ ] Docstrings pragmatiques (PEP 257 : 1 ligne par défaut)
- [ ] Compléter `.claude/CLAUDE.md` - Section Standards
- [ ] Ajouter règle anti-pattern : commentaires inline interdits
- [ ] Commit : `docs: add Python standards to CLAUDE.md`

📝 **Output** : `.claude/CLAUDE.md` - Section Standards

### 1.4 Architecture & Décisions (ADR)
- [ ] Créer diagrammes (composants, séquence)
- [ ] Documenter flow de données (Requête HTTP → Services internes → Response JSON)
- [ ] Rédiger ADR #001 : Crawl4AI+Proxies vs SerpAPI (coût, flexibilité, maintenance)
- [ ] Rédiger ADR #002 : Decodo vs Oxylabs (prix, pool IP, France targeting)
- [ ] Rédiger ADR #003 : Top 10 en mémoire (pas de DB)
- [ ] Rédiger ADR #004 : Tenacity pour retry
- [ ] Rédiger ADR #005 : Captcha handling strategy (proxies rotation + detection, pas de résolution dans MVP)
- [ ] Rédiger ADR #006 : JsonCssExtractionStrategy vs LLMExtractionStrategy (coût, performance)
- [ ] Créer `docs/architecture.md` avec ADR intégrés
- [ ] Commit : `docs: add architecture and ADR`

📝 **Output** : `docs/architecture.md`

### 1.5 Conventions Git
- [ ] Documenter stratégie branches (main/develop/feature)
- [ ] Documenter Conventional Commits (feat, fix, docs, etc.)
- [ ] Documenter pre-commit checks (ruff, mypy, pytest)
- [ ] Documenter workflow développement
- [ ] Compléter `.claude/CLAUDE.md` - Section Git
- [ ] Commit : `docs: add git conventions to CLAUDE.md`

📝 **Output** : `.claude/CLAUDE.md` - Section Git

### 1.6 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.1.0-research dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for research phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

### 1.7 Merge recherche
- [ ] Merger `feature/research-stack` dans `develop`
- [ ] Tag `v0.1.0-research`
- [ ] Push develop + tags

---

## Phase 2 : Architecture & Squelette

**Objectif** : Créer la structure complète du projet

**Branche** : `feature/project-structure`

### 2.1 Création structure complète
- [ ] Créer fichiers racine : `README.md`, `.gitignore`, `.dockerignore`, `Dockerfile`, `pyproject.toml`, `.env.example`
- [ ] Créer structure `app/` avec tous dossiers et fichiers
- [ ] Créer structure `tests/` avec unit/ et integration/
- [ ] Ajouter docstrings TODO dans tous fichiers Python
- [ ] Commit : `chore: create project structure skeleton`

📝 **Output** : Arborescence complète avec fichiers vides + TODO

### 2.2 Configuration fichiers système
- [ ] Remplir `.gitignore` (Python, tests, IDEs, env, Docker, OS)
- [ ] Remplir `.dockerignore`
- [ ] Créer `.env.example` avec variables :
      - LOG_LEVEL=INFO
      - DECODO_USERNAME=customer-XXXX-country-FR
      - DECODO_PASSWORD=your_password
      - DECODO_PROXY_HOST=pr.decodo.com:8080
      - PROXY_ROTATION_ENABLED=true
      - CAPTCHA_DETECTION_ENABLED=true
- [ ] Commit : `chore: add system configuration files`

📝 **Output** : Fichiers config système prêts

### 2.3 Compléter CLAUDE.md
- [ ] Vérifier section Contexte projet
- [ ] Vérifier section Standards (déjà fait Phase 1.3)
- [ ] Ajouter section Organisation fichiers (arborescence)
- [ ] Vérifier section Anti-patterns
- [ ] Vérifier section Git (déjà fait Phase 1.5)
- [ ] Ajouter section Workflow développement
- [ ] Ajouter section Tests (pytest commands)
- [ ] Ajouter section Docker (build/run)
- [ ] Commit si modifs : `docs: finalize CLAUDE.md`

📝 **Output** : `.claude/CLAUDE.md` complet

### 2.4 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.2.0-structure dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for structure phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

### 2.5 Merge structure
- [ ] Merger `feature/project-structure` dans `develop`
- [ ] Tag `v0.2.0-structure`
- [ ] Push develop + tags

---

## Phase 3 : Configuration & Build

**Objectif** : Projet runnable avec config minimale

**Branche** : `feature/config-build`

### 3.1 pyproject.toml complet
- [ ] Section [project] : metadata + dependencies (fastapi, pydantic, crawl4ai, tenacity)
- [ ] Section [project.optional-dependencies] : dev tools
- [ ] Section [tool.ruff] : linting rules + formatting
- [ ] Section [tool.mypy] : strict mode + overrides
- [ ] Section [tool.pytest.ini_options] : test config + coverage
- [ ] Commit : `chore(config): add complete pyproject.toml`

📝 **Output** : `pyproject.toml` complet

### 3.2 Dockerfile multi-stage optimisé
- [ ] Stage 1 Builder : install uv + dependencies + crawl4ai-setup
      **Note** : crawl4ai-setup installe automatiquement Playwright + dépendances système
- [ ] Stage 2 Runtime : copy deps + code, non-root user, healthcheck
- [ ] Optimisé pour Dokploy
- [ ] Commit : `chore(docker): add optimized Dockerfile`

📝 **Output** : `Dockerfile` production-ready

### 3.3 App minimale + health endpoint
- [ ] Implémenter `app/main.py` : FastAPI app basique
- [ ] Implémenter endpoint GET `/health` → `{"status": "ok"}`
- [ ] Implémenter `tests/integration/test_health.py`
- [ ] Commit : `feat(api): add minimal app with health endpoint`

📝 **Output** : App minimale testable

### 3.4 Vérifications locales
- [ ] Install deps : `uv sync --all-extras`
- [ ] Run post-install : `crawl4ai-setup` (installe Playwright)
- [ ] Run app : `fastapi dev app/main.py`
- [ ] Test health : `curl http://localhost:8000/health`
- [ ] Run tests : `pytest -v`
- [ ] Lint : `ruff check . && ruff format . --check`
- [ ] Type check : `mypy app/`
- [ ] Build Docker : `docker build -t flight-search-api .`
- [ ] Run Docker : `docker run -p 8000:8000 flight-search-api`
- [ ] Test Docker health : `curl http://localhost:8000/health`
- [ ] Commit : `chore: verify local and docker builds`

📝 **Output** : Vérification que tout fonctionne

### 3.5 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.3.0-build dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for build phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

### 3.6 Merge config
- [ ] Merger `feature/config-build` dans `develop`
- [ ] Tag `v0.3.0-build`
- [ ] Push develop + tags

---

## Phase 4 : Planning détaillé développement

**Objectif** : Écrire les specs précises avant de coder

**Branche** : `feature/planning-specs`

### 4.1 Spécifications Models
- [ ] Specs SearchRequest (Flight, DateRange, validation)
- [ ] Specs SearchResponse (FlightResult, SearchStats)
- [ ] Liste tests unitaires
- [ ] Ajouter à `docs/PLANNING.md`

### 4.2 Spécifications Configuration & Logging
- [ ] Specs Settings class (Pydantic Settings)
- [ ] Specs logger setup (JSON structuré)
- [ ] Liste tests
- [ ] Ajouter à `docs/PLANNING.md`

### 4.3 Spécifications Services
- [ ] Specs CombinationGenerator (algorithme itertools.product)
- [ ] Specs ProxyService (Decodo config, rotation strategy, bandwidth monitoring)
- [ ] Specs CrawlerService (Crawl4AI setup, stealth mode, captcha detection, retry logic)
- [ ] Specs FlightParserService (JsonCssExtractionStrategy, parsing vols/prix/horaires)
- [ ] Specs SearchService (orchestration : CombinationGenerator → CrawlerService → FlightParser → Top 10 ranking)
- [ ] Liste tests pour chaque service
- [ ] Ajouter à `docs/PLANNING.md`

### 4.4 Spécifications API Routes
- [ ] Specs endpoint POST /api/v1/search-flights
- [ ] Validation request (Pydantic)
- [ ] Error handling (400, 500, 207)
- [ ] Tests intégration (happy path + errors)
- [ ] Ajouter à `docs/PLANNING.md`

### 4.5 Stratégie tests
- [ ] Liste complète tests unitaires par composant
- [ ] Scénarios tests intégration
- [ ] Mocks strategy (Crawl4AI, Decodo proxies, HTML responses Google Flights)
- [ ] Tests captcha detection et retry logic
- [ ] Tests proxy rotation et fallback
- [ ] Coverage target : 80%
- [ ] Ajouter à `docs/PLANNING.md`

### 4.6 Finalisation PLANNING.md
- [ ] Vérifier cohérence globale
- [ ] Commit : `docs: add detailed development planning`

📝 **Output** : `docs/PLANNING.md` ultra-détaillé

### 4.7 Mise à jour CHANGELOG
- [ ] Ajouter entrée v0.4.0-planning dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for planning phase`

📝 **Output** : `docs/CHANGELOG.md` mis à jour

### 4.8 Merge planning
- [ ] Merger `feature/planning-specs` dans `develop`
- [ ] Tag `v0.4.0-planning`
- [ ] Push develop + tags

---

## Phase 5 : Implémentation MVP (TDD)

**Objectif** : Développer tous les composants avec approche TDD (sans résolution captcha)

**Branche** : `feature/implementation`

### 5.1 Models (Pydantic)
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

### 5.12 Merge implementation
- [ ] Merger `feature/implementation` dans `develop`
- [ ] Tag `v0.5.0-mvp`
- [ ] Push develop + tags

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

### 6.3 Merge documentation
- [ ] Merger `feature/documentation` dans `develop`
- [ ] Merger `develop` dans `main`
- [ ] Tag `v1.0.0`
- [ ] Push main + develop + tags

### 6.4 Release GitHub
- [ ] Créer release sur GitHub avec tag v1.0.0
- [ ] Copier CHANGELOG v1.0.0 dans release notes

📝 **Output** : Release v1.0.0 publique (MVP sans résolution captcha)

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
- [ ] Déclencher build automatique (push sur main)
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
- [ ] Ajouter à `docs/REFERENCES.md`

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
- [ ] Mettre à jour PLANNING.md : stratégie captcha complète
- [ ] Ajouter ADR #007 dans architecture.md
- [ ] Commit : `docs: add captcha solving documentation`

### 7.7 Mise à jour CHANGELOG
- [ ] Ajouter entrée v1.1.0-captcha dans `docs/CHANGELOG.md`
- [ ] Commit : `docs: update changelog for captcha solving phase`

### 7.8 Merge & release
- [ ] Merger `feature/captcha-solving` dans `develop`
- [ ] Tests complets sur develop
- [ ] Merger `develop` dans `main`
- [ ] Tag `v1.1.0`
- [ ] Push main + develop + tags
- [ ] Release GitHub v1.1.0

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
- Merger dans develop
- Release : develop → main avec tag

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
│   ├── CLAUDE.md      # Standards, conventions
│   └── PLAN.md        # Ce plan
├── docs/
│   ├── architecture.md
│   ├── PLANNING.md
│   ├── REFERENCES.md
│   ├── VERSIONS.md
│   └── CHANGELOG.md
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   │   ├── request.py
│   │   └── response.py
│   ├── services/
│   │   ├── combination_generator.py
│   │   ├── proxy_service.py
│   │   ├── crawler_service.py
│   │   ├── flight_parser.py
│   │   ├── search_service.py
│   │   └── (captcha_solver.py - Phase 7 optionnelle)
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── utils/
│   └── main.py
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_config.py
│   │   ├── test_combination_generator.py
│   │   ├── test_proxy_service.py
│   │   ├── test_crawler_service.py
│   │   ├── test_flight_parser.py
│   │   ├── test_search_service.py
│   │   └── (test_captcha_solver.py - Phase 7)
│   └── integration/
│       ├── test_health.py
│       └── test_api_routes.py
├── Dockerfile
├── pyproject.toml
├── .env.example
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