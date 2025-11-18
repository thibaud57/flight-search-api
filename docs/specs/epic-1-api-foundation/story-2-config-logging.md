---
title: "Story 2: Configuration & Logging"
epic: "Epic 1: API Foundation"
story_points: 3
dependencies: ["story-1"]
date: "2025-18-11"
keywords: ["config", "logging", "pydantic-settings", "json-logger", "basesettings", "field-validator", "pythonjsonlogger", "structured-logging"]
scope: ["specs"]
technologies: ["Pydantic Settings", "pythonjsonlogger", "pytest"]
---

# 🎯 Contexte Business

## Besoin utilisateur

### Persona 1: Développeur Backend
- Besoin de configurer rapidement l'application en développement local
- Variables environnement chargées automatiquement depuis fichier `.env`
- Messages d'erreur clairs si configuration invalide (LOG_LEVEL incorrect, credentials manquants)
- Documentation inline des variables via type hints et validation Pydantic

### Persona 2: DevOps Engineer
- Besoin de configurer l'application en production sans modifier le code
- Override de variables via environnement système (Docker, Dokploy)
- Validation stricte pour éviter déploiements avec config invalide
- Secrets jamais hardcodés dans le code source ou commités dans git

### Persona 3: Ops/Monitoring
- Besoin de logs structurés JSON pour ingestion dans plateformes observabilité (Grafana, Loki, Datadog)
- Contexte métier enrichi dans chaque log (search_id, destinations, proxy_used, etc.)
- Niveaux de log configurables dynamiquement sans redémarrage (DEBUG en dev, INFO en prod)
- Filtrage facile par champs structurés (level, message, extra fields)

## Contraintes métier

### Contraintes techniques
- Secrets JAMAIS hardcodés : Toutes les clés API (DECODO_*, TWOCAPTCHA_API_KEY) doivent provenir de variables environnement
- Validation stricte : Application refuse de démarrer si config invalide (LOG_LEVEL non reconnu, DECODO_USERNAME mal formaté)
- Type safety : Utilisation de Pydantic v2 avec type hints PEP 695 pour détection erreurs au développement
- Pas de dépendance DB : Configuration en mémoire, chargement au démarrage uniquement

### Contraintes sécurité
- Fichier `.env` dans `.gitignore` : Ne jamais committer secrets
- Masquage logs : Passwords/API keys ne doivent jamais apparaître en clair dans les logs
- Validation format : DECODO_USERNAME doit respecter pattern `customer-{key}-country-{code}`

### Contraintes performance
- Chargement config au démarrage : 1 seule lecture du fichier `.env`, pas de rechargement runtime
- Logs JSON optimisés : Overhead < 5% vs logs texte classiques
- Cache validation : Pydantic valide une seule fois au chargement

## Valeur business

- ✅ Sécurité renforcée : Validation stricte empêche erreurs de configuration coûteuses en production (downtime, fuite secrets)
- ✅ Débogage accéléré : Logs structurés JSON permettent recherche rapide d'incidents (filtrage par search_id, destinations)
- ✅ Compliance : Historique complet des actions pour audit (qui a recherché quoi, quand, avec quel proxy)
- ✅ Foundation pour monitoring : Base solide pour observabilité future (Phase 6: alertes, métriques, dashboards)
- ✅ Developer Experience : Configuration simple et documentée, erreurs explicites, pas de "magic values"
- ✅ Scalabilité ops : Configuration adaptable à tous les environnements (dev, staging, prod) sans modification code

## Métriques succès

### Métriques fonctionnelles
- 100% des variables environnement validées au démarrage (aucun runtime error lié à config invalide)
- 0 secret hardcodé détecté par scan automatisé (git-secrets, gitleaks)
- Logs structurés parsables à 100% en JSON valide

### Métriques qualité
- Coverage ≥ 95% sur modules `app/core/config.py` et `app/core/logger.py`
- 17+ tests passent (8 Settings + 6 Logger + 3 intégration)
- Mypy strict mode : 0 erreur de type
- Ruff lint : 0 erreur, warnings autorisés seulement selon config

### Métriques techniques
- Temps chargement config < 50ms au démarrage application
- Overhead logs structurés < 5% vs logs texte (mesuré via benchmark pytest)
- Taille fichier config < 200 lignes (maintenabilité)

