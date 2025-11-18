---
title: "Story 3: Search endpoint basique (mock)"
epic: "Epic 1: API Foundation"
story_points: 8
dependencies: ["story-2"]
date: "2025-18-11"
keywords: ["api", "search", "mock", "pydantic", "models", "fastapi", "endpoint", "validation"]
scope: ["specs"]
technologies: ["FastAPI", "Pydantic v2", "pytest", "TestClient"]
---

# 🎯 Contexte Business

## Besoin utilisateur

### Persona 1: Développeur Frontend Client API
- Besoin de tester l'intégration API immédiatement sans attendre l'implémentation complète du scraping
- Validation du contrat API (request/response) pour développer l'UI en parallèle
- Retour mock data réaliste pour prototyper affichage résultats vols
- Documentation OpenAPI auto-générée pour comprendre format JSON attendu

### Persona 2: Product Owner
- Besoin de démo rapide pour valider UX et recueillir feedback client early
- Validation hypothèses business : format données, champs pertinents, tri par prix
- Présentation prototype fonctionnel aux stakeholders avant investissement scraping

### Persona 3: Développeur Backend (ce projet)
- Besoin de valider architecture API avant complexité scraping
- Tests end-to-end de la stack FastAPI + Pydantic + validation
- Foundation solide pour intégrer services réels (crawler, parser) en Phase 5.4+

## Contraintes métier

### Contraintes techniques
- Pas de base de données : Mock data hardcodé en mémoire (liste Python statique)
- Pas d'appels externes : Aucune dépendance réseau (pas de Decodo, pas de Google Flights)
- Validation stricte : Pydantic doit rejeter toute requête invalide (status 422)
- Type safety : PEP 695 type hints obligatoires, Mypy strict mode

### Contraintes fonctionnelles
- Destinations minimum 2 : Validation `min_length=2` pour champ `destinations`
- Date range cohérent : `start` doit être strictement avant `end` (validation cross-champs)
- Top 10 résultats : Mock retourne maximum 10 vols (préparation ranking futur)
- Itinéraires réalistes : Mock data doit utiliser destinations de la requête

### Contraintes performance
- Response time < 100ms : Mock data en mémoire, pas de calcul complexe
- Pas de caching : Chaque requête génère une nouvelle liste mock (préparation services dynamiques futurs)

## Valeur business

