---
title: "Story 6: Proxies (ProxyService + Rotation Decodo)"
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
- **Authentification customer-XXX-country-FR stricte** : Format username Decodo exige exactement `customer-{api_key}-country-{country}` (minuscules obligatoires, tirets séparateurs), validation regex nécessaire pour éviter erreurs auth
- **France targeting MVP** : Focus MVP sur proxies résidentiels France uniquement (country=FR) pour cohérence géographique avec Google Flights France, extensible autres pays post-MVP
- **Pool size limité MVP** : Recommandation 3-5 proxies en pool pour MVP (balance entre distribution efficace et overhead gestion), extensible à 10-20 proxies selon monitoring taux blocage

## Valeur business

- **Taux succès crawl ≥85%** : Proxies résidentiels + rotation automatique évitent 90-95% captchas selon anti-detection.md patterns, cible MVP ≥85% requêtes réussies sans blocage
- **Économie vs blocages manuels** : Coût proxies ($2.60/GB × 200KB/requête = ~$0.0005/requête) largement compensé par évitement captchas manuels et maintenance sélecteurs CSS
- **Foundation anti-détection scalable** : ProxyService devient building block réutilisable pour toutes stories scraping futures (5, 6, 7), patterns rotation applicables autres services
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
| `host` | `str` | Hostname proxy Decodo | Format `pr.decodo.com` ou `gate.decodo.com`, min_length=10 |
| `port` | `int` | Port proxy résidentiel | Range 7000-9000 (ports Decodo standard), ≥ 1024 |
| `username` | `str` | Username auth format customer-XXX-country-FR | Pattern regex `^customer-[a-z0-9]+-country-[a-z]{2}$`, min_length=20 |
| `password` | `str` | Mot de passe proxy Decodo | min_length=8, max_length=100 |
| `country` | `str` | Code pays ISO Alpha-2 (FR, US, etc.) | Default "FR", length=2, pattern `^[A-Z]{2}$` (uppercase) |

**Comportement** :

- **Validation nominale** :
  1. Instanciation ProxyConfig avec tous champs renseignés
  2. Validation automatique Pydantic v2 : host format hostname, port range, username regex, password length
  3. Génération URL proxy via `get_proxy_url()` retourne `http://username:password@host:port`
  4. Retour instance ProxyConfig validée

- **Validations Pydantic** :
  - `field_validator('username', mode='after')` : Vérifier format `customer-{api_key}-country-{country}` avec regex `^customer-[a-z0-9]+-country-[a-z]{2}$`
  - `field_validator('host', mode='after')` : Vérifier que host contient "decodo.com" (hostname Decodo valide)
  - `field_validator('port', mode='after')` : Vérifier port dans range 7000-9000 (ports résidentiels Decodo standard)
  - `field_validator('country', mode='before')` : Convertir automatiquement lowercase→uppercase (ex: "fr" → "FR") pour normalisation

- **Edge cases** :
  - **Username format invalide** : Si username ne contient pas "customer-" prefix ou "country-" suffix → Lève `ValidationError` Pydantic avec message explicite "Username must match format customer-XXX-country-XX"
  - **Port hors range** : Si port <7000 ou >9000 → Lève `ValidationError` "Port must be between 7000 and 9000"
  - **Host invalide** : Si host ne contient pas "decodo.com" → Lève `ValidationError` "Host must be a valid Decodo hostname"
  - **Password trop court** : Si password <8 caractères → Lève `ValidationError` "Password must be at least 8 characters"

- **Méthode get_proxy_url()** :
  - Format retour : `http://{username}:{password}@{host}:{port}`
  - Exemple : `http://customer-abc123-country-fr:mypassword@pr.decodo.com:8080`
  - Utilisé par CrawlerService pour passer proxy à BrowserConfig Crawl4AI

**Validations Pydantic** :

| Champ | Contrainte | Validator |
|-------|-----------|-----------|
| `host` | Contient "decodo.com" | `field_validator('host', mode='after')` |
| `port` | 7000 ≤ port ≤ 9000 | `field_validator('port', mode='after')` |
| `username` | Regex `^customer-[a-z0-9]+-country-[a-z]{2}$` | `field_validator('username', mode='after')` |
| `password` | min_length=8, max_length=100 | Field constraint standard |
| `country` | Uppercase conversion + length=2 | `field_validator('country', mode='before')` |

---

## 2. ProxyService (Service Rotation)

