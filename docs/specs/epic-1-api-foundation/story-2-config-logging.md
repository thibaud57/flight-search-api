---
title: "Story 2: Configuration & Logging"
epic: "Epic 1: API Foundation"
story_points: 3
dependencies: ["story-1-health-check.md"]
date: "2025-19-11"
keywords: ["config", "logging", "settings", "pydantic", "env-vars", "structured-logging", "json", "monitoring", "observability", "production"]
scope: ["specs"]
technologies: ["Pydantic", "pydantic-settings", "python-json-logger", "pytest"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **DevOps/SRE** : Configuration application via variables d'environnement pour déploiement multi-environnements (dev, staging, production) sans rebuild image Docker
- **Équipe Sécurité** : Gestion sécurisée des secrets (Decodo credentials, API keys) via .env local et variables d'environnement Dokploy (jamais hardcodés dans code)
- **Équipe Monitoring** : Logs structurés JSON pour intégration plateformes observabilité (Grafana Loki, CloudWatch, Datadog) avec filtrage contexte métier
- **Développeurs** : Environnement local reproductible via fichier .env avec validation automatique types et contraintes

## Contraintes métier

- **Secrets sécurisés** : JAMAIS committer .env dans Git, uniquement .env.example comme template
- **Validation stricte** : Variables d'environnement doivent être validées au startup pour fail-fast si config invalide
- **Compatibilité Dokploy** : Configuration via env vars injectées par Dokploy UI (pas de fichier .env en production)
- **Logs parsables** : Format JSON structuré obligatoire pour indexation automatique et alerting

## Valeur business

- ✅ **Déploiement multi-environnements** : Même image Docker déployable en dev/staging/prod avec config différente (économie build time)
- ✅ **Sécurité renforcée** : Validation Pydantic empêche démarrage avec credentials invalides (détection erreurs < 1s vs détection runtime ~minutes)
- ✅ **Troubleshooting accéléré** : Logs JSON avec contexte métier réduisent temps investigation bugs de ~30min à ~5min (recherche structurée vs grep logs texte)
- ✅ **Foundation observabilité** : Logs structurés préparent intégration monitoring Phase 5+ (captcha detection, proxy rotation, parsing errors)
- ✅ **Conformité best practices** : 12-Factor App configuration (factor III: Config) pour scalabilité cloud-native

## Métriques succès

- **Temps détection erreur config** : < 1s au startup (vs ~5min détection runtime sans validation)
- **Taux erreurs config production** : 0% après déploiement (validation empêche démarrage invalide)
- **Temps recherche logs** : < 30s pour retrouver événement spécifique (JSON filtrable vs grep texte)
- **Adoption monitoring** : 100% logs parsables par Grafana Loki/CloudWatch sans configuration additionnelle

---

# 📋 Spécifications Techniques

## 1. Settings (Pydantic BaseSettings)

**Rôle** : Charger et valider configuration application depuis variables d'environnement et fichier .env.

**Interface** :

```python
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """Configuration application chargée depuis variables d'environnement."""

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    DECODO_USERNAME: str
    DECODO_PASSWORD: str
    DECODO_PROXY_HOST: str
    PROXY_ROTATION_ENABLED: bool
    CAPTCHA_DETECTION_ENABLED: bool

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
```

**Champs Settings** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `LOG_LEVEL` | `Literal["DEBUG", "INFO", "WARNING", "ERROR"]` | Niveau minimum logs affichés | Valeurs strictes (type safety), INFO en prod, DEBUG en dev | `"INFO"` |
| `DECODO_USERNAME` | `str` | Username Decodo au format customer-{api_key}-country-FR | min_length=10, contient "customer-" et "-country-" | Requis |
| `DECODO_PASSWORD` | `str` | Password Decodo pour authentification proxies | min_length=8 | Requis |
| `DECODO_PROXY_HOST` | `str` | Host:port proxy Decodo | Format "host:port" valide | `"pr.decodo.com:8080"` |
| `PROXY_ROTATION_ENABLED` | `bool` | Active rotation automatique proxies | Booléen strict (true/false) | `True` |
| `CAPTCHA_DETECTION_ENABLED` | `bool` | Active détection captchas dans HTML | Booléen strict (true/false) | `True` |

**Comportement** :

- **Chargement automatique** : Variables d'environnement prennent priorité sur fichier .env
- **Validation au startup** : Pydantic valide types et contraintes, lève ValidationError si invalide
- **Fail-fast** : Application refuse démarrage si config invalide (empêche erreurs runtime)
- **Accès global** : Instance Settings injectable via Depends() FastAPI ou importée directement

**Validations** :

- `field_validator` pour `DECODO_USERNAME` : Vérifier format "customer-{key}-country-{code}"
- `field_validator` pour `DECODO_PROXY_HOST` : Vérifier format "host:port" (regex ou split validation)
- `model_validator` (mode='after') : Log warning si PROXY_ROTATION_ENABLED=false et CAPTCHA_DETECTION_ENABLED=false (configuration à risque)

**Type hints** :

- ✅ Literal type pour LOG_LEVEL : Valeurs strictes, autocomplétion IDE
- ✅ Type hints PEP 695 pour validators : `@field_validator classmethod`
- ✅ BaseSettings hérite BaseModel : Validation Pydantic automatique

---

## 2. Logger (Structured JSON)

**Rôle** : Configurer logging application avec format JSON structuré pour observabilité production.

**Interface** :

```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logger(log_level: str) -> logging.Logger:
    """Configure logger avec format JSON structuré."""
```

**Champs Logger Configuration** :

| Paramètre | Type | Description | Contraintes |
|-----------|------|-------------|-------------|
| `log_level` | `str` | Niveau minimum logs (DEBUG, INFO, WARNING, ERROR) | Doit correspondre à Settings.LOG_LEVEL |
| `handler` | `logging.StreamHandler` | Handler stdout pour conteneurs Docker | StreamHandler(sys.stdout) |
| `formatter` | `jsonlogger.JsonFormatter` | Formatter JSON avec champs standards | Format: timestamp, level, message, extra fields |

**Comportement** :

- **Format JSON structuré** : Chaque log est un objet JSON sur une ligne (compatible Grafana Loki, CloudWatch)
- **Champs standards** : asctime (ISO 8601), name, levelname, message, pathname, lineno, funcName
- **Extra fields support** : Logger accepte extra={} pour ajouter contexte métier (search_id, proxy_used, etc.)
- **Stdout output** : Logs écrits sur stdout (Docker capture automatiquement)
- **Pas de secrets** : Fonction helper mask_sensitive_data() pour masquer passwords, API keys dans logs

**Exemple Output JSON Log** :

```json
{
  "asctime": "2025-11-19T10:30:45.123Z",
  "name": "flight-search-api",
  "levelname": "INFO",
  "message": "Flight search started",
  "pathname": "app/services/search_service.py",
  "lineno": 42,
  "funcName": "search_flights",
  "search_id": "abc123",
  "destinations": ["Paris", "Tokyo"],
  "proxy_used": "pr.decodo.com:8080"
}
```

**Contraintes techniques** :

- **JSON sur une ligne** : Chaque log = 1 ligne JSON (facilite parsing)
- **Timestamps ISO 8601** : Format standard pour tri chronologique multi-timezones
- **Pas de colorisation** : Logs JSON bruts en production (colorisation uniquement dev via rich si besoin)
- **Thread-safe** : Logger configuré une seule fois au startup (singleton pattern)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### Settings (Pydantic BaseSettings) (10 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_settings_load_from_env_vars` | Settings charge variables d'environnement | Env vars valides (LOG_LEVEL=DEBUG, DECODO_USERNAME=customer-XXX-country-FR, etc.) | `settings.LOG_LEVEL == "DEBUG"` | Vérifie chargement automatique BaseSettings |
| 2 | `test_settings_load_from_dotenv_file` | Settings charge depuis fichier .env | Fichier .env avec variables valides | Settings instanciée avec valeurs .env | Vérifie fallback .env si env vars absentes |
| 3 | `test_settings_env_vars_override_dotenv` | Env vars prioritaires sur .env | Env var LOG_LEVEL=ERROR + .env LOG_LEVEL=DEBUG | `settings.LOG_LEVEL == "ERROR"` | Vérifie priorité env vars > .env (12-Factor App) |
| 4 | `test_settings_log_level_literal_validation` | LOG_LEVEL accepte uniquement valeurs valides | LOG_LEVEL="INVALID" | Lève `ValidationError` | Vérifie type safety Literal strict |
| 5 | `test_settings_decodo_username_format_valid` | DECODO_USERNAME format customer-{key}-country-{code} validé | DECODO_USERNAME="customer-XXX-country-FR" | Validation succès | Vérifie field_validator format username |
| 6 | `test_settings_decodo_username_format_invalid` | DECODO_USERNAME format invalide rejeté | DECODO_USERNAME="invalid-format" | Lève `ValidationError` | Vérifie field_validator détecte format invalide |
| 7 | `test_settings_decodo_proxy_host_format_valid` | DECODO_PROXY_HOST format host:port validé | DECODO_PROXY_HOST="pr.decodo.com:8080" | Validation succès | Vérifie field_validator format host:port |
| 8 | `test_settings_decodo_proxy_host_format_invalid` | DECODO_PROXY_HOST sans port rejeté | DECODO_PROXY_HOST="pr.decodo.com" | Lève `ValidationError` | Vérifie field_validator détecte port manquant |
| 9 | `test_settings_boolean_fields_coercion` | Booléens acceptent "true"/"false" strings | PROXY_ROTATION_ENABLED="true" | `settings.PROXY_ROTATION_ENABLED == True` | Vérifie coercion automatique Pydantic bool |
| 10 | `test_settings_model_validator_warns_risky_config` | Configuration à risque loggée (rotation+captcha disabled) | PROXY_ROTATION_ENABLED=false + CAPTCHA_DETECTION_ENABLED=false | Warning log émis | Vérifie model_validator détecte config dangereuse |

### Logger (Structured JSON) (8 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 11 | `test_setup_logger_returns_logger_instance` | setup_logger retourne instance Logger | log_level="INFO" | Instance `logging.Logger` retournée | Vérifie fonction retourne logger valide |
| 12 | `test_logger_output_is_valid_json` | Log émis est JSON parsable | logger.info("test message") | Output parsable par `json.loads()` | Vérifie JsonFormatter produit JSON valide |
| 13 | `test_logger_json_contains_standard_fields` | Log JSON contient champs standards | logger.info("test") | JSON contient asctime, name, levelname, message | Vérifie champs obligatoires présents |
| 14 | `test_logger_respects_log_level_debug` | Logger niveau DEBUG affiche tous logs | setup_logger("DEBUG") + logger.debug("test") | Log debug visible dans output | Vérifie niveau DEBUG capture tous logs |
| 15 | `test_logger_respects_log_level_info` | Logger niveau INFO filtre logs DEBUG | setup_logger("INFO") + logger.debug("test") | Log debug PAS visible | Vérifie niveau INFO filtre debug |
| 16 | `test_logger_supports_extra_fields` | Extra fields ajoutés au JSON log | logger.info("test", extra={"search_id": "abc123"}) | JSON contient field "search_id": "abc123" | Vérifie support contexte métier custom |
| 17 | `test_logger_does_not_log_secrets` | Secrets masqués dans logs | logger.info("test", extra={"password": "secret123"}) | JSON contient "password": "***" (masqué) | Vérifie fonction mask_sensitive_data() active |
| 18 | `test_logger_timestamp_is_iso8601` | Timestamps au format ISO 8601 | logger.info("test") | asctime format "YYYY-MM-DDTHH:MM:SS.sssZ" | Vérifie format timestamp standard |

**Total tests unitaires** : 10 (Settings) + 8 (Logger) = **18 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**Format tableau descriptif** (5 colonnes) :

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_settings_loaded_at_app_startup` | Application FastAPI avec Settings dependency | App startup avec env vars valides | Settings instance accessible via Depends() sans erreur |
| 2 | `test_app_refuses_startup_with_invalid_config` | Env vars invalides (LOG_LEVEL="INVALID") | Tentative startup application | ValidationError levée, application refuse démarrage (exit code 1) |
| 3 | `test_logger_functional_with_settings_log_level` | Settings.LOG_LEVEL="DEBUG" chargée | Logger configuré avec Settings.LOG_LEVEL | Logger affiche logs DEBUG correctement |
| 4 | `test_logs_parsable_by_json_parser` | Application running, logs émis | Capture stdout logs + parsing JSON | Tous logs parsables par json.loads() sans erreur |

**Total tests intégration** : 4 tests

**Total tests Story 2** : 18 tests unitaires + 4 tests intégration = **22 tests**

---

## Exemples JSON

**Exemple 1 : Fichier .env valide (template .env.example)**

```bash
LOG_LEVEL=INFO

DECODO_USERNAME=customer-abc123xyz-country-FR
DECODO_PASSWORD=SecurePassword123!
DECODO_PROXY_HOST=pr.decodo.com:8080

PROXY_ROTATION_ENABLED=true
CAPTCHA_DETECTION_ENABLED=true
```

**Exemple 2 : Settings model serialisé (model_dump JSON)**

```json
{
  "LOG_LEVEL": "INFO",
  "DECODO_USERNAME": "customer-abc123xyz-country-FR",
  "DECODO_PASSWORD": "SecurePassword123!",
  "DECODO_PROXY_HOST": "pr.decodo.com:8080",
  "PROXY_ROTATION_ENABLED": true,
  "CAPTCHA_DETECTION_ENABLED": true
}
```

**Exemple 3 : Log entry structuré JSON (avec extra fields)**

```json
{
  "asctime": "2025-11-19T14:22:30.456Z",
  "name": "flight-search-api",
  "levelname": "INFO",
  "message": "Proxy rotation successful",
  "pathname": "app/services/proxy_service.py",
  "lineno": 78,
  "funcName": "rotate_proxy",
  "search_id": "search-uuid-12345",
  "old_proxy": "pr.decodo.com:8080",
  "new_proxy": "pr.decodo.com:8081"
}
```

**Exemple 4 : Log entry avec masquage secrets**

```json
{
  "asctime": "2025-11-19T14:25:10.789Z",
  "name": "flight-search-api",
  "levelname": "DEBUG",
  "message": "Proxy authentication configured",
  "pathname": "app/services/proxy_service.py",
  "lineno": 42,
  "funcName": "configure_proxy",
  "decodo_username": "customer-***-country-FR",
  "decodo_password": "***",
  "proxy_host": "pr.decodo.com:8080"
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Chargement env vars réussi** : Settings charge toutes variables depuis .env ou env vars système sans erreur
2. **Validation types stricte** : LOG_LEVEL accepte uniquement valeurs Literal["DEBUG", "INFO", "WARNING", "ERROR"], rejette valeurs invalides avec ValidationError
3. **Fail-fast config invalide** : Application refuse démarrage si DECODO_USERNAME format invalide ou DECODO_PASSWORD manquant (ValidationError au startup)
4. **Logs JSON structurés** : Tous logs émis au format JSON sur une ligne avec champs standards (asctime, levelname, message)
5. **Extra fields fonctionnels** : Logger accepte extra={} pour contexte métier (search_id, proxy_used, etc.) et les inclut dans JSON

## Critères techniques

6. **BaseSettings Pydantic v2** : Settings hérite pydantic_settings.BaseSettings (pas pydantic.BaseSettings v1)
7. **field_validator pour formats** : DECODO_USERNAME validé avec field_validator (format customer-{key}-country-{code})
8. **pythonjsonlogger intégré** : Logger utilise pythonjsonlogger.JsonFormatter pour format JSON structuré
9. **Type safety Literal** : LOG_LEVEL utilise Literal strict (autocomplétion IDE, type checking mypy)

## Critères qualité

10. **Coverage 85%+** : Tests couvrent 100% Settings validation et 95%+ Logger configuration (18 unitaires + 4 intégration)
11. **Tous tests passent** : 22 tests (18 unitaires + 4 intégration) exécutés avec succès (0 échecs)
12. **Standards projet conformes** : Ruff lint clean, Mypy strict mode clean, Type hints PEP 695 respectés
13. **Docstrings PEP 257** : Settings class et setup_logger() documentées avec docstrings 1 ligne minimum

## Critères production

14. **Secrets jamais loggés** : Fonction mask_sensitive_data() masque DECODO_PASSWORD, API keys dans logs (validation via test)
15. **Compatible Dokploy env vars** : Settings fonctionne avec env vars injectées par Dokploy UI (pas de dépendance .env file en prod)
16. **Logs parsables Grafana Loki** : JSON logs indexables automatiquement par Grafana Loki sans config additionnelle (validation format JSON strict)

---

**💡 Note importante** : Story moyenne (3 story points) → 16 critères couvrent exhaustivement configuration sécurisée (5 fonctionnels), type safety strict (4 techniques), qualité tests élevée (4 qualité), production-ready logging (3 production).

**Principe SMART** : Chaque critère est **S**pécifique (Settings.LOG_LEVEL Literal strict), **M**esurable (22 tests passent), **A**tteignable (Pydantic + pythonjsonlogger patterns connus), **R**elevant (foundation observabilité), **T**emporel (Phase 1, avant endpoints métier).