- ✅ Validation contrat API early : Frontend peut démarrer développement immédiatement, réduction time-to-market de 2-3 semaines
- ✅ Feedback rapide stakeholders : Démo fonctionnelle avec mock data permet validation hypothèses business sans attendre scraping complet
- ✅ Dérisquage technique : Validation stack FastAPI + Pydantic + tests avant investissement scraping complexe (réduction risque d'erreurs architecturales coûteuses)
- ✅ Foundation solide : API ready pour plugger services réels (crawler, parser) en Phase 5.4 sans refactoring majeur
- ✅ Documentation auto-générée : OpenAPI schema disponible immédiatement pour client API (/docs endpoint FastAPI)

## Métriques succès

### Métriques fonctionnelles
- 100% requêtes valides retournent status 200 avec mock data cohérent
- 100% requêtes invalides retournent status 422 avec message erreur explicite Pydantic
- Mock data contient les destinations de la requête dans itinéraires générés

### Métriques qualité
- Coverage ≥ 80% sur modules models, services, routes
- 25+ tests passent (21 unitaires models + 5 service + 8 route + 4 intégration)
- Mypy strict mode : 0 erreur de type
- Ruff lint/format : 0 erreur

### Métriques techniques
- Response time < 100ms (p95) pour endpoint mock
- Taille response JSON < 5KB pour 10 résultats
- 0 dépendance externe (isolation complète pour tests rapides)

---

# 📋 Spécifications Techniques

## 1. Modèle DateRange (Pydantic BaseModel)

**Rôle** : Représente une plage de dates pour la recherche de vols, avec validation stricte du format ISO 8601 et cohérence des dates.

**Interface** :
```python
from pydantic import BaseModel, field_validator, model_validator

class DateRange(BaseModel):
    """Plage de dates pour recherche de vols."""

    start: str
    end: str

    @field_validator("start", "end", mode="after")
    @classmethod
    def validate_iso_format(cls, v: str) -> str:
        """Valide format ISO 8601 (YYYY-MM-DD)."""

    @model_validator(mode="after")
    def validate_start_before_end(self) -> "DateRange":
        """Valide que start < end."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `start` | `str` | Date début recherche | Format ISO 8601 (YYYY-MM-DD) |
| `end` | `str` | Date fin recherche | Format ISO 8601 (YYYY-MM-DD) |

**Validations** :

### field_validator: validate_iso_format
```python
@field_validator("start", "end", mode="after")
@classmethod
def validate_iso_format(cls, v: str) -> str:
    """Valide format ISO 8601 (YYYY-MM-DD)."""
    from datetime import datetime

    try:
        datetime.fromisoformat(v)
    except ValueError:
        raise ValueError(f"Date must be in ISO 8601 format (YYYY-MM-DD), got {v}")
    return v
```

### model_validator: validate_start_before_end
```python
@model_validator(mode="after")
def validate_start_before_end(self) -> "DateRange":
    """Valide que start < end."""
    from datetime import datetime

    start_date = datetime.fromisoformat(self.start)
    end_date = datetime.fromisoformat(self.end)

    if start_date >= end_date:
        raise ValueError(f"start date ({self.start}) must be before end date ({self.end})")

    return self
```

**Exemples** :

### Exemple 1: DateRange valide
```python
date_range = DateRange(start="2025-06-01", end="2025-06-15")
assert date_range.start == "2025-06-01"
assert date_range.end == "2025-06-15"
```

### Exemple 2: Format invalide
```python
# Lève ValidationError
DateRange(start="2025/06/01", end="2025-06-15")
# → Error: Date must be in ISO 8601 format (YYYY-MM-DD), got 2025/06/01
```

### Exemple 3: start >= end
```python
# Lève ValidationError
DateRange(start="2025-06-15", end="2025-06-01")
# → Error: start date (2025-06-15) must be before end date (2025-06-01)
```

---

## 2. Modèle SearchRequest (Pydantic BaseModel)

**Rôle** : Représente une requête de recherche de vols multi-destinations, avec validation stricte des champs.

**Interface** :
```python
from pydantic import BaseModel, field_validator

class SearchRequest(BaseModel):
    """Requête de recherche de vols multi-destinations."""

    destinations: list[str]
    date_range: DateRange
    max_stops: int | None = None

    @field_validator("destinations", mode="after")
    @classmethod
    def validate_destinations_min_length(cls, v: list[str]) -> list[str]:
        """Valide minimum 2 destinations."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `destinations` | `list[str]` | Liste villes à visiter | min_length=2, villes non vides |
| `date_range` | `DateRange` | Plage dates recherche | Modèle imbriqué DateRange validé |
| `max_stops` | `int \| None` | Nombre max escales (optionnel) | ≥ 0 si fourni, None par défaut |

**Validations** :

### field_validator: validate_destinations_min_length
```python
@field_validator("destinations", mode="after")
@classmethod
def validate_destinations_min_length(cls, v: list[str]) -> list[str]:
    """Valide minimum 2 destinations."""
    if len(v) < 2:
        raise ValueError(f"destinations must contain at least 2 cities, got {len(v)}")

    for city in v:
        if not city.strip():
            raise ValueError("destinations cannot contain empty strings")

    return v
```

**Exemples** :

### Exemple 1: SearchRequest valide
```python
request = SearchRequest(
    destinations=["Paris", "Tokyo", "New York"],
    date_range=DateRange(start="2025-06-01", end="2025-06-15"),
    max_stops=1
)
assert len(request.destinations) == 3
assert request.max_stops == 1
```

### Exemple 2: Destinations insuffisantes
```python
# Lève ValidationError
SearchRequest(
    destinations=["Paris"],
    date_range=DateRange(start="2025-06-01", end="2025-06-15")
)
# → Error: destinations must contain at least 2 cities, got 1
```

### Exemple 3: max_stops optionnel
```python
request = SearchRequest(
    destinations=["Paris", "Tokyo"],
    date_range=DateRange(start="2025-06-01", end="2025-06-15")
)
assert request.max_stops is None
```

**Exemple JSON Request** :
```json
{
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  },
  "max_stops": 1
}
```

---

## 3. Modèle FlightResult (Pydantic BaseModel)

**Rôle** : Représente un résultat de vol dans la réponse, avec validation stricte des champs métier.

**Interface** :
```python
from pydantic import BaseModel, field_validator
from typing import Literal

class FlightResult(BaseModel):
    """Résultat de vol unique."""

    itinerary: list[str]
    price: float
    currency: Literal["EUR", "USD"]
    departure_date: str
    return_date: str

    @field_validator("price", mode="after")
    @classmethod
    def validate_price_positive(cls, v: float) -> float:
        """Valide que price >= 0."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `itinerary` | `list[str]` | Liste villes parcours | min_length=2 |
| `price` | `float` | Prix total vol | ≥ 0 |
| `currency` | `Literal["EUR", "USD"]` | Devise prix | Valeurs limitées EUR ou USD |
| `departure_date` | `str` | Date départ | Format ISO 8601 (YYYY-MM-DD) |
| `return_date` | `str` | Date retour | Format ISO 8601 (YYYY-MM-DD) |

**Validations** :

### field_validator: validate_price_positive
```python
@field_validator("price", mode="after")
@classmethod
def validate_price_positive(cls, v: float) -> float:
    """Valide que price >= 0."""
    if v < 0:
        raise ValueError(f"price must be >= 0, got {v}")
    return v
```

**Exemples** :

### Exemple 1: FlightResult valide
```python
flight = FlightResult(
    itinerary=["Paris", "Tokyo", "New York"],
    price=1250.00,
    currency="EUR",
    departure_date="2025-06-01",
    return_date="2025-06-15"
)
assert flight.price == 1250.00
assert flight.currency == "EUR"
```

### Exemple 2: Prix négatif (invalide)
```python
# Lève ValidationError
FlightResult(
    itinerary=["Paris", "Tokyo"],
    price=-100.00,
    currency="EUR",
    departure_date="2025-06-01",
    return_date="2025-06-15"
)
# → Error: price must be >= 0, got -100.0
```

### Exemple 3: Currency invalide
```python
# Lève ValidationError
FlightResult(
    itinerary=["Paris", "Tokyo"],
    price=1000.00,
    currency="GBP",
    departure_date="2025-06-01",
    return_date="2025-06-15"
)
# → Error: Input should be 'EUR' or 'USD'
```

**Exemple JSON FlightResult** :
```json
{
  "itinerary": ["Paris", "Tokyo", "New York"],
  "price": 1250.00,
  "currency": "EUR",
  "departure_date": "2025-06-01",
  "return_date": "2025-06-15"
}
```

---

## 4. Modèle SearchResponse (Pydantic BaseModel)

**Rôle** : Représente la réponse complète de l'API avec métadonnées de recherche.

**Interface** :
```python
from pydantic import BaseModel
import uuid

class SearchResponse(BaseModel):
    """Réponse complète recherche vols."""

    results: list[FlightResult]
    search_id: str
    total_results: int

    @classmethod
    def create(cls, results: list[FlightResult]) -> "SearchResponse":
        """Factory method pour créer response avec search_id auto-généré."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `results` | `list[FlightResult]` | Liste résultats vols | max_length=10 (Top 10) |
| `search_id` | `str` | ID unique recherche | UUID4 format |
| `total_results` | `int` | Nombre total résultats | = len(results) |

**Comportement** :
- `search_id` généré automatiquement via `uuid.uuid4()` dans factory method
- `total_results` calculé automatiquement depuis `len(results)`
- Limite Top 10 : Mock service ne retourne jamais plus de 10 résultats

**Factory Method** :
```python
@classmethod
def create(cls, results: list[FlightResult]) -> "SearchResponse":
    """Factory method pour créer response avec search_id auto-généré."""
    return cls(
        results=results,
        search_id=str(uuid.uuid4()),
        total_results=len(results)
    )
```

**Exemples** :

### Exemple 1: SearchResponse avec factory
```python
flights = [
    FlightResult(
        itinerary=["Paris", "Tokyo"],
        price=1200.00,
        currency="EUR",
        departure_date="2025-06-01",
        return_date="2025-06-15"
    ),
    FlightResult(
        itinerary=["Paris", "New York"],
        price=950.00,
        currency="EUR",
        departure_date="2025-06-01",
        return_date="2025-06-15"
    )
]

response = SearchResponse.create(results=flights)
assert response.total_results == 2
assert len(response.search_id) == 36
```

**Exemple JSON SearchResponse** :
```json
{
  "results": [
    {
      "itinerary": ["Paris", "Tokyo", "New York"],
      "price": 1250.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Paris", "New York", "Tokyo"],
      "price": 1350.00,
      "currency": "EUR",
      "departure_date": "2025-06-02",
      "return_date": "2025-06-14"
    }
  ],
  "search_id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "total_results": 2
}
```

---

## 5. SearchService (Mock Implementation)

**Rôle** : Service orchestrant la recherche de vols, retournant mock data hardcodé pour Phase MVP.

**Interface** :
```python
class SearchService:
    """Service de recherche de vols (mock implementation)."""

    async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
        """Retourne 3-5 résultats mock hardcodés utilisant destinations de la requête."""
```

**Signature Méthode** :
```python
async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
    """Retourne 3-5 résultats mock hardcodés utilisant destinations de la requête.

    Args:
        request: SearchRequest avec destinations et date_range

    Returns:
        Liste 3-5 FlightResult mock avec itinéraires combinant destinations request

    Note:
        Phase MVP : Mock data hardcodé en mémoire.
        Phase 5.4+ : Remplacement par vraie logique scraping.
    """
```

**Comportement Mock** :
- Génère 3-5 résultats mock hardcodés
- Prix range : 800.00 - 2500.00 EUR
- Itinéraires : Combinaisons des destinations fournies dans `request.destinations`
- Dates : Utilise `request.date_range.start` et `request.date_range.end`
- Pas d'appel externe : Pure génération données en mémoire

**Exemple Mock Data** :
```python
async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
    """Retourne mock data hardcodé."""
    mock_flights = [
        FlightResult(
            itinerary=[request.destinations[0], request.destinations[1]],
            price=1250.00,
            currency="EUR",
            departure_date=request.date_range.start,
            return_date=request.date_range.end
        ),
        FlightResult(
            itinerary=[request.destinations[1], request.destinations[0]],
            price=1350.00,
            currency="EUR",
            departure_date=request.date_range.start,
            return_date=request.date_range.end
        ),
        FlightResult(
            itinerary=request.destinations[:2],
            price=980.00,
            currency="EUR",
            departure_date=request.date_range.start,
            return_date=request.date_range.end
        )
    ]
    return mock_flights[:5]
```

---

## 6. Route POST /api/v1/search-flights

**Rôle** : Endpoint FastAPI exposant la recherche de vols, avec validation automatique Pydantic.

**Interface** :

| Champ | Valeur |
|-------|--------|
| **Path** | `/api/v1/search-flights` |
| **Méthode HTTP** | `POST` |
| **Request Body** | `SearchRequest` (JSON) |
| **Response Model** | `SearchResponse` (JSON) |
| **Status Codes** | `200` (success), `422` (validation error) |
| **Authentication** | Aucune (endpoint public MVP) |

**Signature FastAPI** :
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1", tags=["search"])

@router.post("/search-flights", response_model=SearchResponse, status_code=200)
async def search_flights(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """Recherche vols multi-destinations (mock data Phase MVP).

    Args:
        request: SearchRequest validé par Pydantic
        search_service: SearchService injecté via dependency injection

    Returns:
        SearchResponse avec 3-5 résultats mock + search_id + total_results

    Raises:
        HTTPException 422: Si validation Pydantic échoue
    """
```

**Dependency Injection** :
```python
def get_search_service() -> SearchService:
    """Factory pour SearchService (singleton en mémoire)."""
    return SearchService()
```

**Comportement** :
1. FastAPI valide automatiquement `request: SearchRequest` (Pydantic)
2. Si validation échoue → Status 422 avec détails erreurs Pydantic
3. Si validation réussit → Appel `search_service.search_flights(request)`
4. Retour `SearchResponse.create(results)` avec search_id auto-généré
5. FastAPI sérialise automatiquement response en JSON

**Exemples** :

### Exemple 1: Requête valide (curl)
```bash
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "destinations": ["Paris", "Tokyo", "New York"],
    "date_range": {
      "start": "2025-06-01",
      "end": "2025-06-15"
    }
  }'
```

**Response 200** :
```json
{
  "results": [
    {
      "itinerary": ["Paris", "Tokyo"],
      "price": 1250.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Tokyo", "New York"],
      "price": 1350.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    }
  ],
  "search_id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "total_results": 2
}
```

### Exemple 2: Requête invalide (validation error)
```bash
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "destinations": ["Paris"],
    "date_range": {
      "start": "2025-06-15",
      "end": "2025-06-01"
    }
  }'
```

**Response 422** :
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "destinations"],
      "msg": "destinations must contain at least 2 cities, got 1",
      "input": ["Paris"]
    },
    {
      "type": "value_error",
      "loc": ["body", "date_range"],
      "msg": "start date (2025-06-15) must be before end date (2025-06-01)",
      "input": {"start": "2025-06-15", "end": "2025-06-01"}
    }
  ]
}
```

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### DateRange Model (3 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_date_range_valid` | `start="2025-06-01", end="2025-06-15"` | `DateRange` instance créée | Dates chargées correctement |
| 2 | `test_date_range_invalid_format` | `start="2025/06/01"` | `ValidationError` levée | Message contient "ISO 8601 format" |
| 3 | `test_date_range_start_after_end` | `start="2025-06-15", end="2025-06-01"` | `ValidationError` levée | Message contient "start date must be before end date" |

