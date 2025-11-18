---
title: "Story 3: Search endpoint basique (mock)"
scope: "specs"
category: "user-story"
epic: "Epic 1: API Foundation"
story_points: 8
priority: "high"
status: "in_progress"
dependencies: ["story-1", "story-2"]
date: 2025-01-18
keywords: [api, models, pydantic, fastapi, mock, tdd]
technologies: [FastAPI, Pydantic v2, pytest, TestClient]
business_value: "API testable par client, contrat request/response validé"
acceptance_criteria:
  - "Client peut appeler POST /search-flights"
  - "Retourne JSON valide SearchResponse"
  - "Validation Pydantic catch erreurs input"
  - "Tests unitaires Models: 21 tests passent"
---

# Story 3: Search endpoint basique (mock)

## 🎯 Contexte Business

**Besoin utilisateur**:
- Rechercher vols multi-destinations (2-10 villes)
- Obtenir Top 10 meilleurs prix rapidement (SLA: <30s)
- Format JSON standard (intégration client facile)

**Contraintes métier**:
- Max 10 destinations (limite complexité combinatoire)
- Top 10 résultats suffisants (pas de pagination MVP)
- Budget proxies limité (~50€/mois) → optimiser requêtes

**Valeur business**:
- ✅ Client peut tester API (Postman/curl)
- ✅ Contrat request/response validé (évite malentendus)
- ✅ Foundation pour intégration Google Flights (Story 4)
- ✅ Feedback rapide UX (temps réponse, format JSON)

**Métriques succès**:
- Response time mock data: <100ms
- Validation Pydantic: 100% edge cases couverts
- Tests intégration: POST /search retourne 200 + JSON valide

---

## 📋 Spécifications Techniques

### 1. Models (Pydantic v2)

#### 1.1 DateRange

**Description**: Représente une plage de dates pour la recherche de vols.

**Fichier**: `app/models/request.py`

**Schéma**:

```python
class DateRange(BaseModel):
    start: str
    end: str
```

**Champs**:

| Champ | Type | Requis | Description | Format | Contraintes |
|-------|------|--------|-------------|--------|-------------|
| `start` | `str` | Oui | Date de début de la plage | ISO 8601 `YYYY-MM-DD` | Doit être < `end` |
| `end` | `str` | Oui | Date de fin de la plage | ISO 8601 `YYYY-MM-DD` | Doit être > `start` |

**Formats acceptés**:
- ✅ `"2025-06-01"` (ISO 8601)
- ❌ `"01/06/2025"` (format français)
- ❌ `"2025-6-1"` (sans zéros leading)

**Validation cross-champs**:

```python
@model_validator(mode='after')
def validate_date_order(self) -> 'DateRange':
    """Valide que start < end."""
    if self.start >= self.end:
        raise ValueError('start date must be before end date')
    return self
```

**Comportement**:
- Validation exécutée **après** parsing des champs individuels
- Utilise `mode='after'` pour accéder aux valeurs validées
- Lève `ValueError` si `start >= end`

**Exemple erreur**:

```python
# Input invalide
DateRange(start="2025-06-15", end="2025-06-01")

# Erreur levée
ValidationError: 1 validation error for DateRange
  Value error, start date must be before end date
```

#### 1.2 Flight

**Description**: Représente un vol individuel dans la recherche multi-destinations.

**Fichier**: `app/models/request.py`

**Schéma**:

```python
class Flight(BaseModel):
    origin: str
    destination: str
    departure_date: str | None = None
    return_date: str | None = None
```

**Champs**:

| Champ | Type | Requis | Défaut | Description | Format |
|-------|------|--------|--------|-------------|--------|
| `origin` | `str` | Oui | - | Ville de départ | Nom de ville (ex: "Paris") |
| `destination` | `str` | Oui | - | Ville de destination | Nom de ville (ex: "Tokyo") |
| `departure_date` | `str \| None` | Non | `None` | Date de départ | ISO 8601 `YYYY-MM-DD` ou `None` |
| `return_date` | `str \| None` | Non | `None` | Date de retour | ISO 8601 `YYYY-MM-DD` ou `None` |

