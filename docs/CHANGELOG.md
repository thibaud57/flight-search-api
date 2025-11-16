# CHANGELOG - flight-search-api

**Dernière mise à jour** : 16/11/2025

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

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