**Exemple code test AAA** :
```python
from pydantic import ValidationError
import pytest
from app.models.request import DateRange


def test_date_range_valid():
    # Arrange: Setup valid date range
    start = "2025-06-01"
    end = "2025-06-15"

    # Act: Create DateRange instance
    date_range = DateRange(start=start, end=end)

    # Assert: Verify expected properties
    assert date_range.start == start
    assert date_range.end == end


def test_date_range_invalid_format():
    # Arrange: Setup invalid date format
    invalid_data = {
        "start": "2025/06/01",
        "end": "2025-06-15"
    }

    # Act & Assert: Verify ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        DateRange(**invalid_data)

    # Assert: Verify error message
    assert "ISO 8601 format" in str(exc_info.value)


def test_date_range_start_after_end():
    # Arrange: Setup invalid date range (start > end)
    invalid_data = {
        "start": "2025-06-15",
        "end": "2025-06-01"
    }

    # Act & Assert: Verify ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        DateRange(**invalid_data)

    # Assert: Verify error message
    assert "start date" in str(exc_info.value).lower()
    assert "before" in str(exc_info.value).lower()
```

**Total tests unitaires DateRange** : 3 tests

---

### SearchRequest Model (7 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_search_request_valid` | 2+ destinations, date_range valide | `SearchRequest` instance créée | Tous champs chargés correctement |
| 2 | `test_search_request_invalid_destinations_min_length` | 1 destination uniquement | `ValidationError` levée | Message contient "at least 2 cities" |
| 3 | `test_search_request_empty_destination_string` | `destinations=["Paris", ""]` | `ValidationError` levée | Message contient "empty strings" |
| 4 | `test_search_request_valid_max_stops` | `max_stops=1` | `SearchRequest.max_stops == 1` | Champ optionnel accepté |
| 5 | `test_search_request_default_max_stops` | `max_stops` omis | `SearchRequest.max_stops is None` | Valeur par défaut None |
| 6 | `test_search_request_nested_date_range_validation` | `date_range` avec start > end | `ValidationError` levée | Validation DateRange imbriquée fonctionne |
| 7 | `test_search_request_serialization` | Instance valide | `model_dump()` produit dict correct | Sérialisation JSON fonctionne |