**Type hints**:
- ✅ Utilise syntaxe PEP 695 : `str | None` (pas `Optional[str]`)
- ✅ Défaut explicite : `= None` pour champs optionnels (Pydantic v2)

**Utilisation**:
- Généré automatiquement par `CombinationGenerator` à partir de `SearchRequest.destinations`
- Champs `departure_date` et `return_date` calculés depuis `SearchRequest.date_range`

#### 1.3 SearchRequest

**Description**: Requête principale pour rechercher des vols multi-destinations.

**Fichier**: `app/models/request.py`

**Schéma**:

```python
class SearchRequest(BaseModel):
    destinations: list[str]
    date_range: DateRange
    max_results: int = 10
```

**Champs**:

| Champ | Type | Requis | Défaut | Description | Contraintes |
|-------|------|--------|--------|-------------|-------------|
| `destinations` | `list[str]` | Oui | - | Liste des destinations | Min: 2, Max: 10, Unicité requise, Non-vides |
| `date_range` | `DateRange` | Oui | - | Plage de dates de recherche | Objet `DateRange` validé |
| `max_results` | `int` | Non | `10` | Nombre maximum de résultats | Min: 1, Max: 50 |

**Contraintes détaillées**:

**destinations**:
- **Minimum**: 2 destinations (recherche multi-city nécessite au moins 2 villes)
- **Maximum**: 10 destinations (limite performance + coût proxies)
- **Unicité**: Pas de doublons (ex: `["Paris", "Paris"]` invalide)
- **Non-vides**: Chaque destination doit être non-vide après strip (ex: `["  "]` invalide)

**max_results**:
- **Minimum**: 1 (au moins un résultat)
- **Maximum**: 50 (limite raisonnable pour éviter surcharge)
- **Défaut**: 10 (Top 10 résultats)

**Type hints**:
- ✅ `list[str]` (PEP 695, pas `List[str]`)
- ✅ Pas de `Optional` pour `destinations` et `date_range` (obligatoires)

**Validations**:

**Validation 1: Longueur liste destinations**

```python
@field_validator('destinations', mode='after')
@classmethod
def validate_destinations_length(cls, v: list[str]) -> list[str]:
    """Valide que la liste contient entre 2 et 10 destinations."""
    if len(v) < 2:
        raise ValueError('at least 2 destinations required')
    if len(v) > 10:
        raise ValueError('maximum 10 destinations allowed')
    return v
```

**Exemple erreur**:
```python
SearchRequest(destinations=["Paris"], date_range=DateRange(...))
# → ValidationError: Value error, at least 2 destinations required
```

**Validation 2: Unicité destinations**

```python
@field_validator('destinations', mode='after')
@classmethod
def validate_destinations_unique(cls, v: list[str]) -> list[str]:
    """Valide que toutes les destinations sont uniques."""
    if len(v) != len(set(v)):
        raise ValueError('destinations must be unique')
    return v
```

**Exemple erreur**:
```python
SearchRequest(destinations=["Paris", "Tokyo", "Paris"], date_range=DateRange(...))
# → ValidationError: Value error, destinations must be unique
```

**Validation 3: Destinations non-vides**

```python
@field_validator('destinations', mode='after')
@classmethod
def validate_destinations_not_empty(cls, v: list[str]) -> list[str]:
    """Valide que chaque destination est non-vide après strip."""
    for dest in v:
        if not dest.strip():
            raise ValueError('destinations cannot be empty or whitespace')
    return v
```

**Exemple erreur**:
```python
SearchRequest(destinations=["Paris", "  ", "Tokyo"], date_range=DateRange(...))
# → ValidationError: Value error, destinations cannot be empty or whitespace
```

**Validation 4: Contraintes max_results**

```python
@field_validator('max_results', mode='after')
@classmethod
def validate_max_results(cls, v: int) -> int:
    """Valide que max_results est entre 1 et 50."""
    if v < 1:
        raise ValueError('max_results must be at least 1')
    if v > 50:
        raise ValueError('max_results cannot exceed 50')
    return v
```

