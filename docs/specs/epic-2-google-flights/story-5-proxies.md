---
title: "Story 5: Proxies (ProxyService + Rotation Decodo)"
epic: "Epic 2: Google Flights Integration"
story_points: 5
dependencies: ["epic-2/story-4"]
date: "2025-19-11"
keywords: ["proxies", "decodo", "residential", "rotation", "anti-detection", "france-targeting"]
scope: ["specs"]
technologies: ["decodo", "pydantic"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Éviter détection Google Flights** : Google utilise systèmes anti-bot sophistiqués (Cloudflare, DataDome) pour détecter scraping automatisé et bloquer requêtes suspectes via captchas ou rate limiting
- **Multiplier identités IP** : Distribuer requêtes de crawling sur plusieurs adresses IP résidentielles françaises authentiques pour simuler trafic utilisateurs réels géographiquement distribués
- **Rotation automatique transparente** : Service ProxyService gère pool de proxies Decodo et rotation round-robin sans intervention manuelle, intégré dans CrawlerService existant (Story 4)
- **Foundation anti-détection scalable** : Proxies résidentiels constituent première couche défense anti-bot (combinés avec stealth mode Crawl4AI Story 4), extensible avec captcha solving Phase 7 si nécessaire

## Contraintes métier

- **Coûts bandwidth Decodo variables** : Proxies résidentiels facturés au GB consommé ($2.60-3.50/GB selon volume mensuel d'après VERSIONS.md et decodo-proxies.md), chaque HTML Google Flights = ~200-500KB, nécessite optimisation nombre de requêtes
- **Rate limiting Google Flights** : Trop de requêtes depuis même IP déclenchent blocages temporaires (status 429) ou captchas, rotation IP obligatoire pour distribution charge
- **Authentification simple** : Format username Decodo = identifiant simple fourni par dashboard (ex: `testuser`), pas de format complexe customer-XXX-country-FR
- **France targeting MVP** : Focus MVP sur proxies résidentiels France uniquement (country=FR) pour cohérence géographique avec Google Flights France, extensible autres pays post-MVP
- **Rotation server-side Decodo native** : Decodo gère automatiquement la rotation IP côté serveur via endpoint rotating (port se terminant par 0, ex: 40000 pour France). Chaque requête reçoit une IP différente sans logique client. Endpoints sticky (ports 40001-49999) maintiennent la même IP pendant la session. Documentation officielle : https://help.decodo.com/docs/residential-proxy-endpoints-and-ports

## Valeur business

- **Taux succès crawl ≥85%** : Proxies résidentiels + rotation automatique évitent 90-95% captchas selon anti-detection.md patterns, cible MVP ≥85% requêtes réussies sans blocage
- **Économie vs blocages manuels** : Coût proxies ($2.60/GB × 200KB/requête = ~$0.0005/requête) largement compensé par évitement captchas manuels et maintenance sélecteurs CSS
- **Foundation anti-détection scalable** : ProxyService devient building block réutilisable pour toutes stories scraping futures (6, 7), patterns rotation applicables autres services
- **Métriques observables** : Logging structuré fournit insights taux utilisation proxies, distribution charge, corrélation proxy→captcha pour optimisation continue rotation strategy

## Métriques succès

- **Taux échec proxy <5%** : Moins de 5% des requêtes échouent pour raisons proxy (auth error, timeout proxy, IP blacklistée), vérifié via logs structured ERROR proxy_failure
- **Rotation sans duplicates** : Sur 100 requêtes consécutives avec pool 3 proxies → chaque proxy utilisé exactement 33-34 fois (distribution équitable round-robin), vérifié via counter proxy_used
- **Latency overhead proxy <500ms p95** : Temps ajouté par proxy résidentiel vs direct <500ms au p95 percentile (overhead acceptable pour anti-détection), mesuré via response_time_with_proxy - response_time_baseline
- **Intégration CrawlerService transparente** : ProxyService injecté dans CrawlerService (Story 4) utilise get_next_proxy() avant chaque crawler.arun(), vérifié via tests intégration mock spy
- **Coverage tests ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code ProxyConfig, ProxyService, intégration Settings (pytest-cov)

---

# 📋 Spécifications Techniques

## 1. ProxyConfig (Modèle Pydantic)

**Rôle** : Représenter configuration d'un proxy résidentiel Decodo avec validation automatique du format authentification customer-XXX-country-FR et génération URL proxy complète.

**Interface** :
```python
class ProxyConfig(BaseModel):
    """Configuration d'un proxy résidentiel Decodo."""

    host: str
    port: int
    username: str
    password: str
    country: str = "FR"

    def get_proxy_url(self) -> str:
        """Génère URL proxy complète format http://username:password@host:port."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `host` | `str` | Hostname proxy Decodo | Format `fr.decodo.com` ou `gate.decodo.com`, min_length=5 |
| `port` | `int` | Port proxy résidentiel | Port 40000 (rotating France) ou 40001-49999 (sticky), ≥ 1024 |
| `username` | `str` | Username auth Decodo | Identifiant simple fourni par dashboard (ex: `testuser`), min_length=5 |
| `password` | `str` | Mot de passe proxy Decodo | min_length=8, max_length=100 |
| `country` | `str` | Code pays ISO Alpha-2 (FR, US, etc.) | Default "FR", length=2, pattern `^[A-Z]{2}$` (uppercase) |

**Comportement** :

- **Validation nominale** :
  1. Instanciation ProxyConfig avec tous champs renseignés
  2. Validation automatique Pydantic v2 : host format hostname, port range, username regex, password length
  3. Génération URL proxy via `get_proxy_url()` retourne `http://username:password@host:port`
  4. Retour instance ProxyConfig validée

- **Validations Pydantic** :
  - `field_validator('username', mode='after')` : Vérifier min_length=5 (identifiant simple Decodo)
  - `field_validator('host', mode='after')` : Vérifier hostname valide format (relaxé pour multi-provider support)
  - `field_validator('port', mode='after')` : Vérifier port dans range valide 1-65535 (standard TCP/IP)
  - `field_validator('country', mode='before')` : Convertir automatiquement lowercase→uppercase (ex: "fr" → "FR") pour normalisation

- **Edge cases** :
  - **Username trop court** : Si username <5 caractères → Lève `ValidationError` "Username must be at least 5 characters"
  - **Port invalide** : Si port hors range 1-65535 → Lève `ValidationError` "Port must be between 1 and 65535"
  - **Host invalide** : Si host trop court (<5 caractères) → Lève `ValidationError` "Host must be at least 5 characters"
  - **Password trop court** : Si password <8 caractères → Lève `ValidationError` "Password must be at least 8 characters"

**Notes implémentation** :
- **Validation host relaxée** : Implémentation actuelle n'exige plus "decodo.com" dans hostname pour supporter d'autres providers proxy résidentiels (flexibilité multi-provider). Field constraint `min_length=5` uniquement.
- **Validation port élargie** : Port range 1-65535 (standard technique) au lieu de ≥1024 (initialement spécifié pour Decodo 40000+). Ports 1-1023 rarement utilisés proxies mais validation technique standard acceptée.

- **Méthode get_proxy_url()** :
  - Format retour : `http://{username}:{password}@{host}:{port}`
  - Exemple : `http://testuser:mypassword@fr.decodo.com:40000`
  - Utilisé par CrawlerService pour passer proxy à BrowserConfig Crawl4AI

**Validations Pydantic** :

| Champ | Contrainte | Validator |
|-------|-----------|-----------|
| `host` | Contient "decodo.com" | `field_validator('host', mode='after')` |
| `port` | port ≥ 1024 | `field_validator('port', mode='after')` |
| `username` | min_length=5 | Field constraint standard |
| `password` | min_length=8, max_length=100 | Field constraint standard |
| `country` | Uppercase conversion + length=2 | `field_validator('country', mode='before')` |

---

## 2. ProxyService (Service Rotation)

**Rôle** : Wrapper simple autour de ProxyConfig unique pour intégration CrawlerService. La rotation IP est gérée automatiquement côté serveur par Decodo via endpoint rotating (port 40000), pas besoin de pool ni rotation client-side.

**Contexte Architecture** : Decodo propose 2 types d'endpoints proxy :
- **Rotating** (port se terminant par 0, ex: 40000 pour France) : Chaque requête HTTP reçoit automatiquement une IP différente, rotation server-side transparente
- **Sticky** (ports 40001-49999) : Maintient la même IP pendant la durée de session (10 minutes par défaut)

**Décision MVP** : Utiliser endpoint rotating 40000 → ProxyService devient simple wrapper sans logique rotation complexe (Decodo gère tout côté serveur).

**Interface simplifiée** :
```python
class ProxyService:
    """Service de gestion et rotation de proxies résidentiels Decodo."""

    def __init__(self, proxy_pool: list[ProxyConfig]):
        """
        Initialise service avec pool de proxies.

        Args:
            proxy_pool: Liste ProxyConfig depuis Settings, min 1 proxy

        Raises:
            ValueError: Si proxy_pool vide
        """

    def get_next_proxy(self) -> ProxyConfig:
        """Retourne prochain proxy selon rotation round-robin."""
```

**Champs/Paramètres** :

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `__init__` | `proxy_pool: list[ProxyConfig]` | None | Initialise service avec pool de proxies disponibles |
| `get_next_proxy()` | None | `ProxyConfig` | Retourne configuration proxy suivante selon rotation round-robin |

**Comportement** :

- **Rotation round-robin (compatibilité legacy)** :
  - Le service initialise un mécanisme de rotation circulaire sur le pool de proxies fourni
  - Chaque appel retourne la configuration suivante dans l'ordre, revenant au début après le dernier élément
  - **Note** : Rotation IP réelle gérée par Decodo endpoint 40000, pas par cette rotation client

- **Pourquoi conserver round-robin client ?** :
  - Pool peut contenir plusieurs configs Decodo (différents pays/régions)
  - Rotation client distribue requêtes entre configs disponibles
  - Si pool size 1 (cas MVP France uniquement) → retourne toujours même config, rotation IP assurée par Decodo

- **Méthodes supprimées (inutiles avec rotation server-side)** :
  - ❌ `get_random_proxy()` : Mode random post-MVP annulé (Decodo rotation suffisante)
  - ❌ `reset_pool()` : Pas de state client à reset
  - ❌ `current_proxy_index` property : Observabilité inutile (rotation server-side opaque)
  - ❌ `pool_size` property : Accessible via `len(proxy_pool)` si besoin

- **Edge cases** :
  - **Pool vide** : Si `proxy_pool` vide ou None → Lève `ValueError("Proxy pool cannot be empty")` dans `__init__`
  - **Pool size 1** : Round-robin retourne toujours même ProxyConfig, rotation IP assurée par Decodo endpoint 40000

**Logging structuré** :

- DEBUG : `get_next_proxy()` appelé → Logger proxy_host, proxy_country uniquement
- **Logs supprimés** : index, pool_size, total_calls (inutiles avec rotation server-side)

**Décision ADR-style** :
- **Avant** : Pool client avec rotation round-robin/random complexe
- **Après découverte Decodo docs** : Endpoint rotating 40000 gère rotation automatiquement → Simplification ProxyService en simple wrapper
- **Bénéfices** : -50% code (32→16 lignes), -60% tests (108→43 lignes), architecture aligned avec capacités réelles Decodo

---

## 3. Intégration CrawlerService (Extension Story 4)

**Rôle** : Modifier CrawlerService (défini Story 4) pour injecter ProxyService en dépendance, appeler get_next_proxy() avant chaque crawl, passer proxy_config à BrowserConfig Crawl4AI, logger proxy utilisé avec masquage password.

**Modification Interface CrawlerService** :

```python
class CrawlerService:
    """Service de crawling Google Flights avec stealth mode et proxy rotation."""

    def __init__(self, proxy_service: ProxyService | None = None):
        """
        Initialise service avec ProxyService optionnel.

        Args:
            proxy_service: Service rotation proxies Decodo (None désactive proxies)
        """

    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True
    ) -> CrawlResult:
        """
        Crawl Google Flights avec proxy rotation (retry logic Story 7).

        Flow:
        1. Si use_proxy=True → appeler proxy_service.get_next_proxy()
        2. Construire BrowserConfig avec proxy="http://user:pass@host:port"
        3. Exécuter crawler.arun(url) avec BrowserConfig
        4. Si CaptchaDetectedError détecté → logger WARNING et lever exception (retry géré Story 7)
        5. Logger proxy utilisé (masquer password) avec extra={proxy_host, proxy_country}
        """
```

**Comportement crawl_google_flights avec proxy** :

- **Étape 1 : Obtenir proxy** → Si use_proxy=True et proxy_service disponible, appeler `proxy_service.get_next_proxy()` pour récupérer ProxyConfig suivant dans rotation
- **Étape 2 : Construire BrowserConfig** → Créer instance BrowserConfig Crawl4AI avec enable_stealth=True, headless=False, proxy=proxy_config.get_proxy_url() (format http://user:pass@host:port) si proxy disponible, sinon None
- **Étape 3 : Exécuter crawl** → Utiliser AsyncWebCrawler avec BrowserConfig, appeler crawler.arun(url) pour récupérer HTML
- **Étape 4 : Détecter captcha** → Appeler méthode interne _is_captcha_detected(result.html) pour vérifier présence captcha dans HTML, si détecté → logger WARNING avec proxy_host et lever CaptchaDetectedError (retry géré Story 7 via @retry decorator)
- **Étape 5 : Logger succès** → Si crawl réussit, logger INFO avec extra fields url, proxy_host (hostname sans credentials), proxy_country, html_size (masquer password et username API key)

**Points d'Attention Intégration** :

- **Ne JAMAIS logger password en clair** : Logs contiennent uniquement `proxy_host` et `proxy_country`, jamais `username` complet (contient API key) ni `password`
- **Masquage username partiel** : Si logging username nécessaire → masquer API key : `customer-***MASKED***-country-fr`
- **Référence interface Story 4** : CrawlerService défini dans `docs/specs/epic-2-google-flights/story-4-crawler-parser.md`, pas de redéfinition complète ici, seulement extension avec proxy_service injection
- **Référence Story 7** : Retry logic Tenacity (Story 7) décore crawl_google_flights() via @retry, appelle automatiquement get_next_proxy() à chaque retry pour rotation IP automatique

**Logging Structuré Proxy** :

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `proxy_host` | String | Hostname proxy utilisé (sans credentials) | `"pr.decodo.com"` |
| `proxy_country` | String | Code pays proxy | `"FR"` |
| `proxy_port` | Integer | Port proxy | `8080` |
| `proxy_index` | Integer | Index proxy dans pool rotation | `2` (3ème proxy du pool) |
| `use_proxy` | Boolean | Proxies activés pour cette requête | `true` |

**Champs INTERDITS logs** : `proxy_username` (contient API key), `proxy_password` (secret), `proxy_url` (contient credentials embeddées).

---

## 4. Configuration Settings (Pydantic BaseSettings)

**Rôle** : Étendre app/core/config.py (Settings Pydantic BaseSettings) pour ajouter champs configuration proxies Decodo, générer automatiquement pool ProxyConfig via model_validator, charger depuis variables environnement .env.

**Extension Settings** :

```python
class Settings(BaseSettings):
    """Configuration application avec support proxies Decodo."""

    DECODO_USERNAME: str
    DECODO_PASSWORD: SecretStr
    DECODO_PROXY_HOST: str = "fr.decodo.com:40000"
    DECODO_PROXY_ENABLED: bool = True

    @model_validator(mode='after')
    def build_proxy_config(self) -> 'Settings':
        """Génère ProxyConfig depuis variables env si proxies activés."""
```

**Champs Proxies** :

| Champ | Type | Default | Description | Validation |
|-------|------|---------|-------------|------------|
| `DECODO_USERNAME` | `str` | - | Username Decodo (identifiant simple dashboard) | min_length 5 |
| `DECODO_PASSWORD` | `SecretStr` | - | Password Decodo (masqué logs) | min_length 8, masqué automatiquement par SecretStr |
| `DECODO_PROXY_HOST` | `str` | `"fr.decodo.com:40000"` | Hostname:port proxy Decodo France rotating | Format "host:port" avec validation contient "decodo.com" |
| `DECODO_PROXY_ENABLED` | `bool` | `True` | Active/désactive proxies globalement | False désactive proxy |

**Comportement** :

- **Chargement variables** → Settings charge automatiquement variables depuis .env (Config.env_file=".env")
- **Validation username** → min_length 5, identifiant simple fourni par dashboard Decodo
- **Génération ProxyConfig** → model_validator génère ProxyConfig depuis DECODO_USERNAME, PASSWORD, HOST si DECODO_PROXY_ENABLED=True
- **Sécurité password** → SecretStr masque automatiquement DECODO_PASSWORD dans logs (affiche "**********"), get_secret_value() utilisé uniquement pour génération ProxyConfig
- **Mode désactivé** → Si DECODO_PROXY_ENABLED=False, pas de ProxyConfig généré
- **Rotation server-side native Decodo** → Port 40000 (endpoint rotating France) change automatiquement l'IP à chaque requête HTTP. Pas de pool côté client nécessaire, ProxyService devient simple wrapper pour compatibilité CrawlerService. Documentation : https://help.decodo.com/docs/residential-proxy-endpoints-and-ports

**Variables .env** :

```bash
# Proxies Decodo Configuration
DECODO_USERNAME=testuser
DECODO_PASSWORD=my_secure_password_here
DECODO_PROXY_HOST=fr.decodo.com:40000
DECODO_PROXY_ENABLED=true
```


---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### ProxyConfig (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_proxy_config_valid_fields` | ProxyConfig avec tous champs valides | `host="fr.decodo.com"`, `port=40000`, `username="testuser"`, `password="mypassword"`, `country="FR"` | Instance ProxyConfig créée sans erreur, tous champs == input | Vérifie validation Pydantic nominale |
| 2 | `test_proxy_config_username_valid` | Username valide (min 5 caractères) | `username="testuser"` | Validation passe, instance créée | Vérifie min_length username |
| 3 | `test_proxy_config_username_too_short` | Username trop court (<5 caractères) | `username="abc"` | Lève `ValidationError` avec message "at least 5 characters" | Vérifie validation username min_length |
| 4 | `test_proxy_config_invalid_port` | Port invalide (<1024) | `port=80` (trop bas) | Lève `ValidationError` "Port must be >= 1024" | Vérifie validation port minimum |
| 5 | `test_proxy_config_generate_url_format` | Méthode get_proxy_url() génère URL correcte | ProxyConfig valide avec tous champs | Retour == `"http://testuser:mypassword@fr.decodo.com:40000"` | Vérifie format URL proxy pour BrowserConfig |
| 6 | `test_proxy_config_country_uppercase_conversion` | Country automatiquement converti en uppercase | `country="fr"` (lowercase input) | ProxyConfig.country == "FR" (uppercase) | Vérifie normalisation country field_validator mode='before' |

### ProxyService (3 tests - simplifiés post rotation server-side)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 7 | `test_proxy_service_round_robin_rotation` | Rotation round-robin cycle 3 proxies (compatibilité legacy) | Pool avec 3 ProxyConfig distincts, appeler get_next_proxy() 6 fois | Séquence retournée : proxy0, proxy1, proxy2, proxy0, proxy1, proxy2 (cycle complet 2 fois) | Vérifie algorithme round-robin circulaire correct (distribution configs client, rotation IP assurée par Decodo) |
| 8 | `test_proxy_service_get_next_logging` | Logging structuré appel get_next_proxy() | ProxyService initialisé, appeler get_next_proxy() 1 fois | Logs contiennent DEBUG avec extra={proxy_host, proxy_country} | Vérifie observabilité logging proxy utilisé (simplifié, pas d'index/pool_size car inutiles avec rotation server-side) |
| 9 | `test_proxy_service_empty_pool_error` | Pool vide lève ValueError | `proxy_pool=[]` (liste vide) | Lève `ValueError("Proxy pool cannot be empty")` dans __init__ | Vérifie validation pool non vide |

**Tests supprimés (méthodes inutiles avec rotation Decodo native)** :
- ❌ `test_proxy_service_random_distribution` : Méthode `get_random_proxy()` supprimée (rotation server-side Decodo)
- ❌ `test_proxy_service_reset_pool` : Méthode `reset_pool()` supprimée (pas de state client)
- ❌ `test_proxy_service_current_index_property` : Property `current_proxy_index` supprimée (observabilité inutile)

### Settings Configuration (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 13 | `test_settings_proxy_config_generation` | model_validator génère ProxyConfig | .env avec DECODO_USERNAME, PASSWORD, HOST, ENABLED=true | `settings.proxy_config` valide avec credentials cohérents | Vérifie génération automatique ProxyConfig depuis env vars |
| 14 | `test_settings_proxy_disabled` | Proxies désactivés génère None | .env avec DECODO_PROXY_ENABLED=false | `settings.proxy_config == None` | Vérifie comportement désactivation proxies |
| 15 | `test_settings_username_too_short` | Username trop court rejette Settings | .env avec DECODO_USERNAME="abc" | Lève `ValidationError` "at least 5 characters" | Vérifie validation username min_length |
| 16 | `test_settings_secret_str_password_masked` | SecretStr masque password dans logs | Settings avec DECODO_PASSWORD="secret123" | `str(settings.DECODO_PASSWORD) == "**********"` (masqué) | Vérifie sécurité SecretStr Pydantic |

**Total tests unitaires** : 6 (ProxyConfig) + 3 (ProxyService) + 4 (Settings) = **13 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_crawler_with_proxy_rotation` | Mock AsyncWebCrawler, ProxyService avec pool 3 proxies, CrawlerService initialisé avec proxy_service | Appeler `crawl_google_flights(url)` 3 fois consécutives | 3 crawls utilisent 3 proxies différents (proxy0, proxy1, proxy2 vérifiés via BrowserConfig.proxy), logs INFO contiennent proxy_host distinct pour chaque crawl |
| 2 | `test_integration_settings_load_from_env` | Fichier .env avec DECODO_USERNAME, PASSWORD, HOST, ENABLED=true | Charger Settings() depuis env | `settings.proxy_config` valide, aucune exception ValidationError |
| 3 | `test_integration_proxy_service_injected_crawler` | Settings avec proxies enabled, ProxyService créé depuis settings.proxy_pool, CrawlerService reçoit proxy_service via DI | Appeler `crawler_service.crawl_google_flights(url, use_proxy=True)` | CrawlerService appelle `proxy_service.get_next_proxy()` 1 fois (vérifié mock spy), BrowserConfig.proxy contient URL proxy complète, crawl success |
| 4 | `test_integration_proxy_rotation_logging_observability` | ProxyService pool 3 proxies, CrawlerService avec logging structuré activé | Crawler 10 URLs consécutives | Logs contiennent 10 entrées INFO avec extra fields proxy_host, proxy_index, proxy_country, distribution équitable proxies (3-3-4 ou 3-4-3 count), aucun password loggé |
| 5 | `test_integration_proxy_service_disabled_no_injection` | Settings avec DECODO_PROXY_ENABLED=false, CrawlerService initialisé sans proxy_service (None) | Appeler `crawl_google_flights(url, use_proxy=True)` | CrawlerService détecte proxy_service==None, BrowserConfig.proxy==None (pas de proxy utilisé), logs contiennent proxy_host="no_proxy", crawl success en mode direct |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 13 unitaires + 5 intégration = **18 tests**

---

## Exemples JSON

**Exemple 1 : ProxyConfig valide (tous champs renseignés)**

```json
{
  "host": "fr.decodo.com",
  "port": 40000,
  "username": "testuser",
  "password": "my_secure_password_123",
  "country": "FR"
}
```

**Note** : Tous champs validés par Pydantic (host contient "decodo.com", port ≥1024, username min 5 caractères, password ≥8 caractères, country uppercase ISO Alpha-2).

---

**Exemple 2 : ProxyConfig URL générée (get_proxy_url())**

```json
"http://testuser:my_secure_password_123@fr.decodo.com:40000"
```

**Note** : Format URL proxy complète utilisée par BrowserConfig Crawl4AI. Contient credentials embeddées (username:password), ne JAMAIS logger cette URL (utiliser proxy_host uniquement dans logs).

---

**Exemple 3 : Settings .env exemple (variables environnement)**

```bash
# Decodo Proxies Configuration (Story 5)
DECODO_USERNAME=testuser
DECODO_PASSWORD=my_secure_password_here
DECODO_PROXY_HOST=fr.decodo.com:40000
DECODO_PROXY_ENABLED=true
```

**Notes** :
- `DECODO_USERNAME` : Identifiant simple fourni par dashboard Decodo
- `DECODO_PASSWORD` : Mot de passe Decodo (masqué par SecretStr en logs)
- `DECODO_PROXY_HOST` : Hostname:port France rotating (default "fr.decodo.com:40000")
- `DECODO_PROXY_ENABLED` : Boolean active/désactive proxies (false pour dev local)

**Valeurs masquées production** : Remplacer credentials par vraies valeurs Decodo (stockées dans Dokploy secrets UI, pas committées dans git).

---

**Exemple 4 : Error ProxyRotationError (pool exhausted après retry)**

```json
{
  "error": "ProxyRotationError",
  "message": "All proxies in pool failed after 5 retry attempts",
  "details": {
    "proxies_tested": [
      {"host": "pr.decodo.com", "country": "FR", "status": "captcha_detected"},
      {"host": "pr.decodo.com", "country": "FR", "status": "timeout"},
      {"host": "pr.decodo.com", "country": "FR", "status": "captcha_detected"}
    ],
    "total_attempts": 5,
    "last_error": "CaptchaDetectedError: reCAPTCHA v2 detected"
  }
}
```

**Context** : Erreur levée si tous proxies pool échouent après max_retries (Story 4 retry logic). Indique besoin augmenter pool size ou investiguer blocage IP Decodo.

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **ProxyConfig validation complète** : ProxyConfig valide automatiquement 5 champs (host format "decodo.com", port ≥1024, username min 5 caractères, password min 8 caractères, country uppercase ISO Alpha-2) via field_validator Pydantic v2

2. **Rotation IP automatique Decodo** : Endpoint rotating port 40000 change automatiquement l'IP à chaque requête HTTP (rotation server-side native). ProxyService `get_next_proxy()` retourne ProxyConfig configuré avec endpoint rotating, rotation IP effective vérifiée via logs différents proxy réels entre requêtes consécutives (nécessite vraie clé Decodo pour test E2E)

3. **Intégration CrawlerService utilise proxy_service** : CrawlerService.crawl_google_flights() appelle `proxy_service.get_next_proxy()` avant chaque `crawler.arun()`, passe ProxyConfig.get_proxy_url() à BrowserConfig.proxy, vérifié via mock spy get_next_proxy appelé N fois pour N crawls

4. **Retry captcha change proxy automatiquement** : Si CaptchaDetectedError détectée → retry logic Tenacity (Story 4) appelle get_next_proxy() pour rotation IP automatique, 2ème tentative utilise proxy différent (vérifié proxy_index logs différents entre tentative 1 et 2)

5. **Settings génère ProxyConfig automatiquement** : model_validator génère `settings.proxy_config` ProxyConfig depuis variables env (DECODO_USERNAME, PASSWORD, HOST) si DECODO_PROXY_ENABLED=True

6. **Mode proxies désactivé fonctionne** : Si DECODO_PROXY_ENABLED=false → settings.proxy_config==None, CrawlerService initialise sans proxy, BrowserConfig.proxy==None, crawls réussissent en mode direct sans proxy (vérifié logs proxy_host=="no_proxy")

7. **URL proxy format correct** : ProxyConfig.get_proxy_url() retourne exactement `"http://{username}:{password}@{host}:{port}"`, utilisable directement par BrowserConfig Crawl4AI (vérifié regex matching URL + test crawl mock réussi)

8. **Logging proxy masque secrets** : Logs structurés contiennent uniquement `proxy_host`, `proxy_country`, `proxy_index`, jamais `proxy_username` complet (contient API key) ni `proxy_password` ni `proxy_url` (credentials embeddées), vérifié via assertion absence patterns secrets dans logs JSON

## Critères techniques

9. **Type hints PEP 695** : ProxyConfig, ProxyService, Settings extension annotés avec type hints modernes (`list[ProxyConfig]`, `str | None`, `SecretStr`, property retours typés)

10. **Pydantic v2 BaseModel ProxyConfig** : Utilise Field pour contraintes validation, field_validator mode='after' pour username/host/port, field_validator mode='before' pour country normalisation (lowercase→uppercase)

11. **Pydantic v2 BaseSettings extension** : Settings hérite BaseSettings avec env_file='.env', nouveaux champs DECODO_*, model_validator mode='after' pour génération proxy_pool automatique

12. **field_validator username min_length** : Validation min_length=5 obligatoire, lève ValidationError avec message explicite si trop court

13. **Rotation round-robin circulaire** : ProxyService implémente rotation infinie équitable sur le pool de proxies, chaque appel retourne la configuration suivante dans l'ordre cyclique (pas de boucles manuelles modulo)

14. **Dependency Injection ProxyService** : CrawlerService reçoit ProxyService via constructeur `__init__(proxy_service: ProxyService | None = None)`, testable avec mocks (vérifié tests intégration mock injection)

15. **Logging structuré JSON complet** : Tous logs ProxyService et CrawlerService incluent contexte proxy : proxy_host (hostname sans credentials), proxy_country, proxy_index, pool_size, use_proxy boolean (vérifié assertions extra fields présents)

16. **SecretStr Pydantic sécurité** : DECODO_PASSWORD défini comme `SecretStr`, masqué automatiquement dans logs (`str(settings.DECODO_PASSWORD) == "**********"`), `get_secret_value()` utilisé uniquement génération ProxyConfig

17. **Référence Story 4 interface** : CrawlerService extension référence explicitement `docs/specs/epic-2-google-flights/story-4-crawler-parser.md` pour interface existante (crawl_google_flights signature), pas de redéfinition complète

18. **Exceptions custom absentes** : Aucune exception custom ProxyRotationError nécessaire MVP (gestion erreurs via CaptchaDetectedError/NetworkError Story 4 existantes + retry logic Tenacity)

## Critères qualité

19. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de ProxyConfig, ProxyService, Settings extension (pytest-cov report)

20. **18 tests passent** : 13 tests unitaires (6 ProxyConfig + 3 ProxyService + 4 Settings) + 5 tests intégration tous verts (pytest -v), aucun test skipped ou xfail

21. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type (type hints ProxyConfig, ProxyService, Settings validés)

22. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification). Tests ProxyService simplifiés post-découverte rotation server-side Decodo (3 tests au lieu de 6)

23. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler + ProxyService configurés

24. **Docstrings 1 ligne** : ProxyConfig, ProxyService, Settings extension avec docstring descriptive, méthodes principales documentées (get_next_proxy, get_proxy_url, validate_username_format), focus POURQUOI pas QUOI

25. **Aucun code production dans specs** : Ce document contient uniquement signatures Python, tableaux tests descriptifs, exemples JSON, pseudo-code intégration (pas d'implémentation complète méthodes avec logique if/else/loops)

26. **Commits conventional** : Story 5 committée avec message exact `docs(specs): add story 5 specifications` conforme Conventional Commits type docs scope specs

---

**Note importante** : Story moyenne complexité (5 story points initialement, réduite à 3 post-simplification) → 26 critères couvrent exhaustivement gestion proxies (8 fonctionnels), architecture Pydantic v2 validation (10 techniques), qualité tests TDD (8 qualité).

**Simplification post-découverte** : Après vérification documentation Decodo (https://help.decodo.com/docs/residential-proxy-endpoints-and-ports), endpoint rotating port 40000 gère rotation IP automatiquement côté serveur. ProxyService simplifié de 54 lignes à 32 lignes (-40%), tests réduits de 21 à 18 (-14%). Bénéfices : architecture aligned avec capacités natives Decodo, moins de code à maintenir, rotation IP plus fiable (server-side vs client-side).

**Principe SMART** : Chaque critère est **S**pécifique (rotation server-side Decodo port 40000, wrapper ProxyService simple), **M**esurable (18 tests passent, coverage ≥80%, rotation IP vérifiée logs), **A**tteignable (réutilisation Story 4 CrawlerService, patterns Pydantic v2 existants, simplification vs complexité initiale), **R**elevant (foundation anti-détection scalable, économie bandwidth Decodo, architecture aligned capacités réelles provider), **T**emporel (MVP Phase 5, avant orchestration multi-city Story 6).
