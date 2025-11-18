---
title: "Story 1: Health check endpoint"
epic: "Epic 1: API Foundation"
story_points: 2
dependencies: []
date: "2025-18-01"
keywords: ["api", "health", "monitoring", "fastapi"]
scope: ["specs"]
technologies: ["FastAPI", "pytest", "TestClient"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Ops/DevOps** : Vérifier instantanément que l'API est opérationnelle avant et après un déploiement
- **Dokploy** : Utiliser le endpoint comme health check Docker pour détecter les conteneurs défaillants et déclencher des rollbacks automatiques
- **Monitoring externe** : Intégrer dans des outils de surveillance (Uptime Robot, Pingdom) pour alertes en cas de downtime

## Contraintes métier

- **Timeout Dokploy** : Le Docker HEALTHCHECK timeout est configuré à 5s, l'endpoint doit répondre en <100ms pour éviter faux positifs
- **Format response** : JSON structuré avec status code explicite (200 = healthy, 503 = unhealthy) pour parsing automatisé
- **SLA response time** : Réponse endpoint <50ms en p95 pour ne pas impacter le monitoring en production

## Valeur business

- ✅ **Déploiement sécurisé** : Validation automatique que la nouvelle version de l'API répond correctement avant de router le trafic
- ✅ **Rollback automatique** : Dokploy détecte un health check échoué et restaure automatiquement la version précédente, réduisant MTTR
- ✅ **Observabilité** : Fournit un point d'entrée simple pour le monitoring externe, permettant d'alerter ops avant que clients soient impactés
- ✅ **Debugging rapide** : Timestamp et version dans la response facilitent le diagnostic de problèmes déploiement

## Métriques succès

- **Response time p95** : <50ms (target: 10-20ms)
- **Uptime** : 99.9%+ détecté par health checks externes
- **Taux succès déploiements** : 100% des déploiements validés par health check avant mise en production

---

# 📋 Spécifications Techniques

## 1. Route GET /health

**Rôle** : Endpoint de santé léger permettant de vérifier que l'application FastAPI est démarrée et répond correctement.

**Interface** :

| Champ | Valeur |
|-------|--------|
| **Path** | `/health` |
| **Méthode HTTP** | `GET` |
| **Response Model** | `HealthCheckResponse` |
| **Status Codes** | `200` (healthy), `503` (unhealthy) |
| **Authentication** | Aucune (endpoint public) |

**Signature FastAPI** :
```python
@router.get("/health", response_model=HealthCheckResponse, status_code=200)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring and deployment validation."""
```

**Comportement** :
- Retourne immédiatement un statut `healthy` avec timestamp et version de l'application
- Pas de vérifications externes (DB, proxies) pour garantir réponse <50ms
- Statut HTTP 200 par défaut (503 réservé pour futures vérifications critiques)

## 2. Modèle HealthCheckResponse

**Rôle** : Schéma Pydantic définissant la structure de la réponse du health check.

**Interface** :
```python
class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"]
    timestamp: str
    version: str
    checks: dict[str, bool] | None = None
```

**Champs** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `status` | `Literal["healthy", "unhealthy"]` | Statut global de l'application | Valeurs: `healthy` ou `unhealthy` uniquement |
| `timestamp` | `str` | ISO 8601 timestamp de la réponse | Format: `YYYY-MM-DDTHH:MM:SS.sssZ` |
| `version` | `str` | Version de l'application | Format semver: `v0.1.0` |
| `checks` | `dict[str, bool] \| None` | Détails vérifications individuelles (optionnel) | Keys: noms checks, Values: statut bool |

**Validations** :
- `status` : Validation automatique par `Literal` (type safety)
- `timestamp` : Format ISO 8601 généré via `datetime.now(UTC).isoformat()`
- `version` : Lue depuis variable environnement `APP_VERSION` ou fichier `pyproject.toml`

**Exemple** :
```python
response = HealthCheckResponse(
    status="healthy",
    timestamp="2025-11-18T10:30:45.123Z",
    version="v0.1.0",
    checks=None
)
```

## 3. Logique Health Check

**Comportement** :
- **Phase MVP** : Vérification minimale (application répond)
- **Phase Future** : Vérifications optionnelles (DB connection, external APIs) via champ `checks`
- **Edge cases** : Retourner 503 si checks critiques échouent (à implémenter Phase 2+)

**Conditions succès** :
- Application FastAPI démarrée → Status 200 + `status="healthy"`
- Timestamp généré dynamiquement à chaque requête
- Version lue depuis config (fallback `v0.0.0` si non définie)

**Erreurs levées** :
- Aucune pour MVP (endpoint toujours disponible si app répond)

## 4. Exemples JSON

**Exemple 1 : Response Succès (200)** :
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:30:45.123Z",
  "version": "v0.1.0",
  "checks": null
}
```

**Exemple 2 : Response Échec (503) - Phase Future** :
```json
{
  "status": "unhealthy",
  "timestamp": "2025-11-18T10:32:12.456Z",
  "version": "v0.1.0",
  "checks": {
    "database": false,
    "proxy_service": true,
    "external_api": false
  }
}
```

## 5. Intégration Dokploy

**Docker HEALTHCHECK Configuration** :

Le Dockerfile doit inclure une instruction `HEALTHCHECK` utilisant ce endpoint :

```dockerfile
HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=5s \
            --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Paramètres HEALTHCHECK** :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `--interval` | `30s` | Fréquence des checks (toutes les 30 secondes) |