**Exemple erreur**:
```python
SearchRequest(destinations=["Paris", "Tokyo"], date_range=DateRange(...), max_results=100)
# → ValidationError: Value error, max_results cannot exceed 50
```

#### 1.4 FlightResult

**Description**: Représente un résultat de vol scraped depuis Google Flights.

**Fichier**: `app/models/response.py`

**Schéma**:

```python
class FlightResult(BaseModel):
    price: float
    airline: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    stops: int
```

**Champs**:

| Champ | Type | Requis | Description | Format | Exemple |
|-------|------|--------|-------------|--------|---------|
| `price` | `float` | Oui | Prix total du vol | Nombre décimal positif | `1250.50` |
| `airline` | `str` | Oui | Nom de la compagnie aérienne | Texte | `"Air France"` |
| `departure_time` | `str` | Oui | Heure de départ | ISO 8601 `YYYY-MM-DDTHH:MM:SS` | `"2025-06-01T10:30:00"` |
| `arrival_time` | `str` | Oui | Heure d'arrivée | ISO 8601 `YYYY-MM-DDTHH:MM:SS` | `"2025-06-01T22:15:00"` |
| `duration_minutes` | `int` | Oui | Durée totale du vol en minutes | Entier positif | `705` (11h45) |
| `stops` | `int` | Oui | Nombre d'escales | Entier >= 0 | `0` (direct), `1` (1 escale) |

**Type hints**:
- ✅ Types précis : `float`, `str`, `int` (pas de `Any`)
- ✅ Format ISO 8601 pour dates/heures (parsing facile côté client)

**Parsing**:
- Extrait depuis HTML Google Flights via `FlightParserService`
- Utilise `JsonCssExtractionStrategy` (pas de LLM)
- Sélecteurs CSS spécifiques à Google Flights

#### 1.5 SearchStats

**Description**: Statistiques d'exécution de la recherche pour monitoring et debugging.

**Fichier**: `app/models/response.py`

**Schéma**:

```python
class SearchStats(BaseModel):
    total_combinations: int
    successful_searches: int
    failed_searches: int
    total_duration_seconds: float
```

**Champs**:

| Champ | Type | Requis | Description | Exemple |
|-------|------|--------|-------------|---------|
| `total_combinations` | `int` | Oui | Nombre total de combinaisons multi-city générées | `12` |
| `successful_searches` | `int` | Oui | Nombre de recherches réussies (parsing OK) | `10` |
| `failed_searches` | `int` | Oui | Nombre de recherches échouées (timeout, erreur) | `2` |
| `total_duration_seconds` | `float` | Oui | Durée totale de la recherche en secondes | `45.32` |

**Utilisation**:
- **Monitoring**: Calculer taux de succès, performance
- **Debugging**: Identifier problèmes (taux échec élevé → proxies/rate limits)
- **Business**: Estimer coûts (bandwidth proxies)

**Métriques calculées**:
- **Taux de succès**: `successful_searches / total_combinations * 100`
- **Moyenne par recherche**: `total_duration_seconds / total_combinations`

**Note importante**: Le champ `captcha_detected` sera ajouté en **Phase 7 (post-MVP)** uniquement si le monitoring montre >5% de blocages Google Flights. Pour le MVP, on se concentre sur la détection en logs uniquement, pas de métrique captcha dans SearchStats.

**Exemple valeurs**:
```json
{
  "total_combinations": 12,
  "successful_searches": 10,
  "failed_searches": 2,
  "total_duration_seconds": 45.32
}
```

#### 1.6 SearchResponse

**Description**: Réponse complète de l'endpoint `/api/v1/search-flights`.

**Fichier**: `app/models/response.py`

**Schéma**:

```python
class SearchResponse(BaseModel):
    results: list[FlightResult]
    stats: SearchStats
    search_id: str
```

**Champs**:

| Champ | Type | Requis | Description | Contraintes |
|-------|------|--------|-------------|-------------|
| `results` | `list[FlightResult]` | Oui | Liste des meilleurs vols trouvés | Max 10 résultats (Top 10) |
| `stats` | `SearchStats` | Oui | Statistiques d'exécution | Objet `SearchStats` complet |
| `search_id` | `str` | Oui | Identifiant unique de la recherche | UUID v4 |