**Rôle** : Gérer pool de proxies Decodo avec rotation round-robin automatique via itertools.cycle, fournir méthode get_next_proxy() pour distribution équitable charge, exposer observabilité état rotation.

**Interface** :
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
        """Retourne prochain proxy selon rotation round-robin (itertools.cycle)."""

    def get_random_proxy(self) -> ProxyConfig:
        """Retourne proxy aléatoire depuis pool (random.choice)."""

    def reset_pool(self) -> None:
        """Réinitialise cycle rotation (index → 0)."""

    @property
    def current_proxy_index(self) -> int:
        """Retourne index actuel dans cycle rotation (observabilité)."""

    @property
    def pool_size(self) -> int:
        """Retourne taille du pool de proxies."""
```

**Champs/Paramètres** :

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `__init__` | `proxy_pool: list[ProxyConfig]` | None | Initialise cycle avec itertools.cycle(proxy_pool) |
| `get_next_proxy()` | None | `ProxyConfig` | Retourne next(cycle) pour rotation round-robin |
| `get_random_proxy()` | None | `ProxyConfig` | Retourne random.choice(proxy_pool) pour imprévisibilité |
| `reset_pool()` | None | None | Réinitialise cycle avec itertools.cycle(proxy_pool) |
| `current_proxy_index` | None | `int` | Property read-only retourne index actuel (0 à pool_size-1) |
| `pool_size` | None | `int` | Property read-only retourne len(proxy_pool) |

**Comportement** :

- **Rotation round-robin (mode default MVP)** :
  1. Initialiser `self._cycle = itertools.cycle(proxy_pool)` dans `__init__`
  2. Maintenir `self._current_index = 0` pour tracking observabilité
  3. `get_next_proxy()` appelle `next(self._cycle)`, incrémente `_current_index % pool_size`, retourne ProxyConfig
  4. Cycle infini : proxy 0 → 1 → 2 → 0 → 1 → 2 → ... pour pool size 3
  5. Distribution équitable garantie : chaque proxy utilisé exactement N/pool_size fois pour N requêtes

- **Mode random (optionnel post-MVP)** :
  1. `get_random_proxy()` utilise `random.choice(self._proxy_pool)` pour sélection aléatoire
  2. Aucun state tracking (stateless, pas de cycle)
  3. Distribution probabiliste non garantie équitable (acceptable pour imprévisibilité accrue anti-bot)
  4. Utilisé si monitoring détecte rate limiting malgré round-robin

- **Observabilité état rotation** :
  1. `current_proxy_index` property retourne index actuel dans cycle (0-indexed)
  2. Utilisé par logging structuré pour tracer quel proxy utilisé par requête
  3. `pool_size` property retourne nombre total proxies configurés (utile métriques)

- **Edge cases** :
  - **Pool vide** : Si `proxy_pool` vide ou None → Lève `ValueError("Proxy pool cannot be empty")` dans `__init__`
  - **Pool size 1** : Round-robin retourne toujours même proxy (acceptable, pas d'erreur)
  - **Reset pool** : `reset_pool()` réinitialise cycle et index à 0 (utile pour tests ou changement config runtime)

**Logging structuré** :

- INFO : `get_next_proxy()` appelé → Logger proxy_host utilisé, current_index, pool_size
- DEBUG : État cycle rotation après chaque appel (proxy_host, index, total_calls)
- WARNING : Si même proxy retourné >10 fois consécutives (indique pool size 1 ou problème cycle)

**Stratégie rotation** :

| Critère | Round-Robin (itertools.cycle) | Random (random.choice) |
|---------|-------------------------------|------------------------|
| **Distribution** | Équitable garantie (33.3% pour pool size 3) | Probabiliste non garantie |
| **Prédictibilité** | Haute (séquence fixe 0→1→2→0) | Faible (séquence imprévisible) |
| **Performance** | Ultra-rapide (O(1) next()) | Rapide (O(1) choice()) |
| **Use-case** | MVP par défaut (simplicité + équité) | Post-MVP si rate limiting détecté |
| **State** | Stateful (tracking index) | Stateless (aucun tracking) |

**Décision ADR-style** : MVP utilise round-robin (simplicité, distribution équitable, patterns anti-detection.md), post-MVP bascule random si monitoring montre rate limiting malgré distribution équitable (imprévisibilité accrue).

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
        use_proxy: bool = True,
        max_retries: int = 3
    ) -> CrawlResult:
        """
        Crawl Google Flights avec rotation automatique proxy si captcha détecté.

        Flow:
        1. Si use_proxy=True → appeler proxy_service.get_next_proxy()
        2. Construire BrowserConfig avec proxy="http://user:pass@host:port"
        3. Exécuter crawler.arun(url) avec BrowserConfig
        4. Si CaptchaDetectedError → appeler get_next_proxy() nouveau → retry
        5. Logger proxy utilisé (masquer password) avec extra={proxy_host, proxy_country}
        """
```