**Exemple code test AAA** :
```python
from pydantic import ValidationError
import pytest
from app.models.request import SearchRequest, DateRange


def test_search_request_valid():
    # Arrange: Setup valid request data
    destinations = ["Paris", "Tokyo", "New York"]
    date_range = DateRange(start="2025-06-01", end="2025-06-15")
    max_stops = 1

    # Act: Create SearchRequest instance
    request = SearchRequest(
        destinations=destinations,
        date_range=date_range,
        max_stops=max_stops
    )

    # Assert: Verify expected properties
    assert request.destinations == destinations
    assert request.date_range.start == "2025-06-01"
    assert request.max_stops == 1


def test_search_request_invalid_destinations_min_length():
    # Arrange: Setup request with only 1 destination
    invalid_data = {
        "destinations": ["Paris"],
        "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
    }

    # Act & Assert: Verify ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(**invalid_data)

    # Assert: Verify error message
    assert "at least 2 cities" in str(exc_info.value).lower()


def test_search_request_default_max_stops():
    # Arrange: Setup request without max_stops
    request_data = {
        "destinations": ["Paris", "Tokyo"],
        "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
    }

    # Act: Create SearchRequest instance
    request = SearchRequest(**request_data)

    # Assert: Verify default value is None
    assert request.max_stops is None
```