**Contraintes**:
- `results` limité à 10 éléments maximum (Top 10)
- `search_id` généré automatiquement (UUID v4)
- `stats` toujours présent (même si `results` vide)

**Type hints**:
- ✅ `list[FlightResult]` (PEP 695)
- ✅ Composition de models (nested Pydantic models)

**Relations entre models**:
```
SearchResponse
├── results: list[FlightResult]    (1:N)
│   └── FlightResult
│       ├── price
│       ├── airline
│       ├── departure_time
│       ├── arrival_time
│       ├── duration_minutes
│       └── stops
├── stats: SearchStats              (1:1)
│   ├── total_combinations
│   ├── successful_searches
│   ├── failed_searches
│   └── total_duration_seconds
└── search_id: str (UUID v4)
```

**Génération search_id**:
```python
import uuid

search_id = str(uuid.uuid4())
# Exemple: "550e8400-e29b-41d4-a716-446655440000"
```

**Comportement**:
- Triés par prix croissant (moins cher en premier)
- Maximum 10 résultats même si plus de vols trouvés
- Liste vide possible si aucun vol trouvé (stats toujours présent)

---

### 2. SearchService (mock)

**Rôle**: Retourner données simulées pour valider contrat API avant intégration Google Flights.

**Fichier**: `app/services/search_service.py`

**Interface**:
```python
async def search_flights(request: SearchRequest) -> SearchResponse:
    """Retourne mock data pour valider contrat API."""
```

**Comportement mock**:
- Générer 3 FlightResult aléatoires (prix 500-2000€)
- SearchStats: `total_combinations=3`, `successful_searches=3`, `failed_searches=0`
- `search_id`: UUID v4
- Duration: random 1-5 secondes (simule latence réaliste)

**Validation**:
- Input: SearchRequest valide (Pydantic validation)
- Output: SearchResponse valide (Top 10 max)

**Exemple implémentation**:
```python
import uuid
import random
from datetime import datetime

async def search_flights(request: SearchRequest) -> SearchResponse:
    # Mock flight results
    results = [
        FlightResult(
            price=round(random.uniform(500, 2000), 2),
            airline=random.choice(["Air France", "British Airways", "Lufthansa"]),
            departure_time=f"2025-06-01T{random.randint(6,18):02d}:00:00",
            arrival_time=f"2025-06-01T{random.randint(12,23):02d}:00:00",
            duration_minutes=random.randint(300, 800),
            stops=random.randint(0, 2)
        )
        for _ in range(3)
    ]

    # Mock stats
    stats = SearchStats(
        total_combinations=3,
        successful_searches=3,
        failed_searches=0,
        total_duration_seconds=round(random.uniform(1.0, 5.0), 2)
    )

    return SearchResponse(
        results=sorted(results, key=lambda x: x.price)[:request.max_results],
        stats=stats,
        search_id=str(uuid.uuid4())
    )
```

---

### 3. API Route

**Endpoint**: `POST /api/v1/search-flights`

**Fichier**: `app/api/routes.py`

**Request**:
- Body: SearchRequest (JSON)
- Content-Type: application/json

**Response**:
- Body: SearchResponse (JSON)
- Content-Type: application/json

**Status codes**:
- 200: Succès (données retournées)
- 400: Validation error (Pydantic)
- 422: Unprocessable Entity (format JSON invalide)
- 500: Internal server error

**Implémentation**:
```python
from fastapi import APIRouter, HTTPException
from app.models.request import SearchRequest
from app.models.response import SearchResponse
from app.services.search_service import search_flights

router = APIRouter(prefix="/api/v1", tags=["flights"])

@router.post("/search-flights", response_model=SearchResponse)
async def search_flights_endpoint(request: SearchRequest) -> SearchResponse:
    """Search for multi-destination flights."""
    try:
        return await search_flights(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Exemple curl**:
```bash
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "destinations": ["Paris", "Tokyo"],
    "date_range": {
      "start": "2025-06-01",
      "end": "2025-06-15"
    },
    "max_results": 10
  }'