| `--timeout` | `5s` | Timeout max par check (endpoint doit répondre en <5s) |
| `--start-period` | `5s` | Grace period au démarrage avant premier check |
| `--retries` | `3` | Nombre d'échecs consécutifs avant marquer conteneur `unhealthy` |

**Comportement Dokploy** :
1. Conteneur démarre → Wait `start-period` (5s)
2. Execute health check toutes les 30s via `curl -f http://localhost:8000/health`
3. Si timeout >5s ou status ≠200 → Échec
4. Si 3 échecs consécutifs → Conteneur marqué `unhealthy` → Dokploy peut rollback automatiquement

**Note** : L'endpoint `/health` répond en <50ms, largement sous le timeout de 5s, garantissant détection fiable des problèmes réels.

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### HealthCheckResponse Model (5 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_health_check_response_valid` | `status="healthy", timestamp="2025-11-18T10:30:45.123Z", version="v0.1.0"` | `HealthCheckResponse` instance | Vérifie création modèle avec valeurs valides |
| 2 | `test_health_check_response_invalid_status` | `status="invalid"` | `ValidationError` | Vérifie rejection statut hors `Literal` |
| 3 | `test_health_check_response_optional_checks` | `checks={"db": True}` | `response.checks == {"db": True}` | Vérifie champ optionnel `checks` |
| 4 | `test_health_check_response_serialization` | `HealthCheckResponse(...)` | JSON dict avec clés attendues | Vérifie `.model_dump()` produit structure correcte |
| 5 | `test_health_check_response_default_checks` | `checks=None` (default) | `response.checks is None` | Vérifie comportement par défaut champ optionnel |

**Exemple code test AAA** :
```python
from pydantic import ValidationError
import pytest
from app.models.response import HealthCheckResponse


def test_health_check_response_valid():
    # Arrange: Setup valid input data
    status = "healthy"
    timestamp = "2025-11-18T10:30:45.123Z"
    version = "v0.1.0"

    # Act: Create HealthCheckResponse instance
    response = HealthCheckResponse(
        status=status,
        timestamp=timestamp,
        version=version
    )

    # Assert: Verify expected properties
    assert response.status == "healthy"
    assert response.timestamp == timestamp
    assert response.version == version
    assert response.checks is None


def test_health_check_response_invalid_status():
    # Arrange: Setup invalid status
    invalid_data = {
        "status": "invalid_status",
        "timestamp": "2025-11-18T10:30:45.123Z",
        "version": "v0.1.0"
    }

    # Act & Assert: Verify ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        HealthCheckResponse(**invalid_data)

    # Assert: Verify error details mention status field
    assert "status" in str(exc_info.value)
```

**Total tests unitaires** : 5 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**End-to-end** (4 tests) :

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_health_endpoint_returns_200` | App running | GET /health | Status 200 + JSON avec `status="healthy"` |
| 2 | `test_health_endpoint_response_structure` | App running | GET /health | JSON contient clés `status`, `timestamp`, `version`, `checks` |
| 3 | `test_health_endpoint_performance` | App running | GET /health | Response time <100ms |
| 4 | `test_health_endpoint_content_type` | App running | GET /health | Header `Content-Type: application/json` |

**Exemple code test Given/When/Then** :
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    # Given: Application is running and accessible
    # (TestClient simulates running app)

    # When: Client requests health endpoint
    response = client.get("/health")

    # Then: Response is successful with healthy status
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_health_endpoint_response_structure():
    # Given: Application is running
    client = TestClient(app)

    # When: Health endpoint is called
    response = client.get("/health")

    # Then: Response contains all required fields
    assert response.status_code == 200
    data = response.json()
    required_fields = ["status", "timestamp", "version", "checks"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Then: Verify field types
    assert isinstance(data["status"], str)
    assert data["status"] in ["healthy", "unhealthy"]
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)
    assert data["checks"] is None or isinstance(data["checks"], dict)
```

**Total tests intégration** : 4 tests

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Endpoint accessible** : `GET /health` retourne status code 200
2. **Format response valide** : JSON conforme au schéma `HealthCheckResponse` (status, timestamp, version, checks)
3. **Performance** : Temps de réponse < 50ms (99th percentile)
4. **Champ status** : Valeur `"healthy"` quand application opérationnelle

## Critères techniques

5. **Type safety** : Modèle Pydantic avec validation stricte (Literal types)
6. **Synchrone** : Endpoint implémenté avec `def` (pas `async def`)
7. **Sans dépendances externes** : Pas d'appel DB/API (check minimal MVP)

## Critères qualité

8. **Coverage tests** : Minimum 95% sur endpoint + modèle
9. **Tests passent** : 5 tests unitaires + 4 tests intégration tous verts
10. **Standards respect** : Ruff + Mypy + Type hints PEP 695

## Critères production (Phase 6.4)

11. **HEALTHCHECK Dockerfile** : Instruction configurée avec paramètres (interval 30s, timeout 5s, retries 3)
12. **Intégration Dokploy** : Health check détecte conteneur unhealthy et trigger rollback auto