**Total tests unitaires SearchRequest** : 7 tests

---

### FlightResult Model (3 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_flight_result_valid` | Tous champs valides | `FlightResult` instance créée | Champs chargés correctement |
| 2 | `test_flight_result_negative_price` | `price=-100.00` | `ValidationError` levée | Message contient "price must be >= 0" |
| 3 | `test_flight_result_invalid_currency` | `currency="GBP"` | `ValidationError` levée | Message contient "EUR" et "USD" |

**Exemple code test AAA** :
```python
from pydantic import ValidationError
import pytest
from app.models.response import FlightResult


def test_flight_result_valid():
    # Arrange: Setup valid flight data
    itinerary = ["Paris", "Tokyo", "New York"]
    price = 1250.00
    currency = "EUR"
    departure_date = "2025-06-01"
    return_date = "2025-06-15"

    # Act: Create FlightResult instance
    flight = FlightResult(
        itinerary=itinerary,
        price=price,
        currency=currency,
        departure_date=departure_date,
        return_date=return_date
    )

    # Assert: Verify expected properties
    assert flight.itinerary == itinerary
    assert flight.price == price
    assert flight.currency == currency


def test_flight_result_negative_price():
    # Arrange: Setup flight with negative price
    invalid_data = {
        "itinerary": ["Paris", "Tokyo"],
        "price": -100.00,
        "currency": "EUR",
        "departure_date": "2025-06-01",
        "return_date": "2025-06-15"
    }

    # Act & Assert: Verify ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        FlightResult(**invalid_data)

    # Assert: Verify error message
    assert "price must be >= 0" in str(exc_info.value).lower()
```