```

---

## 🧪 Tests

### Tests unitaires (TDD)

**Format recommandé: AAA (Arrange/Act/Assert)**

#### DateRange (4 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_date_range_valid` | `{"start": "2025-06-01", "end": "2025-06-15"}` | Objet `DateRange` créé | Vérifie happy path |
| 2 | `test_date_range_start_equals_end` | `{"start": "2025-06-01", "end": "2025-06-01"}` | `ValidationError` | Vérifie start < end |
| 3 | `test_date_range_start_after_end` | `{"start": "2025-06-15", "end": "2025-06-01"}` | `ValidationError` | Vérifie ordre inversé |
| 4 | `test_date_range_missing_fields` | `{"start": "2025-06-01"}` | `ValidationError` | Vérifie champs obligatoires |

#### Flight (2 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 5 | `test_flight_valid_all_fields` | Tous champs remplis | Objet `Flight` créé | Vérifie happy path |
| 6 | `test_flight_optional_dates_none` | `{"origin": "Paris", "destination": "Tokyo"}` | `departure_date=None`, `return_date=None` | Vérifie défauts optionnels |

#### SearchRequest (9 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 7 | `test_search_request_valid_minimal` | 2 destinations + date_range | `max_results=10` (défaut) | Vérifie happy path minimal |
| 8 | `test_search_request_valid_custom_max_results` | Ajout `max_results=20` | Objet créé avec 20 | Vérifie override défaut |
| 9 | `test_search_request_destinations_too_few` | 1 destination | `ValidationError` | Vérifie min 2 destinations |
| 10 | `test_search_request_destinations_too_many` | 11 destinations | `ValidationError` | Vérifie max 10 destinations |
| 11 | `test_search_request_destinations_duplicates` | `["Paris", "Tokyo", "Paris"]` | `ValidationError` | Vérifie unicité |
| 12 | `test_search_request_destinations_empty_string` | `["Paris", "  ", "Tokyo"]` | `ValidationError` | Vérifie non-vides |
| 13 | `test_search_request_max_results_too_low` | `max_results=0` | `ValidationError` | Vérifie min 1 |
| 14 | `test_search_request_max_results_too_high` | `max_results=100` | `ValidationError` | Vérifie max 50 |
| 15 | `test_search_request_nested_date_range_invalid` | DateRange invalide | `ValidationError` | Vérifie validation cascade |

#### FlightResult (2 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 16 | `test_flight_result_valid` | Tous champs valides | Objet créé | Vérifie happy path |
| 17 | `test_flight_result_missing_fields` | Omission `airline` | `ValidationError` | Vérifie champs requis |

#### SearchStats (1 test)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 18 | `test_search_stats_valid` | Tous champs valides | Objet créé | Vérifie happy path |

#### SearchResponse (3 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 19 | `test_search_response_valid_with_results` | 5 FlightResult + stats + UUID | Objet créé | Vérifie happy path complet |
| 20 | `test_search_response_empty_results` | `results=[]` + stats + UUID | Objet créé | Vérifie liste vide autorisée |
| 21 | `test_search_response_nested_validation` | FlightResult invalide | `ValidationError` | Vérifie validation cascade |

**Total tests unitaires Models**: **21 tests**

#### SearchService mock (5 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 22 | `test_search_service_returns_mock_data` | SearchRequest valide | 3 FlightResult | Vérifie retourne résultats mock |
| 23 | `test_search_service_generates_uuid` | SearchRequest valide | `search_id` UUID v4 | Vérifie UUID valide |
| 24 | `test_search_service_stats_coherent` | SearchRequest valide | SearchStats cohérents | Vérifie total_combinations=3 |
| 25 | `test_search_service_async` | `await search_flights()` | SearchResponse | Vérifie fonction async |
| 26 | `test_search_service_different_requests` | 2 requêtes | Données différentes | Vérifie randomness |

**Total tests unitaires SearchService**: **5 tests**