---

# 📋 Spécifications Techniques

## 1. Classe Settings (BaseSettings)

**Rôle**: Gère la configuration applicative via variables environnement et fichier `.env`, avec validation stricte Pydantic v2.

**Interface**:
```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator, model_validator

class Settings(BaseSettings):
    """Configuration application chargée depuis variables environnement."""

    log_level: str
    decodo_username: str
    decodo_password: str
    decodo_proxy_host: str
    proxy_rotation_enabled: bool
    captcha_detection_enabled: bool
    captcha_solving_enabled: bool
    twocaptcha_api_key: str | None

    model_config = ConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="forbid"
    )

    @field_validator("log_level", mode="after")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valide LOG_LEVEL parmi valeurs autorisées."""

    @model_validator(mode="after")
    def validate_decodo_credentials(self) -> "Settings":
        """Valide cohérence credentials Decodo."""
```

**Champs/Paramètres**:

| Champ | Type | Description | Contraintes | Défaut |
|-------|------|-------------|-------------|---------|
| `log_level` | `str` | Niveau logs application | Enum: DEBUG, INFO, WARNING, ERROR, CRITICAL | `INFO` |
| `decodo_username` | `str` | Username proxy Decodo | Pattern: `customer-{key}-country-{code}`, min_length=10 | Requis |
| `decodo_password` | `str` | Password proxy Decodo | min_length=1 | Requis |
| `decodo_proxy_host` | `str` | Host:port proxy Decodo | Pattern: `{host}:{port}`, exemple: `pr.decodo.com:8080` | Requis |
| `proxy_rotation_enabled` | `bool` | Active rotation proxies | True/False | `True` |
| `captcha_detection_enabled` | `bool` | Active détection captcha | True/False | `True` |
| `captcha_solving_enabled` | `bool` | Active résolution captcha (Phase 7) | True/False | `False` |
| `twocaptcha_api_key` | `str \| None` | API key 2Captcha (optionnel) | min_length=32 si fourni | `None` |

**Comportement**:
- Chargement automatique depuis `.env` au démarrage application
- Variables environnement système overrident valeurs fichier `.env`
- Lève `ValidationError` si champs requis manquants ou format invalide
- Case-insensitive : `LOG_LEVEL=info` équivalent à `log_level=INFO`
- Extra fields interdits : Erreur si variable inconnue présente dans `.env`

**Validations**:

### field_validator: log_level
```python
@field_validator("log_level", mode="after")
@classmethod
def validate_log_level(cls, v: str) -> str:
    """Valide LOG_LEVEL parmi valeurs autorisées."""
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    upper_v = v.upper()
    if upper_v not in allowed_levels:
        raise ValueError(
            f"log_level must be one of {allowed_levels}, got {v}"
        )
    return upper_v
```

### model_validator: validate_decodo_credentials
```python
@model_validator(mode="after")
def validate_decodo_credentials(self) -> "Settings":
    """Valide cohérence credentials Decodo."""
    if self.decodo_username and not self.decodo_password:
        raise ValueError(
            "decodo_password required when decodo_username is set"
        )

    if not self.decodo_username.startswith("customer-"):
        raise ValueError(
            "decodo_username must start with 'customer-'"
        )

    if "-country-" not in self.decodo_username:
        raise ValueError(
            "decodo_username must contain '-country-' pattern"
        )

    if ":" not in self.decodo_proxy_host:
        raise ValueError(
            "decodo_proxy_host must be in format 'host:port'"
        )

    return self
```

### model_validator: validate_captcha_config
```python
@model_validator(mode="after")
def validate_captcha_config(self) -> "Settings":
    """Valide cohérence config captcha."""
    if self.captcha_solving_enabled and not self.twocaptcha_api_key:
        raise ValueError(
            "twocaptcha_api_key required when captcha_solving_enabled=True"
        )

    return self
```

**model_config Settings**:
```python
model_config = ConfigDict(
    env_file=".env",              # Charge depuis fichier .env
    env_prefix="",                # Pas de préfixe (variables directes)
    case_sensitive=False,         # LOG_LEVEL = log_level = Log_Level
    extra="forbid",               # Rejette variables inconnues
    validate_default=True,        # Valide valeurs par défaut
    str_strip_whitespace=True     # Trim whitespaces automatiquement
)
```