**Total tests unitaires FlightResult** : 3 tests

---

### SearchResponse Model (3 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_search_response_create_factory` | Liste 2 FlightResult | `SearchResponse` avec search_id auto-généré | search_id non vide, total_results == 2 |
| 2 | `test_search_response_total_results_matches_length` | Liste 5 FlightResult | `total_results == 5` | Cohérence total_results et len(results) |
| 3 | `test_search_response_search_id_uuid_format` | Factory method appelé | search_id format UUID4 valide | Regex UUID4 ou len == 36 |

**Exemple code test AAA** :
```python
from app.models.response import SearchResponse, FlightResult


def test_search_response_create_factory():
    # Arrange: Setup mock flight results
    flights = [
        FlightResult(
            itinerary=["Paris", "Tokyo"],
            price=1200.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        ),
        FlightResult(
            itinerary=["Tokyo", "New York"],
            price=1350.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        )
    ]

    # Act: Create SearchResponse via factory
    response = SearchResponse.create(results=flights)

    # Assert: Verify expected properties
    assert len(response.results) == 2
    assert response.total_results == 2
    assert response.search_id is not None
    assert len(response.search_id) == 36


def test_search_response_total_results_matches_length():
    # Arrange: Setup 5 mock flights
    flights = [
        FlightResult(
            itinerary=["Paris", "Tokyo"],
            price=1000.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        )
        for _ in range(5)
    ]

    # Act: Create SearchResponse
    response = SearchResponse.create(results=flights)

    # Assert: Verify total_results matches list length
    assert response.total_results == len(response.results)
    assert response.total_results == 5
```

**Total tests unitaires SearchResponse** : 3 tests

---

### SearchService (5 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_search_service_returns_mock_data` | SearchRequest valide | Liste 3-5 FlightResult | Résultats non vides |
| 2 | `test_search_service_results_count_max_10` | SearchRequest valide | len(results) <= 10 | Respect contrainte Top 10 |
| 3 | `test_search_service_itinerary_uses_request_destinations` | destinations=["Paris", "Tokyo"] | Itinéraires contiennent ces villes | Mock utilise input request |
| 4 | `test_search_service_price_positive` | SearchRequest valide | Tous prices >= 0 | Validation métier |
| 5 | `test_search_service_async_execution` | Appel async | Pas d'exception, retour non None | Fonction async fonctionne |

**Exemple code test AAA** :
```python
import pytest
from app.services.search_service import SearchService
from app.models.request import SearchRequest, DateRange


@pytest.mark.asyncio
async def test_search_service_returns_mock_data():
    # Arrange: Setup service and valid request
    service = SearchService()
    request = SearchRequest(
        destinations=["Paris", "Tokyo"],
        date_range=DateRange(start="2025-06-01", end="2025-06-15")
    )

    # Act: Call async search_flights
    results = await service.search_flights(request)

    # Assert: Verify mock data returned
    assert len(results) >= 3
    assert len(results) <= 5
    assert all(result.price >= 0 for result in results)


@pytest.mark.asyncio
async def test_search_service_itinerary_uses_request_destinations():
    # Arrange: Setup service with specific destinations
    service = SearchService()
    destinations = ["Paris", "Tokyo"]
    request = SearchRequest(
        destinations=destinations,
        date_range=DateRange(start="2025-06-01", end="2025-06-15")
    )

    # Act: Call search_flights
    results = await service.search_flights(request)

    # Assert: Verify mock itineraries use request destinations
    for result in results:
        for city in result.itinerary:
            assert city in destinations
```

**Total tests unitaires SearchService** : 5 tests

---