**Comportement crawl_google_flights avec proxy** :

- **Étape 1 : Obtenir proxy** → Si use_proxy=True et proxy_service disponible, appeler `proxy_service.get_next_proxy()` pour récupérer ProxyConfig suivant dans rotation
- **Étape 2 : Construire BrowserConfig** → Créer instance BrowserConfig Crawl4AI avec enable_stealth=True, headless=False, proxy=proxy_config.get_proxy_url() (format http://user:pass@host:port) si proxy disponible, sinon None
- **Étape 3 : Exécuter crawl** → Utiliser AsyncWebCrawler avec BrowserConfig, appeler crawler.arun(url) pour récupérer HTML
- **Étape 4 : Détecter captcha** → Appeler méthode interne _is_captcha_detected(result.html) pour vérifier présence captcha dans HTML, si détecté → logger WARNING avec proxy_host et lever CaptchaDetectedError
- **Étape 5 : Retry automatique** → CaptchaDetectedError déclenche retry logic Tenacity (Story 4) qui appelle automatiquement get_next_proxy() pour rotation IP → nouvelle tentative avec proxy différent
- **Étape 6 : Logger succès** → Si crawl réussit, logger INFO avec extra fields url, proxy_host (hostname sans credentials), proxy_country, html_size (masquer password et username API key)

**Points d'Attention Intégration** :

- **Ne JAMAIS logger password en clair** : Logs contiennent uniquement `proxy_host` et `proxy_country`, jamais `username` complet (contient API key) ni `password`
- **Masquage username partiel** : Si logging username nécessaire → masquer API key : `customer-***MASKED***-country-fr`
- **Référence interface Story 4** : CrawlerService défini dans `docs/specs/epic-2-google-flights/story-4-crawler-parser.md`, pas de redéfinition complète ici, seulement extension avec proxy_service injection
- **Retry logic Story 4 réutilisée** : Tenacity retry automatique (Story 4) appelle get_next_proxy() à chaque retry après CaptchaDetectedError/NetworkError

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
    DECODO_PROXY_HOST: str = "pr.decodo.com:8080"
    DECODO_PROXY_ENABLED: bool = True
    DECODO_PROXY_POOL_SIZE: int = 3
    proxy_pool: list[ProxyConfig] = []

    @field_validator('DECODO_USERNAME', mode='after')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Valide format customer-XXX-country-FR."""

    @field_validator('DECODO_PROXY_POOL_SIZE', mode='after')
    @classmethod
    def validate_pool_size_range(cls, v: int) -> int:
        """Valide pool size entre 1 et 10."""

    @model_validator(mode='after')
    def generate_proxy_pool(self) -> 'Settings':
        """Génère pool de proxies depuis DECODO_USERNAME si proxies activés."""
```

**Champs Proxies** :

| Champ | Type | Default | Description | Validation |
|-------|------|---------|-------------|------------|
| `DECODO_USERNAME` | `str` | - | Username Decodo format customer-XXX-country-FR | Regex strict `^customer-[a-z0-9]+-country-[a-z]{2}$`, conversion lowercase |
| `DECODO_PASSWORD` | `SecretStr` | - | Password Decodo (masqué logs) | min_length 8, masqué automatiquement par SecretStr |
| `DECODO_PROXY_HOST` | `str` | `"pr.decodo.com:8080"` | Hostname:port proxy Decodo | Format "host:port" avec validation contient "decodo.com" |
| `DECODO_PROXY_ENABLED` | `bool` | `True` | Active/désactive proxies globalement | False désactive génération proxy_pool |
| `DECODO_PROXY_POOL_SIZE` | `int` | `3` | Nombre proxies dans pool rotation | Range 1-10 (validation field_validator) |
| `proxy_pool` | `list[ProxyConfig]` | `[]` | Pool proxies généré automatiquement | Généré par model_validator si DECODO_PROXY_ENABLED=True |

**Comportement** :

- **Chargement variables** → Settings charge automatiquement variables depuis .env (Config.env_file=".env")
- **Validation username** → field_validator DECODO_USERNAME vérifie regex `^customer-[a-z0-9]+-country-[a-z]{2}$` et convertit en lowercase
- **Validation pool size** → field_validator DECODO_PROXY_POOL_SIZE vérifie range 1-10, lève ValidationError si hors limites
- **Génération pool automatique** → model_validator génère liste proxy_pool avec DECODO_PROXY_POOL_SIZE instances ProxyConfig si DECODO_PROXY_ENABLED=True
- **Extraction country** → model_validator extrait country code depuis username via regex `country-([a-z]{2})` et convertit en uppercase (ex: "customer-abc-country-fr" → country="FR")
- **Sécurité password** → SecretStr masque automatiquement DECODO_PASSWORD dans logs (affiche "**********"), get_secret_value() utilisé uniquement pour génération ProxyConfig
- **Mode désactivé** → Si DECODO_PROXY_ENABLED=False, proxy_pool reste liste vide, ProxyService non initialisé

**Variables .env** :

```bash
# Proxies Decodo Configuration
DECODO_USERNAME=customer-abc123def456-country-fr
DECODO_PASSWORD=my_secure_password_here
DECODO_PROXY_HOST=pr.decodo.com:8080
DECODO_PROXY_ENABLED=true
DECODO_PROXY_POOL_SIZE=3
```


---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### ProxyConfig (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_proxy_config_valid_fields` | ProxyConfig avec tous champs valides | `host="pr.decodo.com"`, `port=8080`, `username="customer-abc123-country-fr"`, `password="mypassword"`, `country="FR"` | Instance ProxyConfig créée sans erreur, tous champs == input | Vérifie validation Pydantic nominale |
| 2 | `test_proxy_config_username_format_valid` | Username format customer-XXX-country-FR valide | `username="customer-abc123def456-country-fr"` | Validation passe, instance créée | Vérifie regex format username strict |
| 3 | `test_proxy_config_username_format_invalid` | Username format invalide (manque "customer-" prefix) | `username="abc123-country-fr"` | Lève `ValidationError` avec message "must match format customer-XXX-country-XX" | Vérifie validation username stricte |
| 4 | `test_proxy_config_invalid_port_range` | Port hors range 7000-9000 | `port=5000` (trop bas) | Lève `ValidationError` "Port must be between 7000 and 9000" | Vérifie validation port range Decodo |
| 5 | `test_proxy_config_generate_url_format` | Méthode get_proxy_url() génère URL correcte | ProxyConfig valide avec tous champs | Retour == `"http://customer-abc123-country-fr:mypassword@pr.decodo.com:8080"` | Vérifie format URL proxy pour BrowserConfig |
| 6 | `test_proxy_config_country_uppercase_conversion` | Country automatiquement converti en uppercase | `country="fr"` (lowercase input) | ProxyConfig.country == "FR" (uppercase) | Vérifie normalisation country field_validator mode='before' |

### ProxyService (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 7 | `test_proxy_service_round_robin_rotation` | Rotation round-robin cycle 3 proxies | Pool avec 3 ProxyConfig distincts, appeler get_next_proxy() 6 fois | Séquence retournée : proxy0, proxy1, proxy2, proxy0, proxy1, proxy2 (cycle complet 2 fois) | Vérifie algorithme round-robin itertools.cycle correct |
| 8 | `test_proxy_service_random_distribution` | Mode random couvre tous proxies | Pool avec 3 ProxyConfig, appeler get_random_proxy() 100 fois | Tous 3 proxies utilisés au moins 1 fois (distribution probabiliste) | Vérifie random.choice couvre pool complet |
| 9 | `test_proxy_service_get_next_logging` | Logging structuré appel get_next_proxy() | ProxyService initialisé, appeler get_next_proxy() 1 fois | Logs contiennent INFO avec extra={proxy_host, current_index, pool_size} | Vérifie observabilité logging proxy utilisé |
| 10 | `test_proxy_service_reset_pool` | Reset cycle remet index à 0 | Pool 3 proxies, appeler get_next_proxy() 5 fois (index=2 après modulo), appeler reset_pool(), appeler get_next_proxy() 1 fois | Proxy retourné après reset == proxy0 (index reset à 0) | Vérifie méthode reset_pool() fonctionnelle |
| 11 | `test_proxy_service_empty_pool_error` | Pool vide lève ValueError | `proxy_pool=[]` (liste vide) | Lève `ValueError("Proxy pool cannot be empty")` dans __init__ | Vérifie validation pool non vide |
| 12 | `test_proxy_service_current_index_property` | Property current_proxy_index retourne index correct | Pool 3 proxies, appeler get_next_proxy() 4 fois | `current_proxy_index` property retourne 1 (4 % 3 = 1) | Vérifie observabilité index rotation |

### Settings Configuration (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 13 | `test_settings_proxy_pool_generation` | model_validator génère pool automatiquement | .env avec DECODO_USERNAME, PASSWORD, HOST, POOL_SIZE=3, ENABLED=true | `settings.proxy_pool` length==3, tous ProxyConfig valides avec credentials cohérents | Vérifie génération automatique pool depuis env vars |
| 14 | `test_settings_proxy_disabled` | Proxies désactivés génère pool vide | .env avec DECODO_PROXY_ENABLED=false | `settings.proxy_pool == []` (liste vide) | Vérifie comportement désactivation proxies |
| 15 | `test_settings_username_validation_invalid_format` | Username format invalide rejette Settings | .env avec DECODO_USERNAME="invalid_format" | Lève `ValidationError` "must match format customer-XXX-country-XX" | Vérifie field_validator username strict |
| 16 | `test_settings_pool_size_range_invalid` | Pool size hors range 1-10 rejette | DECODO_PROXY_POOL_SIZE=15 (trop grand) | Lève `ValidationError` "must be between 1 and 10" | Vérifie field_validator pool_size range |
| 17 | `test_settings_extract_country_from_username` | Country extrait depuis username | DECODO_USERNAME="customer-abc-country-de" | `settings.proxy_pool[0].country == "DE"` (extrait depuis username) | Vérifie extraction country via regex dans model_validator |
| 18 | `test_settings_secret_str_password_masked` | SecretStr masque password dans logs | Settings avec DECODO_PASSWORD="secret123" | `str(settings.DECODO_PASSWORD) == "**********"` (masqué) | Vérifie sécurité SecretStr Pydantic |

**Total tests unitaires** : 6 (ProxyConfig) + 6 (ProxyService) + 6 (Settings) = **18 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_crawler_with_proxy_rotation` | Mock AsyncWebCrawler, ProxyService avec pool 3 proxies, CrawlerService initialisé avec proxy_service | Appeler `crawl_google_flights(url)` 3 fois consécutives | 3 crawls utilisent 3 proxies différents (proxy0, proxy1, proxy2 vérifiés via BrowserConfig.proxy), logs INFO contiennent proxy_host distinct pour chaque crawl |
| 2 | `test_integration_crawler_captcha_retry_new_proxy` | Mock AsyncWebCrawler retourne HTML captcha 1ère tentative puis HTML valide 2ème tentative, ProxyService pool 2 proxies | Appeler `crawl_google_flights(url, max_retries=2)` | CaptchaDetectedError déclenche retry, 2ème tentative utilise proxy différent (proxy1), logs WARNING captcha puis INFO success, résultat final CrawlResult.success==True |
| 3 | `test_integration_settings_load_from_env` | Fichier .env avec DECODO_USERNAME, PASSWORD, HOST, POOL_SIZE=5, ENABLED=true | Charger Settings() depuis env | `settings.proxy_pool` length==5, tous ProxyConfig valides, country extrait=="FR", aucune exception ValidationError |
| 4 | `test_integration_proxy_service_injected_crawler` | Settings avec proxies enabled, ProxyService créé depuis settings.proxy_pool, CrawlerService reçoit proxy_service via DI | Appeler `crawler_service.crawl_google_flights(url, use_proxy=True)` | CrawlerService appelle `proxy_service.get_next_proxy()` 1 fois (vérifié mock spy), BrowserConfig.proxy contient URL proxy complète, crawl success |
| 5 | `test_integration_proxy_rotation_logging_observability` | ProxyService pool 3 proxies, CrawlerService avec logging structuré activé | Crawler 10 URLs consécutives | Logs contiennent 10 entrées INFO avec extra fields proxy_host, proxy_index, proxy_country, distribution équitable proxies (3-3-4 ou 3-4-3 count), aucun password loggé |
| 6 | `test_integration_proxy_service_disabled_no_injection` | Settings avec DECODO_PROXY_ENABLED=false, CrawlerService initialisé sans proxy_service (None) | Appeler `crawl_google_flights(url, use_proxy=True)` | CrawlerService détecte proxy_service==None, BrowserConfig.proxy==None (pas de proxy utilisé), logs contiennent proxy_host="no_proxy", crawl success en mode direct |

**Total tests intégration** : 6 tests

---

**TOTAL TESTS** : 18 unitaires + 6 intégration = **24 tests**

---

## Exemples JSON

**Exemple 1 : ProxyConfig valide (tous champs renseignés)**

```json
{
  "host": "pr.decodo.com",
  "port": 8080,
  "username": "customer-abc123def456-country-fr",
  "password": "my_secure_password_123",
  "country": "FR"
}
```

**Note** : Tous champs validés par Pydantic (host contient "decodo.com", port dans range 7000-9000, username format regex strict, password ≥8 caractères, country uppercase ISO Alpha-2).

---

**Exemple 2 : ProxyConfig URL générée (get_proxy_url())**

```json
"http://customer-abc123def456-country-fr:my_secure_password_123@pr.decodo.com:8080"
```

**Note** : Format URL proxy complète utilisée par BrowserConfig Crawl4AI. Contient credentials embeddées (username:password), ne JAMAIS logger cette URL (utiliser proxy_host uniquement dans logs).

---

**Exemple 3 : Settings .env exemple (variables environnement)**

```bash
# Decodo Proxies Configuration (Story 6)
DECODO_USERNAME=customer-abc123def456-country-fr
DECODO_PASSWORD=my_secure_password_here
DECODO_PROXY_HOST=pr.decodo.com:8080
DECODO_PROXY_ENABLED=true
DECODO_PROXY_POOL_SIZE=3
```

**Notes** :
- `DECODO_USERNAME` : Format strict `customer-{api_key}-country-{country}` (minuscules obligatoires)
- `DECODO_PASSWORD` : Mot de passe Decodo (masqué par SecretStr en logs)
- `DECODO_PROXY_HOST` : Hostname:port (default "pr.decodo.com:8080")
- `DECODO_PROXY_ENABLED` : Boolean active/désactive proxies (false pour dev local)
- `DECODO_PROXY_POOL_SIZE` : Nombre proxies dans pool rotation (range 1-10 MVP)

**Valeurs masquées production** : Remplacer `abc123def456` et `my_secure_password_here` par vraies valeurs Decodo (stockées dans Dokploy secrets UI, pas committées dans git).

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

1. **ProxyConfig validation complète** : ProxyConfig valide automatiquement 5 champs (host format "decodo.com", port range 7000-9000, username regex `^customer-[a-z0-9]+-country-[a-z]{2}$`, password min 8 caractères, country uppercase ISO Alpha-2) via field_validator Pydantic v2

2. **Rotation round-robin sans duplicates** : Sur 100 appels `get_next_proxy()` avec pool size 3 → chaque proxy utilisé exactement 33 ou 34 fois (distribution équitable ±1), vérifié via counter assertion `abs(count_proxy0 - count_proxy1) <= 1`

3. **Intégration CrawlerService utilise proxy_service** : CrawlerService.crawl_google_flights() appelle `proxy_service.get_next_proxy()` avant chaque `crawler.arun()`, passe ProxyConfig.get_proxy_url() à BrowserConfig.proxy, vérifié via mock spy get_next_proxy appelé N fois pour N crawls

4. **Retry captcha change proxy automatiquement** : Si CaptchaDetectedError détectée → retry logic Tenacity (Story 4) appelle get_next_proxy() pour rotation IP automatique, 2ème tentative utilise proxy différent (vérifié proxy_index logs différents entre tentative 1 et 2)

5. **Settings génère pool automatiquement** : model_validator génère `settings.proxy_pool` liste de `DECODO_PROXY_POOL_SIZE` instances ProxyConfig depuis variables env (DECODO_USERNAME, PASSWORD, HOST), country extrait automatiquement via regex `country-([a-z]{2})`, vérifié len(proxy_pool)==POOL_SIZE et tous proxies valides

6. **Mode proxies désactivé fonctionne** : Si DECODO_PROXY_ENABLED=false → settings.proxy_pool==[], CrawlerService initialise sans proxy_service, BrowserConfig.proxy==None, crawls réussissent en mode direct sans proxy (vérifié logs proxy_host=="no_proxy")

7. **URL proxy format correct** : ProxyConfig.get_proxy_url() retourne exactement `"http://{username}:{password}@{host}:{port}"`, utilisable directement par BrowserConfig Crawl4AI (vérifié regex matching URL + test crawl mock réussi)

8. **Logging proxy masque secrets** : Logs structurés contiennent uniquement `proxy_host`, `proxy_country`, `proxy_index`, jamais `proxy_username` complet (contient API key) ni `proxy_password` ni `proxy_url` (credentials embeddées), vérifié via assertion absence patterns secrets dans logs JSON

## Critères techniques

9. **Type hints PEP 695** : ProxyConfig, ProxyService, Settings extension annotés avec type hints modernes (`list[ProxyConfig]`, `str | None`, `SecretStr`, property retours typés)

10. **Pydantic v2 BaseModel ProxyConfig** : Utilise Field pour contraintes validation, field_validator mode='after' pour username/host/port, field_validator mode='before' pour country normalisation (lowercase→uppercase)

11. **Pydantic v2 BaseSettings extension** : Settings hérite BaseSettings avec env_file='.env', nouveaux champs DECODO_*, model_validator mode='after' pour génération proxy_pool automatique

12. **field_validator username format strict** : Validation regex `^customer-[a-z0-9]+-country-[a-z]{2}$` obligatoire (minuscules only), lève ValidationError avec message explicite si format invalide

13. **itertools.cycle pour round-robin** : ProxyService utilise `self._cycle = itertools.cycle(proxy_pool)` pour rotation infinie équitable, next(cycle) appelé dans get_next_proxy() (pas de boucles manuelles modulo)

14. **Dependency Injection ProxyService** : CrawlerService reçoit ProxyService via constructeur `__init__(proxy_service: ProxyService | None = None)`, testable avec mocks (vérifié tests intégration mock injection)

15. **Logging structuré JSON complet** : Tous logs ProxyService et CrawlerService incluent contexte proxy : proxy_host (hostname sans credentials), proxy_country, proxy_index, pool_size, use_proxy boolean (vérifié assertions extra fields présents)

16. **SecretStr Pydantic sécurité** : DECODO_PASSWORD défini comme `SecretStr`, masqué automatiquement dans logs (`str(settings.DECODO_PASSWORD) == "**********"`), `get_secret_value()` utilisé uniquement génération ProxyConfig

17. **Référence Story 4 interface** : CrawlerService extension référence explicitement `docs/specs/epic-2-google-flights/story-4-crawler-parser.md` pour interface existante (crawl_google_flights signature), pas de redéfinition complète

18. **Exceptions custom absentes** : Aucune exception custom ProxyRotationError nécessaire MVP (gestion erreurs via CaptchaDetectedError/NetworkError Story 4 existantes + retry logic Tenacity)

## Critères qualité

19. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de ProxyConfig, ProxyService, Settings extension (pytest-cov report)

20. **24 tests passent** : 18 tests unitaires (6 ProxyConfig + 6 ProxyService + 6 Settings) + 6 tests intégration tous verts (pytest -v), aucun test skipped ou xfail

21. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type (type hints ProxyConfig, ProxyService, Settings validés)

22. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

23. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks AsyncWebCrawler + ProxyService configurés

24. **Docstrings 1 ligne** : ProxyConfig, ProxyService, Settings extension avec docstring descriptive, méthodes principales documentées (get_next_proxy, get_proxy_url, validate_username_format), focus POURQUOI pas QUOI

25. **Aucun code production dans specs** : Ce document contient uniquement signatures Python, tableaux tests descriptifs, exemples JSON, pseudo-code intégration (pas d'implémentation complète méthodes avec logique if/else/loops)

26. **Commits conventional** : Story 6 committée avec message exact `docs(specs): add story 6 specifications` conforme Conventional Commits type docs scope specs

---

**Note importante** : Story moyenne complexité (5 story points) → 26 critères couvrent exhaustivement gestion proxies (8 fonctionnels), architecture Pydantic v2 validation (10 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (rotation round-robin itertools.cycle, regex username strict), **M**esurable (24 tests passent, coverage ≥80%, distribution équitable ±1), **A**tteignable (réutilisation Story 4 CrawlerService, patterns Pydantic v2 existants), **R**elevant (foundation anti-détection scalable, économie bandwidth Decodo), **T**emporel (MVP Phase 5, avant orchestration multi-destinations Story 5).