#### Route (8 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 27 | `test_route_post_search_valid` | POST données valides | 200 + SearchResponse | Vérifie happy path |
| 28 | `test_route_validation_error_destinations` | Destinations < 2 | 400 + error message | Vérifie validation Pydantic |
| 29 | `test_route_validation_error_dates` | start > end | 400 + error message | Vérifie validation dates |
| 30 | `test_route_validation_error_max_results` | max_results > 50 | 400 + error message | Vérifie validation max_results |
| 31 | `test_route_response_format` | POST valide | JSON SearchResponse | Vérifie structure response |
| 32 | `test_route_response_time` | POST valide | Response <100ms | Vérifie performance mock |
| 33 | `test_route_openapi_docs` | GET /docs | 200 | Vérifie auto-docs FastAPI |
| 34 | `test_route_cors_headers` | POST valide | Headers CORS présents | Vérifie config CORS (si configuré) |

**Total tests unitaires Route**: **8 tests**

**Total tests unitaires Story 3**: **34 tests** (21 Models + 5 Service + 8 Route)

**Exemple code test AAA**:
```python
def test_search_request_valid_minimal():
    # Arrange: Setup input data
    request_data = {
        "destinations": ["Paris", "Tokyo"],
        "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
    }

    # Act: Execute model creation
    request = SearchRequest(**request_data)

    # Assert: Verify expected outcome
    assert len(request.destinations) == 2
    assert request.date_range.start == "2025-06-01"
    assert request.max_results == 10  # Défaut
```

---

### Tests intégration

**Format recommandé: Given/When/Then (BDD)**

**End-to-end API** (4 tests):

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_search_endpoint_happy_path` | App running | POST /search-flights données valides | 200 + JSON SearchResponse valide |
| 2 | `test_integration_multiple_requests_unique_ids` | App running | 2 requêtes POST | 2 search_id différents |
| 3 | `test_integration_validation_errors_422` | App running | POST JSON invalide | 422 + error detail |
| 4 | `test_integration_health_then_search` | App running | GET /health puis POST /search | 200 puis 200 |

**Total tests intégration**: **4 tests**

**Exemple code test Given/When/Then**:
```python
def test_integration_search_endpoint_happy_path():
    # Given: API running, valid request data
    client = TestClient(app)
    request_data = {
        "destinations": ["Paris", "Tokyo"],
        "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
    }

    # When: POST /search-flights
    response = client.post("/api/v1/search-flights", json=request_data)

    # Then: 200 + valid SearchResponse JSON
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "stats" in data
    assert "search_id" in data
    assert len(data["results"]) <= 10