### Route POST /search-flights (8 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_route_search_flights_valid_request` | Request JSON valide | Status 200 + SearchResponse JSON | Response structure correcte |
| 2 | `test_route_search_flights_validation_error_destinations` | 1 destination uniquement | Status 422 + error detail | Pydantic validation fonctionne |
| 3 | `test_route_search_flights_validation_error_date_range` | start > end | Status 422 + error detail | Validation cross-champs fonctionne |
| 4 | `test_route_search_flights_response_contains_search_id` | Request valide | Response JSON contient "search_id" non vide | Métadonnées présentes |
| 5 | `test_route_search_flights_response_contains_results` | Request valide | Response JSON contient "results" liste | Données mock présentes |
| 6 | `test_route_search_flights_response_total_results_matches` | Request valide | total_results == len(results) | Cohérence métadonnées |
| 7 | `test_route_search_flights_dependency_injection` | Mock SearchService injecté | Service mock appelé correctement | Dependency injection fonctionne |
| 8 | `test_route_search_flights_openapi_schema` | GET /openapi.json | Schema contient /api/v1/search-flights | Documentation auto-générée |

**Exemple code test AAA** :
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_route_search_flights_valid_request():
    # Arrange: Setup valid request data
    request_data = {
        "destinations": ["Paris", "Tokyo", "New York"],
        "date_range": {
            "start": "2025-06-01",
            "end": "2025-06-15"
        }
    }

    # Act: POST to search-flights endpoint
    response = client.post("/api/v1/search-flights", json=request_data)

    # Assert: Verify successful response
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_id" in data
    assert "total_results" in data
    assert len(data["results"]) >= 3


def test_route_search_flights_validation_error_destinations():
    # Arrange: Setup invalid request (only 1 destination)
    invalid_request = {
        "destinations": ["Paris"],
        "date_range": {
            "start": "2025-06-01",
            "end": "2025-06-15"
        }
    }

    # Act: POST invalid request
    response = client.post("/api/v1/search-flights", json=invalid_request)

    # Assert: Verify validation error
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
```

**Total tests unitaires Route** : 8 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**End-to-end** (4 tests) :

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_search_flights_end_to_end_valid` | App running | POST /api/v1/search-flights avec request valide | 200 + SearchResponse JSON complet avec 3-5 résultats mock |
| 2 | `test_integration_search_flights_validation_error_destinations` | App running | POST avec 1 destination | 422 + error detail mentionnant "at least 2 cities" |
| 3 | `test_integration_search_flights_validation_error_dates` | App running | POST avec start > end | 422 + error detail mentionnant "start date must be before" |
| 4 | `test_integration_search_flights_multiple_requests_unique_search_ids` | App running | POST 3 requêtes identiques | 3 responses avec search_id différents |

**Exemple code test Given/When/Then** :
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_integration_search_flights_end_to_end_valid():
    # Given: Application is running and valid request prepared
    request_data = {
        "destinations": ["Paris", "Tokyo", "New York"],
        "date_range": {
            "start": "2025-06-01",
            "end": "2025-06-15"
        },
        "max_stops": 1
    }

    # When: Client sends POST request to search endpoint
    response = client.post("/api/v1/search-flights", json=request_data)

    # Then: Response is successful with complete search results
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "search_id" in data
    assert "total_results" in data

    assert len(data["results"]) >= 3
    assert len(data["results"]) <= 10
    assert data["total_results"] == len(data["results"])

    for result in data["results"]:
        assert "itinerary" in result
        assert "price" in result
        assert "currency" in result
        assert result["price"] >= 0


def test_integration_search_flights_validation_error_destinations():
    # Given: Application is running
    invalid_request = {
        "destinations": ["Paris"],
        "date_range": {
            "start": "2025-06-01",
            "end": "2025-06-15"
        }
    }

    # When: Client sends invalid request (only 1 destination)
    response = client.post("/api/v1/search-flights", json=invalid_request)

    # Then: Validation error is returned with clear message
    assert response.status_code == 422

    error_detail = response.json()
    assert "detail" in error_detail

    error_messages = str(error_detail)
    assert "at least 2 cities" in error_messages.lower()


def test_integration_search_flights_multiple_requests_unique_search_ids():
    # Given: Application is running with same request data
    request_data = {
        "destinations": ["Paris", "Tokyo"],
        "date_range": {
            "start": "2025-06-01",
            "end": "2025-06-15"
        }
    }

    # When: Client sends 3 identical requests
    responses = [
        client.post("/api/v1/search-flights", json=request_data)
        for _ in range(3)
    ]

    # Then: Each response has unique search_id
    search_ids = [r.json()["search_id"] for r in responses]
    assert len(search_ids) == 3
    assert len(set(search_ids)) == 3
