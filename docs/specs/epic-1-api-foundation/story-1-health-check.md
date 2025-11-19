---
title: "Story 1: Health check endpoint"
epic: "Epic 1: API Foundation"
story_points: 2
dependencies: []
date: "2025-19-11"
keywords: ["api", "health", "monitoring", "fastapi", "production", "devops", "docker", "dokploy"]
scope: ["specs"]
technologies: ["FastAPI", "Pydantic", "pytest", "TestClient", "Docker"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **DevOps & SRE** : Vérifier disponibilité de l'API avant routage traffic production (load balancers, reverse proxies)
- **Outils Monitoring** : Intégration avec systèmes d'observabilité (Prometheus, Grafana, Datadog) pour alerting automatique
- **Orchestrateurs** : Compatible Docker HEALTHCHECK et Dokploy health checks pour redémarrage automatique containers défaillants
- **CI/CD Pipelines** : Validation déploiement réussi post-release (smoke tests automatiques)

## Contraintes métier

- **Performance critique** : Response time < 100ms (p99) pour éviter faux positifs timeouts dans monitoring
- **Disponibilité 24/7** : Endpoint doit rester accessible même si dépendances externes (Decodo, Google Flights) sont down
- **Zéro dépendances externes** : Ne doit PAS tester connectivité DB/API externes (risque cascade failures)
- **Compatibilité Docker/Dokploy** : Format response compatible HEALTHCHECK Dockerfile et Dokploy health checks HTTP

## Valeur business

- ✅ **Production-ready foundation** : Première pierre pour déploiement Dokploy avec monitoring intégré
- ✅ **Validation déploiement automatique** : CI/CD peut vérifier succès release sans intervention manuelle
- ✅ **Feedback rapide incidents** : Détection downtime < 30s via alerting automatique (vs detection manuelle ~5-10min)
- ✅ **Foundation endpoints métier** : Dérisque architecture API avant développement endpoints complexes (search flights)
- ✅ **Confiance stakeholders** : Démontre maturité infrastructure dès Phase 1 (observabilité, reliability)

## Métriques succès

- **Response time p95** : < 50ms (target ambitieux, acceptable jusqu'à 100ms)
- **Uptime** : 99.9% si application running (downtime uniquement si app crash)
- **Taux réussite health checks** : 100% en conditions normales (0% false negatives)
- **Adoption CI/CD** : Intégration dans 100% des workflows déploiement (GitHub Actions, Dokploy HEALTHCHECK)

---

# 📋 Spécifications Techniques

## 1. Route Health Check

**Rôle** : Exposer endpoint HTTP simple retournant statut santé de l'application.

**Interface** :

```python
def health_check() -> HealthResponse:
    """Retourne le statut santé de l'application."""
```

**Configuration route** :
- Décorateur : GET sur endpoint `/health`
- Response model : `HealthResponse`
- Status code par défaut : `200`

**Response Model** :

```python
class HealthResponse(BaseModel):
    """Schéma response endpoint health check."""

    status: Literal["ok", "error"]
```

**Champs Response** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `status` | `Literal["ok", "error"]` | Statut santé application | Valeur `"ok"` si app running, `"error"` si anomalie détectée |

**Comportement** :

- **Nominal** : Retourner `{"status": "ok"}` avec status code `200 OK` si application opérationnelle
- **Edge case** : Pas de side-effects (aucun appel externe, aucune modification état)
- **Erreurs** : Ne doit PAS lever d'exception (pas de 500 Internal Server Error)
- **Performance** : Réponse < 100ms (pas de calcul complexe, juste return static JSON)

**Type hints** :

- ✅ Type hints PEP 695 : `def health_check() -> HealthResponse:`
- ✅ Literal type pour status : `Literal["ok", "error"]` (type safety strict)
- ✅ Pydantic BaseModel pour validation automatique response

**Contraintes techniques** :

- **Endpoint synchrone** : Utiliser `def` (pas `async def`) car pas d'I/O externe selon CLAUDE.md
- **Pas de dépendances** : Pas de Depends() FastAPI (route autonome)
- **Stateless** : Aucun état partagé, pas de cache, pas de session
- **Idempotence** : GET multiples retournent résultat identique (safe HTTP method)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### Route Health Check (4 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_health_check_returns_ok_status` | Appel endpoint health retourne status ok | GET `/health` | `{"status": "ok"}` | Vérifie comportement nominal : app running → status ok |
| 2 | `test_health_check_returns_200_status_code` | Appel endpoint health retourne status code 200 | GET `/health` | Status code `200` | Vérifie conformité HTTP : succès → 200 OK |
| 3 | `test_health_check_response_matches_schema` | Response conforme schéma Pydantic HealthResponse | GET `/health` | Response validée par `HealthResponse` | Vérifie type safety : champ status existe et est Literal["ok", "error"] |
| 4 | `test_health_check_response_time_fast` | Response time < 100ms | GET `/health` (10 appels) | Temps moyen < 100ms | Vérifie contrainte performance : endpoint ultra-rapide sans calcul |

**Total tests unitaires** : 4 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**Format tableau descriptif** (5 colonnes) :

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_health_endpoint_accessible` | Application FastAPI running avec TestClient | GET `/health` | Status code 200 + JSON response `{"status": "ok"}` |
| 2 | `test_health_response_content_type_json` | TestClient configuré | GET `/health` | Header `Content-Type: application/json` présent dans response |
| 3 | `test_health_endpoint_no_authentication_required` | TestClient sans headers auth | GET `/health` sans authentification | Status code 200 (endpoint public, pas de 401 Unauthorized) |
| 4 | `test_health_docker_healthcheck_compatible` | Application running en mode Docker | Docker HEALTHCHECK exécute `curl http://localhost:8000/health` | Exit code 0 (healthy) si status ok, exit code 1 (unhealthy) si error |

**Total tests intégration** : 4 tests

**Total tests Story 1** : 4 tests unitaires + 4 tests intégration = **8 tests**

---

## Exemples JSON

**Exemple 1 : Response succès (nominal)**

```json
{
  "status": "ok"
}
```

**Exemple 2 : Response error (si applicable - Phase 7+ avec checks avancés)**

```json
{
  "status": "error"
}
```

---

# 🐳 Configuration Production

## Docker HEALTHCHECK

Le endpoint `/health` doit retourner :
- **Status code 200** : Container considéré healthy
- **Status code 5xx** : Container considéré unhealthy (Dokploy redémarre container)

**Configuration Dockerfile requise** :
- Directive HEALTHCHECK avec intervalle 30s
- Timeout 5s maximum
- Start period 10s (warmup)
- 3 retries avant unhealthy
- Commande : curl vers `http://localhost:8000/health`
- Exit code 0 si healthy, 1 si unhealthy

## Intégration Dokploy Health Checks

Le endpoint `/health` s'intègre nativement avec le système de health checks Dokploy :

**Configuration Dokploy (via UI)** :
- **Health Check Path** : `/health`
- **Health Check Port** : `8000`
- **Health Check Interval** : `30s` (période vérification)
- **Health Check Timeout** : `5s` (délai max réponse)
- **Health Check Retries** : `3` (nombre tentatives avant unhealthy)

**Comportement attendu** :
- ✅ Response `{"status": "ok"}` + code 200 → Container healthy (Dokploy maintient service actif)
- ❌ Timeout (> 5s) ou code 5xx → Container unhealthy → Rollback automatique après 3 échecs consécutifs

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Endpoint accessible** : GET `/health` accessible sans authentification et retourne réponse JSON valide
2. **Status code correct** : Endpoint retourne status code `200 OK` en conditions normales
3. **Response JSON valide** : Champ `status` présent avec valeur `"ok"` (type Literal strict)
4. **Response time performante** : Temps de réponse < 100ms au percentile p99 (mesuré sur 100 requêtes)
5. **Pas de side-effects** : Endpoint ne modifie aucun état, ne fait aucun appel externe (idempotence GET garantie)

## Critères techniques

6. **Endpoint synchrone** : Implémenté avec `def` (pas `async def`) car pas d'I/O externe (conformité CLAUDE.md)
7. **Type hints PEP 695 strict** : Signature complète avec `-> HealthResponse`, Literal type pour status field
8. **Pydantic response model** : HealthResponse hérite BaseModel avec validation automatique FastAPI
9. **Aucune dépendance externe** : Ne dépend PAS de DB/API/proxies (disponibilité garantie même si Decodo down)

## Critères qualité

10. **Coverage 95%+** : Tests couvrent 100% route health (4 tests unitaires + 4 tests intégration)
11. **Tous tests passent** : 8 tests (4 unitaires + 4 intégration) exécutés avec succès (0 échecs)
12. **Standards projet conformes** : Ruff lint clean, Mypy strict mode clean, Type hints PEP 695 respectés
13. **Docstring PEP 257** : Route et model documentés avec docstrings 1 ligne minimum

## Critères production

14. **HEALTHCHECK Dockerfile configuré** : Directive HEALTHCHECK intégrée dans Dockerfile avec curl vers `/health`
15. **Compatible Dokploy health checks** : Format response compatible health checks Dokploy (HTTP GET avec validation status code 200)
16. **Monitoring ready** : Endpoint intégrable directement dans Prometheus, Grafana, Datadog sans configuration spéciale

---

**💡 Note importante** : Story simple (2 story points) → 16 critères couvrent exhaustivement les aspects fonctionnels (5), techniques (4), qualité (4) et production (3).

**Principe SMART** : Chaque critère est **S**pécifique (endpoint GET /health), **M**esurable (response time < 100ms), **A**tteignable (pas de complexité technique), **R**elevant (foundation production), **T**emporel (Phase 1 MVP).