```

---

### Exemples JSON

**Exemple 1: SearchRequest valide (minimal)**:
```json
{
  "destinations": ["Paris", "Tokyo"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

**Exemple 2: SearchRequest valide (complet)**:
```json
{
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-30"
  },
  "max_results": 20
}
```

**Exemple 3: SearchResponse attendue (succès)**:
```json
{
  "results": [
    {
      "price": 1250.50,
      "airline": "Air France",
      "departure_time": "2025-06-01T10:30:00",
      "arrival_time": "2025-06-01T22:15:00",
      "duration_minutes": 705,
      "stops": 0
    },
    {
      "price": 1380.00,
      "airline": "British Airways",
      "departure_time": "2025-06-02T08:00:00",
      "arrival_time": "2025-06-02T20:30:00",
      "duration_minutes": 750,
      "stops": 1
    },
    {
      "price": 1425.75,
      "airline": "Lufthansa",
      "departure_time": "2025-06-03T14:00:00",
      "arrival_time": "2025-06-04T02:45:00",
      "duration_minutes": 765,
      "stops": 1
    }
  ],
  "stats": {
    "total_combinations": 12,
    "successful_searches": 10,
    "failed_searches": 2,
    "total_duration_seconds": 45.32
  },
  "search_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Exemple 4: SearchResponse attendue (aucun résultat)**:
```json
{
  "results": [],
  "stats": {
    "total_combinations": 12,
    "successful_searches": 0,
    "failed_searches": 12,
    "total_duration_seconds": 38.21
  },
  "search_id": "7c3a8e2f-4b6d-4c1e-a9f3-2e5d6f8a9b0c"
}
```

---

## ✅ Critères d'acceptation

**Phase 4 (Specs) - En cours**:
- [x] Models Pydantic spécifiés (DateRange, Flight, SearchRequest, FlightResult, SearchStats, SearchResponse)
- [x] Validations Pydantic v2 documentées (field_validator, model_validator)
- [x] 21 tests unitaires Models listés
- [x] SearchStats corrigé (captcha_detected retiré du MVP)
- [x] SearchService mock spécifié (retourne 3 résultats aléatoires)
- [x] 5 tests unitaires SearchService listés
- [x] Route POST /search-flights spécifiée
- [x] 8 tests unitaires Route listés
- [x] 4 tests intégration end-to-end listés
- [x] Exemples JSON fournis (4 exemples)

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1: Models**
  - Écrire 21 tests unitaires (test_models.py)
  - Implémenter Models (request.py, response.py)
  - Tests Models passent ✅
- [ ] **TDD Phase 2: SearchService**
  - Écrire 5 tests unitaires (test_search_service.py)
  - Implémenter SearchService mock
  - Tests Service passent ✅
- [ ] **TDD Phase 3: Route**
  - Écrire 8 tests unitaires (test_api_routes.py)
  - Implémenter Route POST /search
  - Tests Route passent ✅
- [ ] **Tests intégration**: 4 tests end-to-end (TestClient)
- [ ] **Validation manuelle**: `curl -X POST http://localhost:8000/api/v1/search-flights`
- [ ] **Quality checks**: Ruff lint + format: 0 erreurs
- [ ] **Quality checks**: Mypy strict: 0 erreurs
- [ ] **Coverage**: ≥ 80% sur Models, Service, Route
- [ ] **Documentation**: OpenAPI docs auto-générées accessibles `/docs`

---

## 📝 Notes d'implémentation

**Dépendances**:
- **Story 1 (Health check)**: App FastAPI initialisée
- **Story 2 (Config + Logging)**: Settings Pydantic disponible pour injection

**Ordre TDD recommandé**:
1. **Models** (foundation, pas de dépendances)
2. **SearchService** (dépend Models)
3. **Route** (dépend Models + SearchService)
4. **Tests intégration** (valide assemblage)

**Fichiers créés/modifiés**:
- `app/models/request.py`: DateRange, Flight, SearchRequest
- `app/models/response.py`: FlightResult, SearchStats, SearchResponse
- `app/services/search_service.py`: search_flights() mock
- `app/api/routes.py`: POST /search-flights endpoint
- `tests/unit/test_models.py`: 21 tests unitaires Models
- `tests/unit/test_search_service.py`: 5 tests unitaires Service
- `tests/unit/test_api_routes.py`: 8 tests unitaires Route
- `tests/integration/test_api.py`: 4 tests intégration

**Commandes développement**:
```bash
# Tests unitaires story 3
pytest tests/unit/test_models.py tests/unit/test_search_service.py tests/unit/test_api_routes.py -v

# Tests intégration story 3
pytest tests/integration/test_api.py -v

# Tous tests story 3
pytest tests/unit/test_models.py tests/unit/test_search_service.py tests/unit/test_api_routes.py tests/integration/test_api.py -v

# Quality checks
ruff check . --fix && ruff format . && mypy app/

# Coverage story 3
pytest --cov=app/models --cov=app/services/search_service --cov=app/api/routes --cov-report=term-missing
```

**Commit message** (après implémentation complète):
```bash
git commit -m "feat(api): add search endpoint with mock data

- Implement Pydantic v2 Models (DateRange, Flight, SearchRequest, FlightResult, SearchStats, SearchResponse)
- Implement SearchService mock (returns 3 random flights)
- Implement POST /search-flights endpoint
- Add 34 unit tests + 4 integration tests
- Coverage: 95% on Models, Service, Route

Closes story-3"
```

**Temps estimé**:
- Specs (Phase 4): 2 heures (COMPLÉTÉ)
- Implémentation TDD (Phase 5): ~6 heures
  - Models: 2h
  - SearchService: 1h
  - Route: 1h
  - Tests intégration: 1h
  - Quality checks + fixes: 1h
- Total: ~8 heures (~8 story points)