**Exemples**:

### Exemple 1: Fichier `.env` valide
```bash
LOG_LEVEL=INFO

DECODO_USERNAME=customer-abc123xyz-country-FR
DECODO_PASSWORD=secure_password_here
DECODO_PROXY_HOST=pr.decodo.com:8080

PROXY_ROTATION_ENABLED=true
CAPTCHA_DETECTION_ENABLED=true
CAPTCHA_SOLVING_ENABLED=false
```

### Exemple 2: Utilisation dans application
```python
from app.core.config import Settings

settings = Settings()
print(settings.log_level)  # "INFO"
print(settings.decodo_username)  # "customer-abc123xyz-country-FR"
```

### Exemple 3: Erreur validation
```python
# Fichier .env invalide
LOG_LEVEL=INVALID_LEVEL

# Erreur levée au chargement
# ValidationError: log_level must be one of {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}, got INVALID_LEVEL
```

---

## 2. Logger Structuré JSON

**Rôle**: Configure logging structuré JSON avec contexte métier enrichi pour observabilité et débogage.

**Interface**:
```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logger(log_level: str) -> logging.Logger:
    """Configure logger structuré JSON."""

def get_logger(name: str) -> logging.Logger:
    """Retourne logger configuré pour module."""

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra: str | int | float | bool | list[str] | None
) -> None:
    """Log message avec contexte métier enrichi."""
```

**Configuration Logger JSON**:

### Handler pythonjsonlogger
```python
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={
        "asctime": "timestamp",
        "levelname": "level",
        "name": "logger"
    }
)
handler.setFormatter(formatter)
```

### Format structuré
Chaque log produit un objet JSON avec champs obligatoires + extra fields:

