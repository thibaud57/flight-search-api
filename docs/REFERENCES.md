# REFERENCES.md - flight-search-api

Documentation technique complète pour toutes les technologies utilisées dans le projet.

**Date de dernière mise à jour** : 16 novembre 2025

---

## Table des Matières

1. [FastAPI](#fastapi)
2. [Pydantic v2](#pydantic-v2)
3. [Crawl4AI](#crawl4ai)
4. [Decodo Proxies](#decodo-proxies)
5. [Google Flights URL Structure](#google-flights-url-structure)
6. [Techniques Anti-Détection](#techniques-anti-détection)
7. [Détection de Captchas](#détection-de-captchas)
8. [Tenacity](#tenacity)
9. [Dokploy](#dokploy)

---

## FastAPI

### 1. Dependency Injection (Injection de Dépendances)

**Explication**
La Dependency Injection en FastAPI permet au framework de fournir automatiquement les dépendances déclarées dans vos fonctions. Il suffit de déclarer ce dont vous avez besoin via `Depends()`, et FastAPI se charge de l'injection, réduisant la duplication de code et centralisant la logique partagée.

**Exemple de code minimal**

```python
from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()

# Dépendance simple
def get_query(q: str | None = None):
    return q

# Utilisation dans une route
@app.get("/items/")
async def read_items(q: Annotated[str | None, Depends(get_query)] = None):
    return {"q": q}
```

**Patterns courants**

**Dépendances réutilisables avec classes**
```python
class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
    return {"q": commons.q, "skip": commons.skip, "limit": commons.limit}
```

**Sous-dépendances (dépendances imbriquées)**
```python
def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None,
):
    if not q:
        return last_query
    return q

@app.get("/items/")
async def read_items(query: Annotated[str, Depends(query_or_cookie_extractor)]):
    return {"query": query}
```

**Type aliases réutilisables**
```python
QueryDep = Annotated[str | None, Depends(get_query)]

@app.get("/items/")
async def read_items(q: QueryDep = None):
    return {"q": q}
```

**Points clés**
- Les dépendances peuvent être `async def` ou `def`, mixées librement
- Caching automatique des dépendances identiques dans une même requête
- Contrôlable avec `use_cache=False` si besoin de réévaluation
- Intégrées automatiquement dans le schéma OpenAPI

**Source** : https://fastapi.tiangolo.com/tutorial/dependencies/

---

### 2. Async Routes (Routes Asynchrones)

**Explication**
FastAPI supporte nativement les routes asynchrones via `async def`. Le choix entre `async def` et `def` dépend de vos besoins : utilisez `async def` si vous devez attendre des appels externes (APIs, BDD async), et `def` pour les traitements purement synchrones ou avec des librairies sans support async.

**Exemple de code minimal**

```python
from fastapi import FastAPI

app = FastAPI()

# Route asynchrone
@app.get("/async-items/")
async def read_async_items():
    # Vous pouvez utiliser await ici
    return {"message": "Async route"}

# Route synchrone
@app.get("/sync-items/")
def read_sync_items():
    return {"message": "Sync route"}
```

**Best practices**

**Async pour les appels externes (recommandé)**
```python
import httpx

@app.get("/external/")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

**Sync pour les traitements sans I/O**
```python
@app.get("/compute/")
def compute_result():
    result = sum(range(1000000))
    return {"result": result}
```

**Async avec dépendances asynchrones**
```python
async def get_db():
    # Connexion async à la base de données
    return db_connection

@app.get("/items/")
async def read_items(db: Annotated[Database, Depends(get_db)]):
    items = await db.fetch_items()
    return items
```

**Points clés**
- `await` n'existe que dans `async def`
- FastAPI exécute `def` dans un threadpool externe
- Les deux approches offrent de bonnes performances
- Mélanger `async def` et `def` est sans problème

**Source** : https://fastapi.tiangolo.com/async/

---

### 3. TestClient (Tests d'Intégration)

**Explication**
FastAPI fournit `TestClient`, basé sur Starlette et HTTPX, pour tester vos endpoints facilement. Il simule des requêtes HTTP sans serveur réel, permettant des tests d'intégration rapides et fiables avec une syntaxe familière.

**Installation**
```bash
pip install httpx pytest
```

**Exemple de code minimal**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

# Créer le client de test
client = TestClient(app)

# Test simple
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

**Patterns de test courants**

**GET avec paramètres de requête**
```python
def test_query_params():
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    assert response.json()["skip"] == 0
```

**POST avec JSON**
```python
def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Widget"
```

**Avec headers personnalisés**
```python
def test_with_auth():
    headers = {"Authorization": "Bearer token123"}
    response = client.get("/protected/", headers=headers)
    assert response.status_code == 200
```

**Validation d'erreurs**
```python
def test_invalid_request():
    response = client.post("/items/", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error
    errors = response.json()["detail"]
    assert len(errors) > 0
```

**Points clés**
- Utiliser `def` pour les fonctions de test (pas `async def`)
- Les requêtes se font avec `client.get()`, `client.post()`, etc.
- Accès JSON via `response.json()`
- Vérifier `response.status_code` pour les assertions
- Exécution avec `pytest` automatiquement

**Source** : https://fastapi.tiangolo.com/tutorial/testing/

---

## Pydantic v2

### 1. BaseSettings & Configuration d'Environnement

**Description**
`BaseSettings` hérite de `BaseModel` et ajoute le chargement automatique des variables d'environnement, fichiers `.env`, et secrets. Les variables d'environnement prennent toujours priorité sur les valeurs du fichier `.env`.

**Exemple minimal**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug_mode: bool = False

    class Config:
        env_file = '.env'
        env_prefix = 'APP_'

# Chargera APP_API_KEY et APP_DEBUG_MODE depuis l'environnement
settings = Settings()
```

**Source** : https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

### 2. Field Validator & Model Validator

**field_validator**

**Description**
Valide des champs individuels après (ou avant) le parsing Pydantic. Supporte 4 modes : `after` (défaut), `before`, `plain`, `wrap`.

**Exemple minimal**
```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    age: int

    @field_validator('age', mode='after')
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('age must be positive')
        return v
```

**model_validator**

**Description**
Valide l'ensemble du modèle après instantiation. Permet des validations cross-champs ou des transformations globales.

**Exemple minimal**
```python
from pydantic import BaseModel, model_validator

class Person(BaseModel):
    first_name: str
    last_name: str

    @model_validator(mode='after')
    def validate_names(self) -> 'Person':
        if self.first_name == self.last_name:
            raise ValueError('Names must be different')
        return self
```

**Source** : https://docs.pydantic.dev/latest/concepts/validators/

---

### 3. Configuration avec model_config

**Description**
Remplace la classe `Config` de v1. Utilise un dictionnaire `model_config` ou `ConfigDict` pour contrôler le comportement du modèle (extra fields, frozen, validation, etc.).

**Exemple minimal**
```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,           # Immutable
        validate_assignment=True,  # Valide les modifications
        extra='forbid',        # Rejette les champs supplémentaires
        str_strip_whitespace=True
    )

    name: str
    age: int
```

**Options clés**
- `extra` : `'ignore'` | `'forbid'` | `'allow'`
- `frozen` : Rend le modèle immutable
- `validate_default` : Valide les valeurs par défaut
- `validate_assignment` : Valide lors de modifications
- `strict` : Mode stricte (pas de coercion de types)

**Source** : https://docs.pydantic.dev/latest/api/config/

---

### 4. Migration v1 → v2 - Changements Importants

**Méthodes renommées**
| v1 | v2 |
|----|-----|
| `model.dict()` | `model.model_dump()` |
| `model.json()` | `model.model_dump_json()` |
| `Model.parse_obj(data)` | `Model.model_validate(data)` |
| `Model.parse_raw(json)` | `Model.model_validate_json(json)` |

**Décorateurs de validation remplacés**
| v1 | v2 |
|----|-----|
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |

**Champs optionnels**
```python
# v1
optional_field: Optional[str]  # ✓ Accepte None par défaut

# v2
optional_field: Optional[str] = None  # ✓ Doit spécifier le défaut
optional_field: str | None = None     # ✓ Syntaxe moderne
```

**Source** : https://docs.pydantic.dev/latest/migration/

---

## Crawl4AI

### 1. AsyncWebCrawler - Utilisation et Méthodes Principales

**Description**
AsyncWebCrawler est la classe principale pour les opérations de web scraping. Elle fournit une interface asynchrone pour crawler des pages individuelles ou multiples avec support complet de la configuration du navigateur, l'extraction structurée et le caching.

**Méthodes principales**
- `arun(url, config)` : Crawl une URL unique et retourne un objet CrawlResult
- `arun_many(urls, configs)` : Traite plusieurs URLs en parallèle avec configuration par URL

**Exemple minimal**
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_cfg = BrowserConfig(browser_type="chromium", headless=True)
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun("https://example.com", config=run_cfg)
        print(result.cleaned_html)

asyncio.run(main())
```

**Points clés**
- Utiliser le context manager `async with` pour gérer automatiquement les ressources
- Séparer BrowserConfig (global) et CrawlerRunConfig (par crawl)
- Le CrawlResult contient `cleaned_html`, `markdown`, et `extracted_content`

**Source** : https://docs.crawl4ai.com/api/async-webcrawler/

---

### 2. BrowserConfig - Configuration Browser et Stealth Mode

**Description**
BrowserConfig contrôle le comportement global du navigateur incluant le type de navigateur, le mode sans interface, les dimensions de la fenêtre, les proxies, les user-agents et les contextes persistants. Inclut le stealth mode pour contourner la détection de bots.

**Options principales**
- `browser_type` : Type de navigateur ("chromium", "firefox", "webkit")
- `headless` : Mode sans interface (True/False)
- `enable_stealth` : Active le stealth mode via playwright-stealth (True/False)
- `user_agent` : User-Agent personnalisé
- `viewport` : Dimensions de la fenêtre
- `proxy` : Configuration proxy

**Exemple avec stealth mode**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_conf = BrowserConfig(
    browser_type="chromium",
    headless=True,
    enable_stealth=True  # Active la protection contre la détection
)

async with AsyncWebCrawler(config=browser_conf) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown)
```

**Points clés**
- Stealth mode modifie les fingerprints du navigateur pour éviter la détection basique
- Désactivé par défaut (`False`)
- Recommandé pour les sites avec protection anti-bot
- Peut être combiné avec UndetectedAdapter pour une protection accrue

**Source** : https://docs.crawl4ai.com/core/browser-config/

---

### 3. JsonCssExtractionStrategy - Extraction CSS sans LLM

**Description**
JsonCssExtractionStrategy permet l'extraction de données structurées sans utiliser de modèles de langage. Elle utilise des sélecteurs CSS pour identifier et extraire des données avec précision, rapidité et coût zéro. Idéale pour les pages avec structure HTML répétitive.

**Concept**
- **Base Selector** : Identifie les conteneurs répétitifs (lignes de tableau, cartes de produits)
- **Fields** : Spécifie les sélecteurs CSS pour extraire les données individuelles

**Exemple complet**
```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_crypto_prices():
    schema = {
        "name": "Cryptocurrency Data",
        "baseSelector": ".crypto-row",  # Répéteur principal
        "fields": [
            {
                "name": "name",
                "selector": ".crypto-name",
                "type": "text"
            },
            {
                "name": "price",
                "selector": ".crypto-price",
                "type": "text"
            },
            {
                "name": "change",
                "selector": ".crypto-change",
                "type": "text"
            }
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.coinbase.com/explore",
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        print(json.dumps(result.extracted_content, indent=2))

asyncio.run(extract_crypto_prices())
```

**Types de champs supportés**
- `text` : Contenu textuel
- `attribute` : Attributs HTML (href, data-*, etc.)
- `html` : HTML brut
- `regex` : Extraction via expression régulière

**Avantages**
- Performance : Exécution quasi-instantanée
- Fiabilité : Résultats consistants et reproductibles
- Scalabilité : Traitement parallèle de milliers de pages
- Coût : Zéro appel API ou surcharge computationnelle

**Source** : https://docs.crawl4ai.com/extraction/no-llm-strategies/

---

## Decodo Proxies

### 1. Residential Rotation

**Description**
La rotation résidentielle de Decodo permet d'obtenir des adresses IP différentes soit à chaque requête, soit pendant une durée définie. Les proxies utilisent des appareils résidentiels authentiques (115M+ IPs) dans 195+ pays pour un masquage d'identité fiable.

**Modes disponibles**
- **Rotating proxies** : changement d'IP à chaque requête
- **Sticky sessions** : conservation de la même IP pendant 1 à 1440 minutes (jusqu'à 24 heures)

**Configuration exemple**

**Mode Rotating (sans session ID)**
```bash
curl -U username:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

**Mode Sticky Session (10 minutes par défaut)**
```bash
curl -U user-username-country-us-session-abc123:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

**Mode Sticky Session Personnalisé (30 minutes)**
```bash
curl -U user-username-country-us-sessionduration-30-session-abc123:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

**Source** : https://help.decodo.com/docs/residential-proxy-quick-start

---

### 2. France Targeting (Ciblage géographique)

**Description**
Decodo permet de cibler précisément les IPs résidentielles de France via des paramètres de localisation. Le pays est spécifié avec le code Alpha-2 ISO (FR pour France), et peut être combiné avec d'autres critères comme la ville ou les codes postaux.

**Configuration exemple**

**Endpoint France (tous les modes)**
```
fr.decodo.com:30001-39999  # Sticky session (port spécifique)
fr.decodo.com:30000        # Rotating session (port terminé en 0)
```

**Avec authentification Username/Password**
```bash
curl -U user-username-country-fr:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

**Avec ciblage France + Paris**
```bash
curl -U user-username-country-fr-city-paris:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

**Notes importantes**
- Le code pays est toujours en minuscules (fr, pas FR)
- Le ciblage par ville et ASN sont mutuellement exclusifs
- Whitelisted IP n'accepte que IPv4 (pas IPv6)

**Source** : https://help.decodo.com/docs/residential-proxy-endpoints-and-ports

---

### 3. Authentication (Authentification)

**Description**
Decodo propose deux méthodes d'authentification : Username/Password (standard) et IP Whitelisting (authentification par adresse IP).

**Format Authentication Username/Password**

**Format standard**
```
username:password
```

**Format avec paramètres (recommandé)**
```
user-{username}-country-{country_code}-city-{city_name}-session-{session_id}:password
```

**Exemple France avec session sticky**
```
user-myuser-country-fr-session-mysession123:mypassword
```

**Format avec API Key (Note du plan)**
```
customer-{api_key}-country-{country_code}:password
```

**Exemple pour France**
```
customer-abc123def456-country-fr:password
```

**Source** : https://help.decodo.com/docs/residential-proxy-authentication-methods

---

### 4. Bandwidth Optimization (Optimisation de bande passante)

**Description**
Decodo propose une tarification basée sur la bande passante avec réductions selon le volume. Les coûts diminuent proportionnellement avec l'augmentation de la consommation mensuelle.

**Pricing Plans**

| Volume | Prix/GB | Coût mensuel |
|--------|---------|--------------|
| 2 GB | $3.00 | $6 |
| 8 GB | $2.75 | $22 |
| 25 GB (Populaire) | $2.60 | $65 |
| 50 GB | $2.45 | $123 |
| 100 GB | $2.25 | $225 |
| 250 GB | $2.00 | $500 |
| 500 GB | $1.75 | $875 |
| 1000 GB | $1.50 | $1500 |
| Pay As You Go | $3.50 | - |

**Optimisation de coûts**

**Stratégie de volume**
- Pour les grands besoins : privilégier les plans à volume élevé
- Économies : jusqu'à 57% de réduction (1000GB vs 2GB)

**Budget des dépassements**
- Prévoir 30-40% de marge supplémentaire pour les pics
- Dépassements facturés au tarif Pay As You Go ($3.50/GB)

**Source** : https://decodo.com/proxies/residential-proxies/pricing

---

## Google Flights URL Structure

### 1. Structure URL de Base

**Format standard**
```
https://www.google.com/travel/flights?[parameters]
```

**Paramètres principaux**
- `departure_id` : Code aéroport départ (3 lettres)
- `arrival_id` : Code aéroport arrivée (3 lettres)
- `outbound_date` : Date départ (YYYY-MM-DD)
- `return_date` : Date retour (YYYY-MM-DD)
- `hl` : Langue interface (ex: `fr` pour français)
- `curr` : Devise (ex: `EUR` pour euros)
- `flight_type` : Type de vol (1=aller-simple, 2=aller-retour, 3=multi-city)

---

### 2. Format des Dates

**Format standardisé** : `YYYY-MM-DD`

**Exemples**
- Départ : `2025-11-21`
- Retour : `2025-11-28`

**Utilisation dans URLs**
```
outbound_date=2025-11-21&return_date=2025-11-28
```

---

### 3. Paramètres Multi-City

**Format JSON Multi-City**

Pour les vols avec plusieurs étapes, utiliser le paramètre `multi_city_json` avec un JSON encodé :

```json
[
  {
    "departure_id": "CDG",
    "arrival_id": "NRT",
    "date": "2025-11-21"
  },
  {
    "departure_id": "NRT",
    "arrival_id": "LAX,SEA",
    "date": "2025-11-28"
  },
  {
    "departure_id": "LAX",
    "arrival_id": "AUS",
    "date": "2025-12-05",
    "times": "8,18,9,23"
  }
]
```

**Structure des Segments**

Chaque segment multi-city requiert :
- **departure_id** : Aéroport de départ (code IATA)
- **arrival_id** : Aéroport d'arrivée (code IATA, ou codes multiples séparés par virgule)
- **date** : Date au format YYYY-MM-DD
- **times** (optionnel) : Plage horaire (format 24h : `start,end` ou `dep_start,dep_end,arr_start,arr_end`)

---

### 4. Localisation & Devise (France/EUR)

**Paramètres de Localisation**

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `hl` | `fr` | Interface en français |
| `curr` | `EUR` | Devise en euros |
| `hl` | `fr-FR` | Français France (variante complète) |

**Exemple URL Localisée France**
```
https://www.google.com/travel/flights?
  departure_id=CDG
  &arrival_id=ORY
  &outbound_date=2025-11-21
  &hl=fr
  &curr=EUR
```

---

### 5. Exemples Concrets Complets

**Aller-Simple : Paris (CDG) → Tokyo (NRT)**
```
https://www.google.com/travel/flights?
  flight_type=1
  &departure_id=CDG
  &arrival_id=NRT
  &outbound_date=2025-11-21
  &hl=fr
  &curr=EUR
```

**Aller-Retour : Paris (CDG) → New York (JFK)**
```
https://www.google.com/travel/flights?
  flight_type=2
  &departure_id=CDG
  &arrival_id=JFK
  &outbound_date=2025-12-01
  &return_date=2025-12-15
  &hl=fr
  &curr=EUR
```

**Multi-City : Paris → Tokyo → Los Angeles**
```
https://www.google.com/travel/flights?
  flight_type=3
  &multi_city_json=[
    {"departure_id":"CDG","arrival_id":"NRT","date":"2025-11-21"},
    {"departure_id":"NRT","arrival_id":"LAX","date":"2025-11-28"},
    {"departure_id":"LAX","arrival_id":"CDG","date":"2025-12-10"}
  ]
  &hl=fr
  &curr=EUR
```

---

### 6. Notes Importantes pour Implémentation

1. **URL Encoding** : Les paramètres JSON doivent être URL-encodés (espaces = `%20`, guillemets = `%22`)
2. **Format Dates** : Toujours utiliser `YYYY-MM-DD`, pas de variantes
3. **Codes IATA** : Google accepte aussi les identifiants de métropole (ex: `NYC` au lieu de `JFK`)
4. **Localisation** : `hl` affecte uniquement l'interface, les dates et codes restent universels
5. **Devise** : Affecte l'affichage uniquement, requête interne en USD
6. **Multi-City Limites** : ~10+ segments supportés officieusement

---

## Techniques Anti-Détection

### 1. Stealth Mode Crawl4AI

**Description**
Le Stealth Mode de Crawl4AI utilise `playwright-stealth` pour modifier les fingerprints du navigateur en supprimant les indicateurs détectables comme `navigator.webdriver` et en émulant un comportement de plugins réaliste.

**Configuration**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False  # Important : éviter le mode headless
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://example.com")
```

**Best Practices**
- Désactiver le mode headless (plus facile à détecter)
- Implémenter des délais raisonnables entre les requêtes
- Combiner avec d'autres techniques d'anti-détection

**Source** : https://docs.crawl4ai.com/advanced/undetected-browser/

---

### 2. Undetected Browser Mode (Mode Avancé)

**Description**
Pour les sites avec détection sophistiquée (Cloudflare, DataDome, Akamai), le mode Undetected Browser applique des patches plus profonds offrant une protection maximale contre les systèmes de détection modernes.

**Configuration**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    browser_type="undetected",  # Chrome non-détectable
    headless=True,
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security"
    ]
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://protected-site.com")
```

**Stratégie Progressive**
1. Commencer avec navigateur régulier + stealth mode
2. Si bloqué, escalader vers undetected browser
3. Pour protection maximale, combiner stealth mode + undetected browser

**Source** : https://docs.crawl4ai.com/advanced/undetected-browser/

---

### 3. User-Agent Rotation

**Description**
La rotation des User-Agents alterne les chaînes d'identification du navigateur pour simuler des requêtes provenant d'utilisateurs différents. La rotation pondérée (weighted rotation) est plus efficace que la sélection purement aléatoire.

**Configuration avec Pool Pondéré**
```python
import random

# Pool de user-agents avec poids
USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.4),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.3),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", 0.2),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.1),
]

def get_random_user_agent():
    agents, weights = zip(*USER_AGENTS)
    return random.choices(agents, weights=weights, k=1)[0]

# Utilisation avec Crawl4AI
browser_config = BrowserConfig(
    user_agent=get_random_user_agent()
)
```

**Best Practices**
- Utiliser des user-agents actuels et réalistes (Chrome/Firefox récents)
- Maintenir une diverse pool (Windows, macOS, navigateurs populaires)
- Assigner des poids plus élevés aux versions modernes
- Combiner avec throttling et rotation de proxies

---

### 4. Proxy Rotation

**Description**
La rotation des proxies distribue les requêtes sur plusieurs adresses IP pour éviter les blocages. Combiner proxies avec fingerprinting du navigateur et stealth mode simule un comportement utilisateur organique.

**Types de Proxies**

| Type | Détectabilité | Coût | Utilisation Recommandée |
|------|---------------|------|------------------------|
| Datacenter | Élevée | Très bas | Throttling simple |
| Residential (ISP) | Faible | Moyen-Haut | Web scraping complexe |
| Static Residential | Très faible | Haut | Connexions persistantes |
| Mobile | Très faible | Très haut | Contenu mobile-restricted |

**Configuration avec Stealth Mode et Proxy**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False,
    proxy="http://user:pass@proxy-ip:port",
    user_agent=get_random_user_agent()
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun("https://example.com")
```

**Pool Manager Pattern**
```python
import random
from itertools import cycle

PROXY_POOL = [
    "http://proxy1:port",
    "http://proxy2:port",
    "http://proxy3:port",
]

proxy_cycle = cycle(PROXY_POOL)

def get_next_proxy():
    return next(proxy_cycle)

# Ou sélection aléatoire pour plus de variation
def get_random_proxy():
    return random.choice(PROXY_POOL)
```

**Best Practices de Rotation**
- Utiliser ISP/Static Residential proxies pour l'evasion optimale
- Implémenter un pool manager avec rotation intelligente
- Associer chaque proxy à un nouveau fingerprint du navigateur
- Monitorer les taux de succès et adapter la rotation

---

### 5. Stratégie Complète Combinée

**Configuration Multi-Couches**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
import random

# Configuration avec toutes les techniques
browser_config = BrowserConfig(
    enable_stealth=True,           # Stealth mode
    headless=False,                # Désactiver headless
    browser_type="chromium",       # Ou "undetected" si nécessaire
    user_agent=get_random_user_agent(),  # User-agent rotation
    proxy=get_next_proxy(),        # Proxy rotation
    viewport={"width": 1920, "height": 1080},
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox"
    ]
)

# Avec délais aléatoires
import asyncio

async with AsyncWebCrawler(config=browser_config) as crawler:
    for url in urls:
        result = await crawler.arun(url)
        await asyncio.sleep(random.uniform(2, 5))  # Délai humain
```

**Ordre d'Application Recommandé**
1. **Couche 1** : Stealth Mode + User-Agent Rotation
2. **Couche 2** : Ajouter Proxy Rotation
3. **Couche 3** : Basculer à Undetected Browser si bloqué
4. **Couche 4** : Ajouter délais aléatoires et comportements humains

---

## Détection de Captchas

### 1. Patterns HTML de reCAPTCHA

**reCAPTCHA v2 (Checkbox)**
```html
<!-- Élément conteneur principal -->
<div class="g-recaptcha"
     data-sitekey="VOTRE_SITE_KEY"
     data-callback="onCaptchaSuccess"></div>

<!-- Iframes associés -->
<iframe src="https://www.google.com/recaptcha/api2/frame..."
        title="reCAPTCHA"></iframe>
```

**Patterns de détection**
- Classes CSS: `g-recaptcha`, `grecaptcha`
- Attributs: `data-sitekey`, `data-callback`
- Iframes depuis `google.com/recaptcha/api`
- Token caché: `<input name="g-recaptcha-response" type="hidden">`

**reCAPTCHA v2 Invisible**
```html
<div class="g-recaptcha"
     data-sitekey="VOTRE_SITE_KEY"
     data-size="invisible"></div>
```

**reCAPTCHA v3**
```javascript
// Pas d'élément DOM visible
// Détection par les requêtes réseau
<script src="https://www.google.com/recaptcha/api.js?render=VOTRE_SITE_KEY"></script>
```

---

### 2. Patterns HTML de hCaptcha

**hCaptcha Standard**
```html
<!-- Conteneur avec classe h-captcha -->
<div class="h-captcha"
     data-sitekey="YOUR_SITEKEY"
     data-theme="light"></div>

<!-- Script de chargement -->
<script src="https://js.hcaptcha.com/1/api.js" async defer></script>

<!-- Iframes hCaptcha -->
<iframe src="https://hcaptcha.com/captcha/..."
        title="hCaptcha"></iframe>
```

**Patterns de détection**
- Classes CSS: `h-captcha`
- Attributs: `data-sitekey`, `data-theme`, `data-callback`
- Iframes depuis `hcaptcha.com`
- Token response: `<textarea id="h-captcha-response"></textarea>`

---

### 3. Code de Détection Python

```python
from html.parser import HTMLParser
from typing import Dict, List, Optional
import re

class CaptchaDetector:
    """Détecte les captchas reCAPTCHA et hCaptcha dans le HTML"""

    RECAPTCHA_V2_PATTERN = r'class=["\']g-recaptcha["\']'
    RECAPTCHA_V3_PATTERN = r'recaptcha/api\.js\?render='
    HCAPTCHA_PATTERN = r'class=["\']h-captcha["\']'
    HCAPTCHA_SCRIPT = r'js\.hcaptcha\.com'

    @staticmethod
    def detect_recaptcha_v2(html: str) -> bool:
        """Détecte reCAPTCHA v2 (checkbox ou invisible)"""
        return bool(re.search(CaptchaDetector.RECAPTCHA_V2_PATTERN, html))

    @staticmethod
    def detect_recaptcha_v3(html: str) -> bool:
        """Détecte reCAPTCHA v3"""
        return bool(re.search(CaptchaDetector.RECAPTCHA_V3_PATTERN, html))

    @staticmethod
    def detect_hcaptcha(html: str) -> bool:
        """Détecte hCaptcha"""
        has_div = bool(re.search(CaptchaDetector.HCAPTCHA_PATTERN, html))
        has_script = bool(re.search(CaptchaDetector.HCAPTCHA_SCRIPT, html))
        return has_div or has_script

    @staticmethod
    def extract_sitekey(html: str) -> Optional[str]:
        """Extrait la clé de site captcha si présente"""
        patterns = [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'sitekey:["\']([^"\']+)["\']',
            r'render=([A-Za-z0-9_-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def detect_any_captcha(html: str) -> Dict[str, bool]:
        """Détecte tous les types de captchas"""
        return {
            'recaptcha_v2': CaptchaDetector.detect_recaptcha_v2(html),
            'recaptcha_v3': CaptchaDetector.detect_recaptcha_v3(html),
            'hcaptcha': CaptchaDetector.detect_hcaptcha(html),
            'has_sitekey': CaptchaDetector.extract_sitekey(html) is not None
        }
```

---

### 4. Stratégie de Retry avec Rotation IP (Tenacity + Proxies)

**Architecture Recommandée**
```
Requête initiale
    ↓
[Crawl4AI + Stealth Mode]
    ↓
Captcha détecté ? → Oui → Rotate IP + Retry (Tenacity)
    ↓ Non                  ↓
    Success            [Wait exponential backoff]
                            ↓
                        Retry avec nouveau proxy
                            ↓
                        Max tentatives? → Oui → Log + Abandon
                        ↓ Non
                        Retry avec proxy suivant
```

**Implémentation Complète**

```python
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
from crawl4ai import AsyncWebCrawler, BrowserConfig
import logging
import random
from typing import Dict, List

logger = logging.getLogger(__name__)

class CaptchaHandlingCrawler:
    """Crawler avec détection et retry avec rotation IP"""

    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.current_proxy_index = 0
        self.logger = logger

    def get_next_proxy(self) -> str:
        """Récupère le prochain proxy en rotation"""
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    async def _crawl_single(self, url: str, proxy: str) -> Dict:
        """Effectue un seul crawl avec un proxy"""
        browser_config = BrowserConfig(
            enable_stealth=True,
            proxy=proxy if proxy else None,
            headless=True
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url)

            # Détection captcha
            detection = CaptchaDetector.detect_any_captcha(result.html)
            is_blocked = result.status_code in [403, 429]

            return {
                'success': not (any(detection.values()) or is_blocked),
                'html': result.html,
                'status_code': result.status_code,
                'captcha_detected': detection,
                'proxy_used': proxy
            }

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.INFO)
    )
    async def crawl_with_retry(self, url: str) -> Dict:
        """
        Crawl avec retry et rotation IP.

        Stratégie:
        - 1ère tentative: Sans proxy (plus rapide)
        - 2-5ème tentatives: Avec rotation IP
        - Wait: 2^x * 2 secondes (min 4s, max 60s)
        """
        attempt_num = getattr(self.crawl_with_retry, 'retry_num', 0)
        use_proxy = attempt_num > 0
        proxy = self.get_next_proxy() if use_proxy else None

        self.logger.info(f"Attempt {attempt_num + 1} for {url}" +
                        (f" with proxy {proxy}" if proxy else " without proxy"))

        result = await self._crawl_single(url, proxy)

        if not result['success']:
            self.logger.warning(
                f"Captcha/Block detected: {result['captcha_detected']}, "
                f"Status: {result['status_code']}"
            )
            raise Exception(f"Captcha detected on attempt {attempt_num + 1}")

        self.logger.info(f"Success for {url} with proxy {result['proxy_used']}")
        return result
```

---

### 5. Configuration Optimale de Retry

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| **Max tentatives** | 5 | Équilibre entre flexibilité et coûts |
| **Initial delay** | 4s | Évite les blocages immédiats |
| **Max delay** | 60s | Respecte les limites serveur |
| **Exponential base** | 2 | Croissance rapide pour éviter spam |
| **Proxy rotation** | À chaque retry | Force le changement d'IP |
| **User-Agent rotation** | À chaque tentative | Augmente la légitimité |

**Délais Progressifs**
```
Tentative 1: Pas de proxy, attendre 0s
Tentative 2: Proxy 1, attendre 4s (2^1 * 2)
Tentative 3: Proxy 2, attendre 8s (2^2 * 2)
Tentative 4: Proxy 3, attendre 16s (2^3 * 2)
Tentative 5: Proxy 4, attendre 32s (2^4 * 2)
```

---

### 6. Best Practices pour Minimiser les Captchas

**Préventif**
```python
# ✅ Utiliser des proxies résidentiels (Decodo)
# → Clés résidentiels = +95% moins de captchas

# ✅ Ajouter des délais aléatoires
import random
import asyncio

async def crawl_with_delays(urls: List[str]):
    for url in urls:
        delay = random.uniform(2, 8)  # 2-8 secondes
        await asyncio.sleep(delay)
        # Crawl...

# ✅ Rotation user-agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0"
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)
```

**Mode Stealth**
```python
# ✅ Activer stealth mode
browser_config = BrowserConfig(
    enable_stealth=True,  # Masque les indicateurs bot
    headless=True,
    ignore_https_errors=True,
    extra_http_headers={
        'Accept-Language': 'fr-FR,fr;q=0.9',
        'User-Agent': get_random_user_agent()
    }
)
```

---

## Tenacity

### 1. @retry Decorator - Utilisation Basique

**Explication**
Le décorateur `@retry` est le point d'entrée principal de Tenacity. Il enveloppe une fonction avec une logique de retry automatique.

**Exemple de Code**

```python
from tenacity import retry, stop_after_attempt

# Basique - retente indéfiniment sur exception
@retry
def unreliable_function():
    raise Exception("Échec temporaire")

# Avancé - avec limite d'attempts et wait strategy
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def robust_api_call():
    # Retente jusqu'à 5 fois avec backoff exponentiel
    return requests.get('https://api.example.com/data')
```

**Source** : https://tenacity.readthedocs.io/en/latest/api.html

---

### 2. Wait Strategies - Exponential Backoff et Jitter

**Explication**
Les stratégies d'attente contrôlent les délais entre les tentatives de retry. L'exponential backoff augmente progressivement les délais pour éviter de surcharger un service défaillant. Le jitter (aléatoire) prévient le problème du "thundering herd".

**Exemples de Code**

```python
from tenacity import (
    retry, wait_fixed, wait_exponential,
    wait_random_exponential, wait_random, wait_chain
)

# Fixed wait - délai constant
@retry(wait=wait_fixed(2))
def simple_retry():
    pass

# Exponential backoff - 2^x * multiplier secondes
@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def exponential_retry():
    # Attend 4s minimum, jusqu'à 10s max
    pass

# Exponential avec jitter aléatoire
@retry(wait=wait_random_exponential(multiplier=1, max=60))
def jitter_retry():
    # Attendu aléatoire jusqu'à 2^x * 1 secondes, max 60s
    pass

# Combinaison : 3s fixe + 0-2s aléatoire
@retry(wait=wait_fixed(3) + wait_random(0, 2))
def combined_wait():
    pass

# Chaîné - stratégies différentes selon tentatives
@retry(wait=wait_chain(
    wait_fixed(1),
    wait_fixed(5),
    wait_fixed(10)
))
def chained_wait():
    # 1s pour 1ère tentative, 5s pour 2e, 10s pour 3e+
    pass
```

**Source** : https://tenacity.readthedocs.io/en/latest/index.html#wait-strategies

---

### 3. Async Support - Retry avec Async/Await

**Explication**
Tenacity supporte nativement les coroutines asyncio avec sleeps asynchrones. Le décorateur `@retry` fonctionne directement sur les fonctions `async def`.

**Exemples de Code**

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Async basique avec décorateur
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.example.com/data') as resp:
            return await resp.json()

# Utilisation
async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

```python
# AsyncRetrying pour boucles sans décorateur
from tenacity import AsyncRetrying, stop_after_attempt

async def process_with_retry():
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):
        with attempt:
            # Votre code asynchrone ici
            await some_async_operation()

asyncio.run(process_with_retry())
```

**Source** : https://tenacity.readthedocs.io/en/latest/index.html#retrying-async

---

### 4. Points Clés à Retenir

| Concept | Usage Pattern |
|---------|---------------|
| **Stop Conditions** | `stop_after_attempt(N)`, `stop_after_delay(seconds)` |
| **Retry Conditions** | `retry_if_exception_type(Exception)`, `retry_if_result(predicate)` |
| **Wait Strategies** | Combinables avec `+` ou `\|` : fixed, exponential, jitter, chain |
| **Async** | Décorateur `@retry` ou classe `AsyncRetrying`, sleeps natifs |

---

## Dokploy

### 1. Dockerfile Best Practices (Optimisation pour Dokploy)

**Description**
Dokploy supporte plusieurs types de build dont Dockerfile avec chemins configurables. Les meilleures pratiques recommandent d'utiliser des builds multi-stage avec Alpine Linux pour minimiser la taille des images et les ressources de production.

**Configuration**
```dockerfile
# Multi-stage build pour production
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV NODE_ENV=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
CMD ["node", "dist/index.js"]
```

**Champs à configurer dans Dokploy**
- **Dockerfile Path** : `Dockerfile` (ou chemin personnalisé)
- **Docker Context Path** : `.` (répertoire racine)
- **Docker Build Stage** : Optionnel, pour les builds multi-stage

**Bonnes pratiques**
- Utiliser Alpine Linux pour réduire la taille des images
- Implémenter des builds multi-stage pour les applications de production
- Copier uniquement les fichiers nécessaires du stage de build au stage final
- Définir `NODE_ENV=production` pour optimiser les dépendances

**Source** : https://docs.dokploy.com/docs/core/applications/build-type

---

### 2. Gestion des Variables d'Environnement (Env Vars)

**Description**
Dokploy propose un système à trois niveaux pour gérer les variables d'environnement.

**Trois niveaux de variables**

**Niveau Projet (Partagé)**
```
Variables accessibles à tous les services du projet
Syntaxe de référence : ${{project.VARIABLE_NAME}}
Exemple : DATABASE_URL=postgresql://postgres:postgres@database:5432/postgres
```

**Niveau Environnement**
```
Spécifiques à un environnement (staging, production)
Syntaxe de référence : ${{environment.VARIABLE_NAME}}
Permet des configurations différentes par environnement
```

**Niveau Service**
```
Spécifiques à un service individuel
Affichage dans la section "Environment" de chaque service
Variable automatique : DOKPLOY_DEPLOY_URL (en preview deployments)
```

**Configuration des multiline variables**
```
Pour les clés SSH ou certificats, encadrer avec des guillemets doubles :
"-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQE...
-----END PRIVATE KEY-----"
```

**Meilleures pratiques**
- Utiliser les variables partagées pour les configurations répétitives (credentials, URLs)
- Nommer les variables de manière descriptive (ex: `DB_PRIMARY_HOST`)
- Documenter le rôle de chaque variable pour la maintenance
- Garder les secrets sensibles au niveau projet ou service

**Source** : https://docs.dokploy.com/docs/core/variables

---

### 3. Deployment Workflow (Flux de Déploiement)

**Description**
Dokploy recommande une approche de déploiement en production sans build sur le serveur. Utiliser une pipeline CI/CD (GitHub Actions, GitLab CI) pour construire et publier les images Docker, puis les déployer sur Dokploy avec contrôle de santé et rollback automatique.

**Architecture recommandée**

```
1. Développement local → Push vers Git
2. Pipeline CI/CD → Build Docker image
3. Registry (DockerHub, GitLab Registry) → Stockage image
4. Dokploy → Pull et déploiement du pre-built image
5. Health Checks → Validation de déploiement
6. Rollback automatique si défaillance
```

**Configuration de la Pipeline (exemple GitHub Actions)**
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t registry/app:latest .
      - name: Push to registry
        run: docker push registry/app:latest
      - name: Trigger Dokploy deployment
        run: curl -X POST https://dokploy-instance/api/deploy
```

**Meilleures pratiques production**
- Construire les images en CI/CD
- Déployer des images pré-construites (pas de build sur le serveur)
- Configurer des health checks pour chaque service
- Implémenter des rollbacks automatiques
- Utiliser des volumes persistants pour les données
- Monitorer les déploiements et les logs en temps réel

**Sources**
- https://docs.dokploy.com/docs/core/applications/going-production
- https://docs.dokploy.com/docs/core/docker-compose
- https://docs.dokploy.com/docs/core/applications/advanced

---

## Ressources Additionnelles

| Technologie | Documentation Principale |
|-------------|--------------------------|
| FastAPI | https://fastapi.tiangolo.com/ |
| Pydantic v2 | https://docs.pydantic.dev/latest/ |
| Crawl4AI | https://docs.crawl4ai.com/ |
| Decodo | https://help.decodo.com/docs |
| Tenacity | https://tenacity.readthedocs.io/ |
| Dokploy | https://docs.dokploy.com/ |

---

**Dernière validation** : 16 novembre 2025
