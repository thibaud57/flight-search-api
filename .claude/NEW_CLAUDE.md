# flight-search-api — Quick Reference

## 🎯 One-Liner

API FastAPI scraping Google Flights multi-destinations. Python 3.13+, Crawl4AI + Playwright, proxy résidentiels, Top 10 résultats en mémoire (pas de DB).

---

## 🔥 MUST DO (Règles Critiques)

- **NEVER** commit `.env` → Secrets dans Dokploy UI prod uniquement
- **ALWAYS** run pre-commit avant push : `ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/`
- **NEVER** add inline comments → Code self-explanatory (noms explicites, types, docstrings)
- **ALWAYS** use `async with AsyncWebCrawler(timeout=10)` → Default 30s trop long
- **CRITICAL** : Type hints ALL functions (PEP 695 style : `list[T]`, `X | None`)
- **CRITICAL** : Coverage ≥ 80% → CI bloque si inférieur
- **NEVER** import from modules internes → Toujours via `__init__.py`
- **ALWAYS** TDD cycle → Red (test fails) → Green (minimal code) → Refactor

---

## 🛠️ Setup Initial

```bash
# Installation
uv sync --all-extras
uv run crawl4ai-setup

# Configuration
cp .env.example .env  # Remplir PROXY_USERNAME, PROXY_PASSWORD, LOG_LEVEL

# Vérification
ruff check . && mypy app/ && pytest tests/unit/
```

---

## 🚀 Commandes Quotidiennes

### Développement
```bash
fastapi dev app/main.py    # Hot-reload dev server
```

### Quality Checks (Pre-commit obligatoire)
```bash
ruff check . --fix && ruff format . && mypy app/ && pytest tests/unit/
```

### Tests
```bash
pytest tests/unit/ -v                  # Tests unitaires (rapides)
pytest tests/integration/ -v           # Tests intégration (TestClient)
pytest --cov=app --cov-report=html     # Coverage interactif
pytest -x                              # Stop au 1er échec
pytest -k "pattern"                    # Filtre par nom
```

### Docker
```bash
docker build -t flight-search-api .
docker run -p 8001:8000 --env-file .env flight-search-api

# Background
docker run -d -p 8001:8000 --name flight-api flight-search-api
docker logs -f flight-api
```

---

## 📂 Structure Projet

```
app/
  ├── api/           # Routes FastAPI
  ├── core/          # Config (Pydantic Settings) + Logger (JSON structuré)
  ├── models/        # Schémas Pydantic (request.py, response.py)
  ├── services/      # Logique métier (crawler, parser, search, proxy)
  ├── utils/         # Helpers réutilisables
  └── main.py        # Entry point

tests/               # Structure miroir app/
  ├── unit/          # Tests isolés avec mocks (coverage ≥80%)
  ├── integration/   # Tests end-to-end (TestClient FastAPI)
  └── fixtures/      # Factories + Mocks + Helpers (DRY)

docs/
  ├── references/    # Docs techniques modulaires (10 fichiers)
  ├── CODING_STANDARDS.md    # Standards détaillés (conventions, anti-patterns)
  └── ARCHITECTURE.md        # Architecture + ADR

.claude/
  ├── CLAUDE.md      # Ce fichier (quick ref + living doc)
  └── PLAN.md        # Plan d'action détaillé projet
```

---

## 📝 Workflow Feature (TDD)

1. **Branche** : `git checkout develop && git pull && git checkout -b feature/nom-descriptif`
2. **TDD Loop** (pour chaque composant) :
   - Écrire tests unitaires → FAIL (red)
   - Implémenter code minimal → PASS (green)
   - Refactor si nécessaire
3. **Intégration** : `pytest tests/integration/test_nouvelle_route.py -v`
4. **Quality** : `ruff check . --fix && ruff format . && mypy app/ && pytest -v`
5. **Commit** : `git add . && git commit -m "feat(scope): description"`
6. **PR** : `git push -u origin feature/nom` → Créer PR GitHub → CI passe → Merge
7. **Cleanup** : `git checkout develop && git pull && git branch -d feature/nom`

---

## ⚠️ Gotchas (Pièges Non-Évidents)

- **Crawl4AI timeout default = 30s** → ALWAYS set `timeout=10` explicitement
- **Proxy rotation** → Fonctionne UNIQUEMENT si `PROXY_ROTATION_ENABLED=true` dans `.env`
- **Type ignore** → MUST have comment : `# type: ignore[error-code]  # reason`
- **Tests** → MUST use fixtures from `tests/fixtures/` (DRY principe)
- **Pydantic models** → ALWAYS add `model_config = ConfigDict(extra="forbid")`
- **Logging** → ALWAYS include context : `logger.info("msg", extra={"search_id": id})`
- **Circular imports** → Use `TYPE_CHECKING` block (voir CODING_STANDARDS.md §3.2)

---

## 🏗️ Décisions Architecturales (WHY?)

- **Pourquoi pas de DB ?** → Top 10 résultats fit en mémoire. DB = latence + complexité inutile pour MVP.
- **Pourquoi CSS extraction seulement ?** → Pas de LLM = parsing rapide + déterministe + coût réduit
- **Pourquoi Crawl4AI + Playwright ?** → Playwright intégré, async natif, stealth headers inclus
- **Pourquoi PEP 695 + strict mypy ?** → Type checking moderne catch bugs à dev time vs runtime
- **Pourquoi TDD obligatoire ?** → Coverage ≥80% garantit, tests = documentation vivante
- **Pourquoi structured JSON logging ?** → Contexte métier (search_id, destinations, proxy) traçable en prod

---

## 🔗 Références Détaillées

**Standards & Conventions** :
- Coding standards complets → `docs/CODING_STANDARDS.md` (PEP 695, imports, docstrings, async, tests, git)
- Architecture + ADR → `docs/ARCHITECTURE.md`

**Documentation Technique Modulaire** :
- FastAPI + Pydantic v2 → `docs/references/fastapi.md`, `pydantic-v2.md`
- Crawl4AI + Async patterns → `docs/references/crawl4ai.md`, `tenacity.md`
- Docker + Dokploy → `docs/references/dokploy.md`

**Accès rapide** : Voir `docs/REFERENCES.md` (index complet)

---

## 🐞 Troubleshooting Rapide

| Problème | Solution |
|----------|----------|
| `ModuleNotFoundError` | `uv sync --all-extras` |
| `crawl4ai-setup` échoue | Vérifier internet + espace disque (~500MB) |
| Mypy erreur lib externe | Ajouter `ignore_missing_imports = true` dans `pyproject.toml` |
| Docker build lent | Utiliser `--cache-from` |
| Tests échouent après pull | `uv sync` puis `pytest --cache-clear` |

---

## 📝 Living Document — Évolution

_Cette section documente l'évolution progressive du projet (pattern # Anthropic)_

### Baseline (Phase 0-3)
- Architecture de base
- Stack technique (Python 3.13, FastAPI, Crawl4AI)
- Pre-commit checks standard
- TDD workflow

### Ajouts Itératifs

_Format : `# It. N : "Règle découverte" (contexte/problème résolu)_

**Ajouter ici vos découvertes au fil du développement avec `#` :**

Exemples :
```
# It. 5 : "Toujours fixer timeout=10 pour Crawl4AI" (découvert: hangs sur Google Flights)
# It. 8 : "Proxy rotation logs debug avec extra={}" (découvert: 403 silencieux)
# It. 12 : "MyPy strict sur app/ uniquement, relax sur tests/" (découvert: complexité fixtures)
```

---

**Version** : 1.0 (Baseline optimisée)
**Dernière mise à jour** : 2025-01-28