```

**Total tests intégration** : 4 tests

---

## Exemples JSON

**Exemple 1 : Request valide avec 3 destinations** :
```json
{
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  },
  "max_stops": 1
}
```

**Exemple 2 : Response succès (200)** :
```json
{
  "results": [
    {
      "itinerary": ["Paris", "Tokyo", "New York"],
      "price": 1250.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Paris", "New York", "Tokyo"],
      "price": 1350.00,
      "currency": "EUR",
      "departure_date": "2025-06-02",
      "return_date": "2025-06-14"
    },
    {
      "itinerary": ["Paris", "Tokyo"],
      "price": 980.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    }
  ],
  "search_id": "a1b2c3d4-e5f6-4789-a012-3456789abcde",
  "total_results": 3
}
```

**Exemple 3 : Error response (422) - Destinations insuffisantes** :
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "destinations"],
      "msg": "destinations must contain at least 2 cities, got 1",
      "input": ["Paris"]
    }
  ]
}
```

**Exemple 4 : Error response (422) - Date range invalide** :
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "date_range"],
      "msg": "start date (2025-06-15) must be before end date (2025-06-01)",
      "input": {
        "start": "2025-06-15",
        "end": "2025-06-01"
      }
    }
  ]
}
```

**Exemple 5 : Error response (422) - Multiple validation errors** :
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "destinations"],
      "msg": "destinations must contain at least 2 cities, got 1",
      "input": ["Paris"]
    },
    {
      "type": "value_error",
      "loc": ["body", "date_range"],
      "msg": "start date (2025-06-15) must be before end date (2025-06-01)",
      "input": {
        "start": "2025-06-15",
        "end": "2025-06-01"
      }
    }
  ]
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Endpoint retourne 200 pour requête valide** : POST /api/v1/search-flights avec request valide retourne status 200 + JSON SearchResponse
2. **Endpoint retourne 422 pour requête invalide** : Destinations < 2 ou date_range incohérent retourne status 422 + error detail Pydantic
3. **Mock data cohérent** : Résultats mock contiennent itinéraires utilisant destinations de la requête
4. **Mock data range 3-5 résultats** : Chaque recherche retourne entre 3 et 5 FlightResult mock
5. **Prix positifs** : Tous résultats mock ont price >= 0
6. **Search_id unique** : Chaque requête génère nouveau search_id UUID4 distinct
7. **Total_results cohérent** : Champ total_results == len(results) dans response
8. **Validation destinations minimum** : Requête avec < 2 destinations rejetée avec message explicite
9. **Validation date_range cross-champs** : start >= end rejeté avec message explicite
10. **Currency Literal type safety** : Currency accepte uniquement "EUR" ou "USD"

## Critères techniques

11. **Type safety PEP 695** : Tous modèles utilisent type hints modernes (list[str], str | None, Literal)
12. **Pydantic v2 validators** : field_validator et model_validator utilisés pour validations custom
13. **Async service method** : SearchService.search_flights est async def (préparation futures appels externes)
14. **Dependency injection FastAPI** : Route utilise Depends(get_search_service)
15. **Factory method SearchResponse** : create() classmethod génère search_id automatiquement
16. **Pas d'appel externe** : SearchService mock génère données en mémoire uniquement
17. **OpenAPI schema auto-généré** : GET /docs affiche documentation endpoint avec exemples

## Critères qualité

18. **Coverage ≥ 80%** : pytest --cov=app atteint minimum 80% sur models, services, routes
19. **25+ tests passent** : 21 unitaires models + 5 service + 8 route + 4 intégration tous verts
20. **Mypy strict mode** : mypy app/ retourne 0 erreur de type
21. **Ruff lint/format** : ruff check . && ruff format . passent sans erreur
22. **Docstrings 1 ligne** : Tous modèles, services, routes ont docstring 1 ligne explicite

## Critères production (logging)

23. **Logs structurés pour recherches** : SearchService log avec extra context (search_id, destinations, result_count)
24. **Log niveau INFO pour requêtes** : Chaque recherche loggée avec format JSON structuré
25. **Pas de secrets dans logs** : Aucun password/API key dans logs (validation manuelle logs)

---

**💡 Note importante** : Cette story (8 story points) prépare la foundation pour intégration scraping réel (Story 4+). Le mock data permet de valider le contrat API et l'architecture avant la complexité du crawling Google Flights.

**Principe SMART** : Chaque critère est **S**pécifique (cible claire), **M**esurable (tests automatisés), **A**tteignable (scope MVP), **R**elevant (valeur business), **T**emporel (Phase 5.3).