**Champs obligatoires**:
- `timestamp` (str): ISO 8601 format `2025-11-18T10:30:00.123Z`
- `logger` (str): Nom du module (ex: `app.services.crawler_service`)
- `level` (str): Niveau log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` (str): Message humain lisible

**Extra fields recommandés** (contexte métier):
- `search_id` (str): ID unique recherche pour traçabilité
- `destinations` (list[str]): Destinations recherchées
- `proxy_used` (str): Proxy Decodo utilisé
- `captcha_detected` (bool): Captcha rencontré
- `flight_count` (int): Nombre vols parsés
- `error_type` (str): Type d'erreur si applicable
- `retry_attempt` (int): Numéro tentative retry

**Exemple output JSON**:
```json
{
  "timestamp": "2025-11-18T10:30:15.234Z",
  "logger": "app.services.search_service",
  "level": "INFO",
  "message": "Flight search completed",
  "search_id": "abc123xyz",
  "destinations": ["Paris", "Tokyo", "New York"],
  "flight_count": 10,
  "duration_ms": 1234
}
```

**Méthode log_with_context**:

```python
def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra: str | int | float | bool | list[str] | None
) -> None:
    """Log message avec contexte métier enrichi.

    Args:
        logger: Logger configuré
        level: Niveau log (debug, info, warning, error, critical)
        message: Message humain lisible
        **extra: Contexte métier (search_id, destinations, etc.)

    Example:
        log_with_context(
            logger,
            "info",
            "Flight search started",
            search_id="abc123",
            destinations=["Paris", "Tokyo"]
        )
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)
```

**Niveaux logging et contexte métier**:

| Niveau | Utilisation | Environnement | Contexte recommandé |
|--------|-------------|---------------|---------------------|
| `DEBUG` | Détails verbeux développement | Dev uniquement | Tous les champs disponibles + internals (HTML size, parsing steps) |
| `INFO` | Opérations normales | Dev + Prod | search_id, destinations, flight_count, duration_ms |
| `WARNING` | Situations anormales récupérables | Dev + Prod | retry_attempt, error_type, proxy_used |
| `ERROR` | Erreurs nécessitant action | Dev + Prod | error_type, search_id, stack_trace (sanitized) |
| `CRITICAL` | Erreurs bloquant service | Prod | Tous champs + alert_sent=True |

**Standards logging métier**:

### Événements à logger obligatoirement
1. **Début recherche vols** (INFO):
   - search_id, destinations, date_range
2. **Détection captcha** (WARNING):
   - search_id, captcha_detected=True, proxy_used
3. **Rotation proxy** (WARNING):
   - search_id, old_proxy, new_proxy, reason
4. **Parsing réussi** (INFO):
   - search_id, flight_count, parsing_duration_ms
5. **Erreur parsing** (ERROR):
   - search_id, error_type, html_snippet (sanitized)
6. **Top 10 résultats** (INFO):
   - search_id, result_count, cheapest_price, average_price

### Sanitization obligatoire
- ❌ Passwords jamais loggués : Masquer `DECODO_PASSWORD`, `TWOCAPTCHA_API_KEY`
- ❌ PII (données personnelles) : Masquer emails, numéros téléphone si présents
- ✅ Truncate HTML : Max 500 caractères pour snippets HTML en logs

**Exemple utilisation complète**:

```python
from app.core.logger import get_logger, log_with_context

logger = get_logger(__name__)

log_with_context(
    logger,
    "info",
    "Flight search started",
    search_id="abc123",
    destinations=["Paris", "Tokyo"],
    date_range={"start": "2025-06-01", "end": "2025-06-15"}
)

log_with_context(
    logger,
    "warning",
    "Captcha detected, retrying with new proxy",
    search_id="abc123",
    captcha_detected=True,
    proxy_used="pr.decodo.com:8080",
    retry_attempt=1
)

log_with_context(
    logger,
    "info",
    "Flight search completed",
    search_id="abc123",
    flight_count=10,
    duration_ms=1234,
    cheapest_price=1250.00
)
```

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé: AAA (Arrange/Act/Assert)**

### Settings (8 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_settings_valid_config` | `.env` valide avec tous champs requis | `Settings` instance créée | Tous champs chargés correctement |
| 2 | `test_settings_invalid_log_level` | `LOG_LEVEL=INVALID` | `ValidationError` levée | Message contient valeurs autorisées |
| 3 | `test_settings_missing_required_field` | `.env` sans `DECODO_USERNAME` | `ValidationError` levée | Message indique champ manquant |
| 4 | `test_settings_extra_fields_forbidden` | `.env` avec `UNKNOWN_VAR=value` | `ValidationError` levée | Message indique extra field interdit |
| 5 | `test_settings_validation_decodo_username_pattern` | `DECODO_USERNAME=invalid_format` | `ValidationError` levée | Message indique pattern requis |
| 6 | `test_settings_validation_decodo_proxy_host_format` | `DECODO_PROXY_HOST=invalid_host` | `ValidationError` levée | Message indique format `host:port` requis |
| 7 | `test_settings_env_override` | `.env` + env var `LOG_LEVEL=DEBUG` | `settings.log_level == "DEBUG"` | Env var prioritaire sur fichier |
| 8 | `test_settings_defaults` | `.env` minimal (requis seulement) | `proxy_rotation_enabled == True`, `captcha_solving_enabled == False` | Valeurs par défaut appliquées |

**Exemple code test AAA**:

```python
from pydantic import ValidationError
import pytest
from app.core.config import Settings

def test_settings_valid_config(tmp_path):
    # Arrange: Setup valid .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=INFO\n"
        "DECODO_USERNAME=customer-abc123-country-FR\n"
        "DECODO_PASSWORD=password123\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
        "PROXY_ROTATION_ENABLED=true\n"
        "CAPTCHA_DETECTION_ENABLED=true\n"
        "CAPTCHA_SOLVING_ENABLED=false\n"
    )

    # Act: Load settings
    settings = Settings(_env_file=str(env_file))

    # Assert: Verify all fields loaded correctly
    assert settings.log_level == "INFO"
    assert settings.decodo_username == "customer-abc123-country-FR"
    assert settings.decodo_password == "password123"
    assert settings.decodo_proxy_host == "pr.decodo.com:8080"
    assert settings.proxy_rotation_enabled is True
    assert settings.captcha_detection_enabled is True
    assert settings.captcha_solving_enabled is False


def test_settings_invalid_log_level(tmp_path):
    # Arrange: Setup .env with invalid LOG_LEVEL
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=INVALID_LEVEL\n"
        "DECODO_USERNAME=customer-abc123-country-FR\n"
        "DECODO_PASSWORD=password123\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
    )

    # Act & Assert: Expect ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=str(env_file))

    # Assert: Verify error message
    assert "log_level" in str(exc_info.value)
    assert "DEBUG" in str(exc_info.value)
    assert "INFO" in str(exc_info.value)


def test_settings_validation_decodo_username_pattern(tmp_path):
    # Arrange: Setup .env with invalid username pattern
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=INFO\n"
        "DECODO_USERNAME=invalid_format\n"
        "DECODO_PASSWORD=password123\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
    )

    # Act & Assert: Expect ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=str(env_file))

    # Assert: Verify error message indicates pattern requirement
    assert "customer-" in str(exc_info.value).lower()
```

**Total tests unitaires Settings**: 8 tests

---

### Logger (6 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_logger_json_output_format` | `logger.info("test message")` | JSON valide avec champs obligatoires | Parse JSON, vérifie timestamp, logger, level, message |
| 2 | `test_logger_all_levels` | Logs à tous niveaux (DEBUG→CRITICAL) | 5 logs JSON distincts | Vérifie `level` correct pour chaque |
| 3 | `test_logger_extra_context` | `log_with_context(extra={"search_id": "abc"})` | JSON contient `search_id` field | Vérifie extra field présent |
| 4 | `test_logger_message_sanitization` | Log avec password dans message | JSON message masqué | Password remplacé par `***` |
| 5 | `test_logger_performance` | 1000 logs structurés | Durée < 1000ms | Benchmark overhead < 1ms/log |
| 6 | `test_logger_handler_config` | `setup_logger("DEBUG")` | Logger configuré avec bon niveau | `logger.level == logging.DEBUG` |

**Exemple code test AAA**:

```python
import json
import logging
from io import StringIO
from app.core.logger import setup_logger, log_with_context

def test_logger_json_output_format():
    # Arrange: Setup logger with StringIO handler to capture output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = setup_logger("INFO")
    logger.handlers = [handler]

    # Act: Log message
    logger.info("Test message")

    # Assert: Verify JSON format
    log_output = stream.getvalue().strip()
    log_json = json.loads(log_output)

    assert "timestamp" in log_json
    assert log_json["logger"] is not None
    assert log_json["level"] == "INFO"
    assert log_json["message"] == "Test message"


def test_logger_extra_context():
    # Arrange: Setup logger
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = setup_logger("INFO")
    logger.handlers = [handler]

    # Act: Log with extra context
    log_with_context(
        logger,
        "info",
        "Flight search started",
        search_id="abc123",
        destinations=["Paris", "Tokyo"]
    )

    # Assert: Verify extra fields present
    log_output = stream.getvalue().strip()
    log_json = json.loads(log_output)

    assert log_json["search_id"] == "abc123"
    assert log_json["destinations"] == ["Paris", "Tokyo"]


def test_logger_performance():
    # Arrange: Setup logger
    logger = setup_logger("INFO")

    # Act: Benchmark 1000 logs
    import time
    start = time.perf_counter()

    for i in range(1000):
        log_with_context(
            logger,
            "info",
            f"Test log {i}",
            search_id=f"search_{i}",
            count=i
        )

    duration_ms = (time.perf_counter() - start) * 1000

    # Assert: Verify performance < 1ms per log
    assert duration_ms < 1000, f"Performance too slow: {duration_ms}ms for 1000 logs"
```

**Total tests unitaires Logger**: 6 tests

---

## Tests intégration

**Format recommandé: Given/When/Then (BDD)**

**End-to-end** (3 tests):

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_settings_load_from_env` | Fichier `.env` valide créé | Charger `Settings()` | Instance créée, tous champs valides |
| 2 | `test_integration_logger_writes_valid_json` | Logger configuré | Écrire 10 logs différents niveaux | Tous logs JSON valides parsables |
| 3 | `test_integration_settings_injected_fastapi` | App FastAPI + endpoint utilisant `Depends(get_settings)` | GET endpoint | Response contient log_level de settings |

**Exemple code test Given/When/Then**:

```python
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.config import Settings

def test_integration_settings_load_from_env(tmp_path):
    # Given: Valid .env file exists
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=DEBUG\n"
        "DECODO_USERNAME=customer-test123-country-FR\n"
        "DECODO_PASSWORD=testpass\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
        "PROXY_ROTATION_ENABLED=true\n"
        "CAPTCHA_DETECTION_ENABLED=false\n"
        "CAPTCHA_SOLVING_ENABLED=false\n"
    )

    # When: Load settings from .env file
    settings = Settings(_env_file=str(env_file))

    # Then: All fields loaded correctly
    assert settings.log_level == "DEBUG"
    assert settings.decodo_username == "customer-test123-country-FR"
    assert settings.proxy_rotation_enabled is True
    assert settings.captcha_detection_enabled is False


def test_integration_logger_writes_valid_json():
    # Given: Logger configured with all levels
    from app.core.logger import setup_logger, log_with_context
    from io import StringIO
    import json

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = setup_logger("DEBUG")
    logger.handlers = [handler]

    # When: Write 10 logs at different levels
    levels = ["debug", "info", "warning", "error", "critical"]
    for i, level in enumerate(levels * 2):
        log_with_context(
            logger,
            level,
            f"Test message {i}",
            test_id=i
        )

    # Then: All logs are valid JSON
    logs = stream.getvalue().strip().split("\n")
    assert len(logs) == 10

    for log_line in logs:
        log_json = json.loads(log_line)
        assert "timestamp" in log_json
        assert "level" in log_json
        assert "message" in log_json


def test_integration_settings_injected_fastapi():
    # Given: FastAPI app with settings dependency
    app = FastAPI()

    def get_settings() -> Settings:
        return Settings(
            log_level="INFO",
            decodo_username="customer-test-country-FR",
            decodo_password="test",
            decodo_proxy_host="pr.decodo.com:8080",
            proxy_rotation_enabled=True,
            captcha_detection_enabled=True,
            captcha_solving_enabled=False,
            twocaptcha_api_key=None
        )

    @app.get("/config")
    def read_config(settings: Settings = Depends(get_settings)):
        return {"log_level": settings.log_level}

    client = TestClient(app)

    # When: GET /config endpoint
    response = client.get("/config")

    # Then: Response contains log_level from settings
    assert response.status_code == 200
    data = response.json()
    assert data["log_level"] == "INFO"
```

**Total tests intégration**: 3 tests

---

## Exemples JSON

**Exemple 1: Fichier `.env` valide complet**:
```bash
# Logging configuration
LOG_LEVEL=INFO

# Decodo Proxy credentials (required)
DECODO_USERNAME=customer-abc123xyz456-country-FR
DECODO_PASSWORD=secure_password_here_min_8_chars
DECODO_PROXY_HOST=pr.decodo.com:8080

# Feature flags
PROXY_ROTATION_ENABLED=true
CAPTCHA_DETECTION_ENABLED=true

# Captcha solving (Phase 7 - optional)
CAPTCHA_SOLVING_ENABLED=false
# TWOCAPTCHA_API_KEY=your_2captcha_api_key_32_chars_min
```

**Exemple 2: Log JSON structure - Recherche vols démarrée**:
```json
{
  "timestamp": "2025-11-18T10:30:15.234Z",
  "logger": "app.services.search_service",
  "level": "INFO",
  "message": "Flight search started",
  "search_id": "abc123xyz",
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

**Exemple 3: Log JSON structure - Captcha détecté (WARNING)**:
```json
{
  "timestamp": "2025-11-18T10:30:18.567Z",
  "logger": "app.services.crawler_service",
  "level": "WARNING",
  "message": "Captcha detected, retrying with new proxy",
  "search_id": "abc123xyz",
  "captcha_detected": true,
  "proxy_used": "pr.decodo.com:8080",
  "retry_attempt": 1,
  "destinations": ["Paris"]
}
```

**Exemple 4: Log JSON structure - Erreur parsing (ERROR)**:
```json
{
  "timestamp": "2025-11-18T10:30:25.890Z",
  "logger": "app.services.flight_parser",
  "level": "ERROR",
  "message": "Failed to parse flight data: missing price field",
  "search_id": "abc123xyz",
  "error_type": "ParsingError",
  "html_snippet": "<div class='flight'>...</div>",
  "flight_index": 3
}
```

**Exemple 5: Erreur validation Settings - LOG_LEVEL invalide**:
```json
{
  "error": "ValidationError",
  "field": "log_level",
  "message": "log_level must be one of {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}, got TRACE",
  "input_value": "TRACE"
}
```

**Exemple 6: Erreur validation Settings - Pattern DECODO_USERNAME**:
```json
{
  "error": "ValidationError",
  "field": "decodo_username",
  "message": "decodo_username must start with 'customer-' and contain '-country-' pattern",
  "input_value": "user-abc-france"
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Configuration chargement automatique** : Classe `Settings` charge automatiquement variables depuis fichier `.env` au démarrage sans intervention manuelle
2. **Validation LOG_LEVEL stricte** : Seules valeurs DEBUG, INFO, WARNING, ERROR, CRITICAL acceptées (case-insensitive), sinon `ValidationError` levée avec message explicite
3. **Validation credentials Decodo** : `DECODO_USERNAME` doit respecter pattern `customer-{key}-country-{code}`, sinon `ValidationError` avec explication pattern requis
4. **Validation DECODO_PROXY_HOST format** : Doit contenir `:` (format `host:port`), sinon `ValidationError` indiquant format attendu
5. **Extra fields interdits** : Variables inconnues dans `.env` provoquent `ValidationError` avec liste champs autorisés
6. **Override environnement prioritaire** : Variables environnement système overrident valeurs `.env` (ex: `export LOG_LEVEL=DEBUG` prioritaire sur `LOG_LEVEL=INFO` dans `.env`)
7. **Logs structurés JSON valides** : Chaque log produit JSON parsable avec champs obligatoires (timestamp, logger, level, message)
8. **Contexte métier enrichi logs** : Fonction `log_with_context` ajoute extra fields (`search_id`, `destinations`, etc.) au JSON de log
9. **Sanitization secrets logs** : Passwords (`DECODO_PASSWORD`, `TWOCAPTCHA_API_KEY`) ne doivent jamais apparaître en clair dans logs (masqués par `***`)
10. **Valeurs par défaut appliquées** : Champs optionnels (`proxy_rotation_enabled`, `captcha_solving_enabled`) utilisent valeurs par défaut si absents de `.env`

## Critères techniques

11. **Type safety strict Pydantic v2** : Tous champs `Settings` typés avec hints PEP 695 (`str | None`, `bool`, etc.), validés par Mypy strict mode
12. **ConfigDict model_config complet** : Configuration `Settings` inclut `env_file=".env"`, `case_sensitive=False`, `extra="forbid"`, `validate_default=True`
13. **field_validator pour LOG_LEVEL** : Validateur custom utilise `@field_validator("log_level", mode="after")` avec liste allowed_levels
14. **model_validator cross-champs** : Validateurs `validate_decodo_credentials` et `validate_captcha_config` utilisent `@model_validator(mode="after")`
15. **pythonjsonlogger configuré** : Handler utilise `JsonFormatter` avec `rename_fields` pour champs lisibles (timestamp, level, logger)

## Critères qualité

16. **Coverage ≥ 95% modules config/logger** : Coverage pytest sur `app/core/config.py` et `app/core/logger.py` atteint minimum 95%
17. **17+ tests tous verts** : 8 tests Settings + 6 tests Logger + 3 tests intégration passent sans échec
18. **Mypy strict mode 0 erreur** : Commande `mypy app/core/` retourne 0 erreur de type
19. **Ruff lint/format conformes** : `ruff check app/core/` et `ruff format app/core/ --check` passent sans erreur (warnings autorisés selon config)
20. **Performance chargement config < 50ms** : Instanciation `Settings()` avec `.env` valide prend moins de 50ms (mesuré via benchmark pytest)
21. **Overhead logs structurés < 5%** : Benchmark 1000 logs JSON vs 1000 logs texte montre différence < 5% (mesuré via `time.perf_counter()`)
22. **Docstrings 1 ligne pragmatiques** : Toutes classes/fonctions ont docstring 1 ligne expliquant responsabilité, pas de verbosité inutile

---
