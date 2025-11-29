# 🎯 One-Liner

API FastAPI scraping Google Flights multi-destinations. Python 3.13+, Crawl4AI + Playwright, proxy résidentiels, Top 10 résultats en mémoire (pas de DB).

---

# 🔥 MUST DO (Règles Critiques)

- **NEVER** commit `.env` → Secrets dans Dokploy UI prod uniquement
- **ALWAYS** run pre-commit avant push : `uv run ruff check . --fix && uv run ruff format . && uv run mypy app/ && uv run pytest tests/unit/`
- **NEVER** add inline comments → Code self-explanatory (noms explicites, types, docstrings)
- **ALWAYS** use `async with AsyncWebCrawler(timeout=10)` → Default 30s trop long
- **CRITICAL** : Type hints ALL functions (PEP 695 style : `list[T]`, `X | None`)
- **CRITICAL** : Coverage ≥ 80% → CI bloque si inférieur
- **CRITICAL** : Use `HTTPStatus` enum (never magic numbers) → `HTTPStatus.SERVICE_UNAVAILABLE` pas `503`
- **NEVER** import from modules internes → Toujours via `__init__.py`
- **ALWAYS** TDD cycle → Red (test fails) → Green (minimal code) → Refactor

---

# ⚠️ Gotchas (Pièges Projet-Spécifiques)

- **Proxy rotation** → Fonctionne UNIQUEMENT si `PROXY_ROTATION_ENABLED=true` dans `.env`
- **Type ignore** → MUST have comment : `# type: ignore[error-code]  # reason`
- **Tests** → MUST use fixtures from `tests/fixtures/` (DRY principe)
- **Pydantic models** → ALWAYS add `model_config = ConfigDict(extra="forbid")`
- **Logging** → ALWAYS include context : `logger.info("msg", extra={"search_id": id})`
- **Circular imports** → Use `TYPE_CHECKING` block
- **Playwright + reload** → Auto-reload (`--reload`) incompatible avec Playwright sur certains OS → Use `uvicorn` sans reload

---

# 📚 Documentation Complète

**Architecture & WHY** : [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- 6 ADRs complets (Crawl4AI vs SerpAPI, Decodo vs Oxylabs, Top 10 mémoire, Tenacity, Captcha MVP, CSS vs LLM)
- Diagrammes Mermaid (composants, séquence)
- Flow de données end-to-end

**Standards & HOW** : [docs/CODING_STANDARDS.md](../docs/CODING_STANDARDS.md)
- Python (PEP 695, imports via `__init__.py`, docstrings, async patterns)
- Tooling (Ruff, Mypy strict, structured logging JSON)
- Tests (TDD strategy, fixtures, AAA/BDD patterns, configuration pytest)
- Git (branches, conventional commits, pre-commit checks)
- Docker (multi-stage, best practices)

**Références Techniques** : [docs/REFERENCES.md](../docs/REFERENCES.md) → [docs/references/](../docs/references/)
- FastAPI, Pydantic v2, Crawl4AI, Tenacity, Decodo Proxies
- Anti-detection, Captcha detection, Google Flights URL, Kayak
- GitHub Actions, Dokploy deployment

**Versions & Compatibilité** : [docs/VERSIONS.md](../docs/VERSIONS.md)
- Matrice compatibilité Python 3.13 + dépendances
- Migration Pydantic v1→v2 (breaking changes)

**Specs & Stories** : [docs/SPECS.md](../docs/SPECS.md) → [docs/specs/](../docs/specs/)
- 4 Epics, 10 Stories détaillées avec tests TDD

---

# ⚡ Commandes Essentielles

**Setup** : `uv sync --all-extras && uv run crawl4ai-setup`
**Dev** : `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
**Pre-commit** : `uv run ruff check . --fix && uv run ruff format . && uv run mypy app/ && uv run pytest tests/unit/`
**Tests** : `uv run pytest tests/unit/ -v` | `uv run pytest --cov=app --cov-report=html`
**Docker** : `docker build -t flight-search-api . && docker run -p 8001:8000 --env-file .env flight-search-api`

→ Sécurité & Secrets : [docs/CODING_STANDARDS.md](../docs/CODING_STANDARDS.md) §6