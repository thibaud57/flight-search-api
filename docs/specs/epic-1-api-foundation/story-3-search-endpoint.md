---
title: "Story 3: Search endpoint (mock data)"
epic: "Epic 1: API Foundation"
story_points: 8
dependencies: ["story-1-health-check.md", "story-2-config-logging.md"]
date: "2025-19-11"
keywords: ["api", "search", "endpoint", "mock", "pydantic", "fastapi", "validation", "multi-city", "flight-search", "tdd", "testing"]
scope: ["specs"]
technologies: ["FastAPI", "Pydantic", "pytest", "TestClient"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Développeurs Frontend** : Endpoint API mock pour développer interface utilisateur en parallèle backend (évite blocage attente scraping réel)
- **Product Owner** : Validation UX et format données dès Phase 1 sans dépendance infrastructure scraping complexe
- **QA/Testeurs** : Données mock prévisibles pour tester scénarios edge cases (1 destination, 5 destinations, plages dates longues)
- **Équipe Backend** : Contrat API fixé (modèles request/response) avant implémentation scraping réel Phase 5

## Contraintes métier

- **Données mock réalistes** : 10 résultats hardcodés avec variations prix (800€ - 2500€), compagnies multiples (Air France, Lufthansa, Emirates, etc.)
- **Performance acceptable** : Response time < 200ms même avec mock data (préparation scalabilité future)
- **Validation stricte** : Request doit être validée selon contraintes métier (1-5 destinations, plages dates cohérentes)
- **Sans dépendances externes** : Aucun appel DB/API/scraping dans cette story (pure mock en mémoire)

## Valeur business

- ✅ **Déblocage développement frontend** : Frontend peut commencer intégration API dès Phase 1 (gain temps ~2 semaines sur planning global)
- ✅ **Validation contrat API early** : Product Owner valide format données avant investissement scraping complexe (dérisquage architectural majeur)
- ✅ **Foundation TDD rigoureuse** : 46 tests (42 unitaires + 4 intégration) définissent comportements attendus pour Phase 5 (tests réutilisables, juste swap mock→scraping)
- ✅ **Feedback rapide stakeholders** : Démo fonctionnelle avec données réalistes dès fin Phase 1 (confiance investisseurs, validation product-market fit)
- ✅ **Documentation vivante** : Modèles Pydantic servent de référence auto-documentée (OpenAPI schema généré automatiquement)

## Métriques succès

- **Couverture tests** : ≥90% sur modèles et endpoint (46 tests couvrent validation, edge cases, intégration)
- **Response time** : < 200ms au p95 pour mock data (baseline performance avant scraping)
- **Adoption frontend** : 100% endpoints frontend utilisent ce contrat API mock (pas de divergence schéma)
- **Taux validation errors détectés** : 100% requêtes invalides rejetées avec messages clairs (destinations vides, dates incohérentes)

---

# 📋 Spécifications Techniques

## 1. SearchRequest Model

**Rôle** : Modèle Pydantic représentant requête utilisateur pour recherche vols multi-destinations.

**Interface** :

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Annotated

class DateRange(BaseModel):
    """Plage de dates pour recherche vols."""

    start: str
    end: str

class SearchRequest(BaseModel):
    """Requête de recherche vols multi-destinations."""

    destinations: Annotated[list[str], "Liste destinations (1-5 villes)"]
    date_range: DateRange
```

**Champs SearchRequest** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `destinations` | `list[str]` | Liste villes destinations (ex: ["Paris", "Tokyo", "New York"]) | min_length=1, max_length=5, chaque ville min_length=2 | Requis |
| `date_range` | `DateRange` | Plage dates voyage (start/end) | Modèle nested DateRange, dates ISO 8601 (YYYY-MM-DD) | Requis |

**Champs DateRange** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `start` | `str` | Date début voyage au format ISO 8601 | Format YYYY-MM-DD, doit être ≥ date du jour | Requis |
| `end` | `str` | Date fin voyage au format ISO 8601 | Format YYYY-MM-DD, doit être > start | Requis |

**Comportement** :

- **Validation automatique** : Pydantic valide types et contraintes à instanciation
- **Edge cases** : Accepte 1 destination seule (aller simple) ou jusqu'à 5 destinations (multi-city complexe)
- **Erreurs levées** : `ValidationError` si destinations vide, dates invalides, end < start
- **Normalisation** : Destinations trim whitespace (field_validator avec .strip())

**Validations Pydantic** :

- `field_validator('destinations', mode='after')` : Vérifier 1 ≤ len(destinations) ≤ 5, chaque ville min 2 caractères après strip
- `field_validator('start', 'end', mode='before')` : Valider format ISO 8601 (YYYY-MM-DD), convertir en date objects pour comparaison
- `model_validator(mode='after')` sur `DateRange` : Vérifier end > start (dates cohérentes)
- `model_validator(mode='after')` sur `DateRange` : Vérifier start ≥ date du jour (pas de voyages passés)

**Type hints** :

- ✅ Type hints PEP 695 : `list[str]` (pas `List[str]`), `Annotated` pour documentation inline
- ✅ Nested models : DateRange typé explicitement
- ✅ Validators classmethod : `@field_validator @classmethod def validate_field(cls, v: str) -> str:`

---

## 2. SearchResponse Model

**Rôle** : Modèle Pydantic représentant réponse API avec top 10 résultats vols et statistiques recherche.

**Interface** :

```python
from pydantic import BaseModel
from typing import Annotated

class FlightResult(BaseModel):
    """Résultat individuel vol (1 sur 10 retournés)."""

    price: Annotated[float, "Prix total en EUR"]
    airline: str
    departure_date: str
    route: list[str]

class SearchStats(BaseModel):
    """Statistiques métadonnées recherche."""

    total_results: int
    search_time_ms: int
    destinations_searched: list[str]

class SearchResponse(BaseModel):
    """Réponse API contenant top 10 résultats + stats."""

    results: Annotated[list[FlightResult], "Top 10 résultats triés par prix croissant"]
    search_stats: SearchStats
```

**Champs FlightResult** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `price` | `float` | Prix total vol en EUR (ex: 1250.50) | ≥ 0.0, précision 2 décimales | Requis |
| `airline` | `str` | Nom compagnie aérienne (ex: "Air France") | min_length=2, max_length=100 | Requis |
| `departure_date` | `str` | Date départ au format ISO 8601 (YYYY-MM-DD) | Format ISO 8601 valide | Requis |
| `route` | `list[str]` | Itinéraire destinations (ex: ["Paris", "Tokyo", "New York"]) | min_length=1, même ordre que SearchRequest.destinations | Requis |

**Champs SearchStats** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `total_results` | `int` | Nombre total résultats trouvés (mock: toujours 10) | ≥ 0, ≤ 10 (Phase 1 mock limité) | Requis |
| `search_time_ms` | `int` | Temps recherche en millisecondes (mock: ~50ms) | ≥ 0, < 10000 (< 10s timeout) | Requis |
| `destinations_searched` | `list[str]` | Destinations recherchées (copie SearchRequest.destinations) | Même longueur que request | Requis |

**Champs SearchResponse** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `results` | `list[FlightResult]` | Liste top 10 résultats triés prix croissant | max_length=10, sorted by price ASC | Requis |
| `search_stats` | `SearchStats` | Métadonnées recherche (total, temps, destinations) | Modèle nested SearchStats | Requis |

**Comportement** :

- **Tri automatique** : results triés par price croissant (mock data pré-triée)
- **Limitation top 10** : results.length ≤ 10 toujours (Phase 1 mock, Phase 5 scraping top 10 réels)
- **Métadonnées cohérentes** : search_stats.destinations_searched doit matcher SearchRequest.destinations
- **Validation automatique** : Pydantic valide nested models et contraintes

**Validations Pydantic** :

- `field_validator('price', mode='after')` sur `FlightResult` : Vérifier ≥ 0.0
- `field_validator('results', mode='after')` sur `SearchResponse` : Vérifier len(results) ≤ 10
- `model_validator(mode='after')` sur `SearchResponse` : Vérifier results triés par price croissant

**Type hints** :

- ✅ Nested models explicites : `search_stats: SearchStats`
- ✅ Annotated pour documentation : `list[FlightResult]` avec description
- ✅ Type hints PEP 695 complets

---

## 3. SearchService (Mock)

**Rôle** : Service métier générant mock data de 10 résultats vols pour Phase 1 (sera remplacé par scraping réel Phase 5).

**Interface** :

```python
class SearchService:
    """Service recherche vols (mock Phase 1)."""

    def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Retourne 10 résultats mock triés par prix."""
```

**Comportement** :

- **Mock data hardcodé** : Retourne toujours même liste de 10 FlightResult avec variations réalistes
- **Tri prix croissant** : Mock data pré-triée de 800€ à 2500€ environ
- **Compagnies variées** : Air France, Lufthansa, Emirates, Delta, United, British Airways, Qatar Airways, Singapore Airlines, Cathay Pacific, ANA
- **Routes cohérentes** : Chaque FlightResult.route reprend SearchRequest.destinations dans même ordre
- **Statistiques mock** : search_stats.total_results = 10, search_time_ms = random 30-80ms, destinations_searched = request.destinations

**Mock Data Exemple** (10 résultats hardcodés) :

```python
# Résultat 1 (prix le plus bas)
FlightResult(
    price=825.50,
    airline="Air France",
    departure_date="2025-06-01",
    route=["Paris", "Tokyo"]  # Adapté selon request.destinations
)

# Résultat 2
FlightResult(
    price=950.00,
    airline="Lufthansa",
    departure_date="2025-06-02",
    route=["Paris", "Tokyo"]
)

# ... (8 résultats intermédiaires)

# Résultat 10 (prix le plus élevé)
FlightResult(
    price=2450.00,
    airline="Qatar Airways",
    departure_date="2025-06-15",
    route=["Paris", "Tokyo"]
)
```

**Contraintes techniques** :

- **Fonction synchrone** : `def search_flights()` (pas async, pas d'I/O externe)
- **Stateless** : Aucun état partagé, chaque appel indépendant
- **Déterministe** : Mock data identique pour inputs identiques (sauf search_time_ms random)
- **Pas de dépendances** : Aucun import crawl4ai, decodo, DB

---

## 4. Route POST /api/v1/search-flights

**Rôle** : Endpoint FastAPI acceptant SearchRequest et retournant SearchResponse via SearchService mock.

**Interface** :

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

router = APIRouter(prefix="/api/v1", tags=["search"])

@router.post("/search-flights", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_flights_endpoint(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)]
) -> SearchResponse:
    """Endpoint recherche vols multi-destinations (mock Phase 1)."""
```

**Paramètres** :

| Paramètre | Type | Description | Contraintes |
|-----------|------|-------------|-------------|
| `request` | `SearchRequest` | Body JSON requête validée par Pydantic | Validation automatique FastAPI, 422 si invalide |
| `search_service` | `SearchService` | Service injecté via Depends() | Singleton ou factory injection |

**Response** :

| Status Code | Body | Description |
|-------------|------|-------------|
| `200 OK` | `SearchResponse` JSON | Recherche succès, top 10 résultats retournés |
| `422 Unprocessable Entity` | Error details JSON | Validation failed (destinations invalides, dates incohérentes) |
| `500 Internal Server Error` | Error details JSON | Erreur serveur inattendue (ne devrait pas arriver en Phase 1 mock) |

**Comportement** :

- **Validation automatique** : FastAPI valide SearchRequest body, retourne 422 si invalide
- **Injection SearchService** : SearchService fourni via Depends() (testable, mockable)
- **Response 200 systématique** : Mock data toujours disponible, pas d'erreur attendue Phase 1
- **Logging** : Log info avec extra fields (destinations, search_time) pour observabilité

**Exemple appel** :

```bash
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "destinations": ["Paris", "Tokyo"],
    "date_range": {"start": "2025-06-01", "end": "2025-06-15"}
  }'
```

**Contraintes techniques** :

- **Endpoint synchrone** : `def` (pas `async def`) car SearchService sync en Phase 1
- **Prefix route** : `/api/v1/` pour versioning API
- **Tag OpenAPI** : `tags=["search"]` pour groupement documentation
- **response_model** : Validation automatique output via SearchResponse schema

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### SearchRequest Model (21 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_search_request_valid_single_destination` | Request valide avec 1 destination | `{"destinations": ["Paris"], "date_range": {"start": "2025-06-01", "end": "2025-06-15"}}` | SearchRequest instance créée sans erreur | Vérifie edge case minimum destinations (1) |
| 2 | `test_search_request_valid_two_destinations` | Request valide avec 2 destinations | `{"destinations": ["Paris", "Tokyo"], "date_range": {...}}` | SearchRequest valide | Vérifie cas nominal multi-city |
| 3 | `test_search_request_valid_five_destinations` | Request valide avec 5 destinations (max) | `{"destinations": ["Paris", "Tokyo", "New York", "London", "Dubai"], "date_range": {...}}` | SearchRequest valide | Vérifie edge case maximum destinations (5) |
| 4 | `test_search_request_empty_destinations_fails` | Destinations vide rejetée | `{"destinations": [], "date_range": {...}}` | Lève `ValidationError` | Vérifie validation min_length=1 |
| 5 | `test_search_request_too_many_destinations_fails` | Plus de 5 destinations rejetées | `{"destinations": ["Paris", "Tokyo", "NYC", "London", "Dubai", "Berlin"], ...}` | Lève `ValidationError` | Vérifie validation max_length=5 |
| 6 | `test_search_request_destination_too_short_fails` | Destination 1 caractère rejetée | `{"destinations": ["P"], "date_range": {...}}` | Lève `ValidationError` | Vérifie validation min_length=2 par ville |
| 7 | `test_search_request_destinations_whitespace_trimmed` | Destinations avec espaces nettoyées | `{"destinations": ["  Paris  ", "Tokyo "], ...}` | destinations = ["Paris", "Tokyo"] (trimmed) | Vérifie field_validator .strip() |
| 8 | `test_date_range_valid_dates` | DateRange dates valides | `{"start": "2025-06-01", "end": "2025-06-15"}` | DateRange instance créée | Vérifie parsing dates ISO 8601 |
| 9 | `test_date_range_end_before_start_fails` | End avant start rejetée | `{"start": "2025-06-15", "end": "2025-06-01"}` | Lève `ValidationError` | Vérifie model_validator end > start |
| 10 | `test_date_range_same_day_fails` | Start = end rejetée | `{"start": "2025-06-01", "end": "2025-06-01"}` | Lève `ValidationError` | Vérifie end strictement > start |
| 11 | `test_date_range_start_past_fails` | Start dans le passé rejetée | `{"start": "2020-01-01", "end": "2020-01-15"}` | Lève `ValidationError` | Vérifie model_validator start ≥ today |
| 12 | `test_date_range_invalid_format_fails` | Format date invalide rejeté | `{"start": "01-06-2025", "end": "15-06-2025"}` | Lève `ValidationError` | Vérifie field_validator ISO 8601 strict |
| 13 | `test_date_range_non_existent_date_fails` | Date inexistante rejetée | `{"start": "2025-02-30", "end": "2025-03-01"}` | Lève `ValidationError` | Vérifie validation date réelle |
| 14 | `test_search_request_nested_date_range_valid` | SearchRequest avec DateRange nested | Request complète valide | SearchRequest.date_range instance DateRange | Vérifie nested model parsing |
| 15 | `test_search_request_missing_destinations_fails` | Champ destinations manquant | `{"date_range": {...}}` | Lève `ValidationError` | Vérifie champ requis |
| 16 | `test_search_request_missing_date_range_fails` | Champ date_range manquant | `{"destinations": ["Paris"]}` | Lève `ValidationError` | Vérifie champ requis |
| 17 | `test_search_request_destinations_not_list_fails` | Destinations string au lieu de list | `{"destinations": "Paris", ...}` | Lève `ValidationError` | Vérifie type list strict |
| 18 | `test_search_request_model_dump_json_valid` | Serialization JSON valide | SearchRequest instance | JSON parsable et conforme schéma | Vérifie model_dump_json() fonctionne |
| 19 | `test_search_request_model_validate_from_dict` | Instanciation depuis dict | Dict valide | SearchRequest instance créée | Vérifie model_validate() factory |
| 20 | `test_date_range_future_dates_valid` | Dates très futures acceptées | `{"start": "2030-01-01", "end": "2030-12-31"}` | DateRange valide | Vérifie pas de limite max date future |
| 21 | `test_search_request_type_hints_pep695_compliant` | Type hints code conforme PEP 695 | Code source | list[str] (pas List[str]), Annotated utilisé | Vérifie standards projet CLAUDE.md |

### SearchResponse Model (5 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 22 | `test_flight_result_valid_fields` | FlightResult valide | `{"price": 1250.50, "airline": "Air France", "departure_date": "2025-06-01", "route": ["Paris"]}` | FlightResult instance créée | Vérifie champs obligatoires présents |
| 23 | `test_flight_result_negative_price_fails` | Prix négatif rejeté | `{"price": -100.0, ...}` | Lève `ValidationError` | Vérifie field_validator price ≥ 0 |
| 24 | `test_search_stats_valid_fields` | SearchStats valide | `{"total_results": 10, "search_time_ms": 50, "destinations_searched": ["Paris"]}` | SearchStats instance créée | Vérifie nested model validé |
| 25 | `test_search_response_results_sorted_by_price` | Results triés prix croissant | Liste FlightResult désordonnée | ValidationError si pas triée (ou auto-sort) | Vérifie model_validator tri prix |
| 26 | `test_search_response_max_10_results` | Max 10 results respecté | 11 FlightResult dans results | Lève `ValidationError` | Vérifie field_validator len ≤ 10 |

### SearchService Mock (5 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 27 | `test_search_service_returns_10_results` | Service retourne 10 résultats | SearchRequest valide | len(response.results) == 10 | Vérifie mock data complet |
| 28 | `test_search_service_results_sorted_by_price` | Résultats triés prix croissant | SearchRequest valide | response.results[0].price < response.results[9].price | Vérifie tri mock data |
| 29 | `test_search_service_route_matches_request_destinations` | Routes mock matchent destinations request | SearchRequest(destinations=["Paris", "Tokyo"]) | Tous FlightResult.route == ["Paris", "Tokyo"] | Vérifie cohérence mock data |
| 30 | `test_search_service_search_stats_accurate` | search_stats cohérentes | SearchRequest valide | search_stats.total_results == 10, destinations_searched == request.destinations | Vérifie métadonnées correctes |
| 31 | `test_search_service_deterministic_output` | Mock data identique pour inputs identiques | Même SearchRequest appelée 2x | response1.results == response2.results (sauf search_time_ms) | Vérifie déterminisme mock |

### Route POST /search-flights (8 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 32 | `test_endpoint_accepts_valid_request` | Endpoint accepte request valide | POST body SearchRequest valide | Status 200 + SearchResponse JSON | Vérifie comportement nominal |
| 33 | `test_endpoint_validates_request_body` | Body invalide rejeté | POST body destinations vide | Status 422 + validation error details | Vérifie validation automatique FastAPI |
| 34 | `test_endpoint_returns_10_results` | Endpoint retourne 10 résultats | POST request valide | response.results.length == 10 | Vérifie intégration SearchService |
| 35 | `test_endpoint_response_matches_schema` | Response conforme SearchResponse schema | POST request valide | JSON validé par SearchResponse model | Vérifie response_model FastAPI |
| 36 | `test_endpoint_injects_search_service_dependency` | SearchService injecté via Depends() | Mock SearchService fourni | Mock service utilisé (vérifiable via spy) | Vérifie dependency injection |
| 37 | `test_endpoint_logs_search_info` | Endpoint log search metadata | POST request valide | Log INFO avec extra fields destinations, search_time | Vérifie logging observabilité |
| 38 | `test_endpoint_handles_edge_case_single_destination` | Request 1 destination traitée | POST destinations=["Paris"] | Status 200 + 10 results avec route=["Paris"] | Vérifie edge case min destinations |
| 39 | `test_endpoint_handles_edge_case_max_destinations` | Request 5 destinations traitée | POST destinations avec 5 villes | Status 200 + 10 results avec route 5 villes | Vérifie edge case max destinations |

**Total tests unitaires** : 21 (SearchRequest) + 5 (SearchResponse) + 5 (SearchService) + 8 (Route) = **39 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**Format tableau descriptif** (5 colonnes) :

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_end_to_end_search_request_valid` | Application FastAPI running avec TestClient, SearchService mock injecté | POST `/api/v1/search-flights` avec body JSON valide (2 destinations, dates futures) | Status 200 + JSON response conforme SearchResponse schema avec 10 results triés prix croissant |
| 2 | `test_end_to_end_validation_error_empty_destinations` | TestClient configuré | POST `/api/v1/search-flights` avec destinations=[] | Status 422 + error details JSON indiquant validation destinations failed |
| 3 | `test_end_to_end_validation_error_invalid_dates` | TestClient configuré | POST `/api/v1/search-flights` avec date_range.end < date_range.start | Status 422 + error details JSON indiquant validation DateRange failed |
| 4 | `test_end_to_end_openapi_schema_includes_endpoint` | Application running, OpenAPI schema généré | GET `/openapi.json` | Schema contient endpoint POST `/api/v1/search-flights` avec SearchRequest/SearchResponse models documentés |

**Total tests intégration** : 4 tests

**Total tests Story 3** : 39 tests unitaires + 4 tests intégration = **43 tests**

---

## Exemples JSON

**Exemple 1 : Request valide (2 destinations)**

```json
{
  "destinations": ["Paris", "Tokyo"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

**Exemple 2 : Request valide (1 destination)**

```json
{
  "destinations": ["New York"],
  "date_range": {
    "start": "2025-07-10",
    "end": "2025-07-20"
  }
}
```

**Exemple 3 : Request valide (5 destinations max)**

```json
{
  "destinations": ["Paris", "Tokyo", "New York", "London", "Dubai"],
  "date_range": {
    "start": "2025-08-01",
    "end": "2025-08-30"
  }
}
```

**Exemple 4 : Response succès (10 résultats mock)**

```json
{
  "results": [
    {
      "price": 825.50,
      "airline": "Air France",
      "departure_date": "2025-06-01",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 950.00,
      "airline": "Lufthansa",
      "departure_date": "2025-06-02",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1120.75,
      "airline": "Emirates",
      "departure_date": "2025-06-03",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1280.00,
      "airline": "Delta",
      "departure_date": "2025-06-05",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1450.25,
      "airline": "United",
      "departure_date": "2025-06-07",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1620.50,
      "airline": "British Airways",
      "departure_date": "2025-06-08",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1785.00,
      "airline": "Qatar Airways",
      "departure_date": "2025-06-10",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 1950.75,
      "airline": "Singapore Airlines",
      "departure_date": "2025-06-12",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 2150.00,
      "airline": "Cathay Pacific",
      "departure_date": "2025-06-13",
      "route": ["Paris", "Tokyo"]
    },
    {
      "price": 2450.00,
      "airline": "ANA",
      "departure_date": "2025-06-15",
      "route": ["Paris", "Tokyo"]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 52,
    "destinations_searched": ["Paris", "Tokyo"]
  }
}
```

**Exemple 5 : Error 422 (destinations vide)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "destinations"],
      "msg": "List should have at least 1 item after validation, not 0",
      "input": [],
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

**Exemple 6 : Error 422 (dates incohérentes)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "date_range"],
      "msg": "End date must be after start date",
      "input": {
        "start": "2025-06-15",
        "end": "2025-06-01"
      }
    }
  ]
}
```

**Exemple 7 : Error 422 (trop de destinations)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "destinations"],
      "msg": "List should have at most 5 items after validation, not 6",
      "input": ["Paris", "Tokyo", "New York", "London", "Dubai", "Berlin"],
      "ctx": {
        "max_length": 5
      }
    }
  ]
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Endpoint accessible** : POST `/api/v1/search-flights` accessible et retourne JSON valide pour requêtes conformes
2. **Validation destinations stricte** : Endpoint accepte 1-5 destinations, rejette 0 ou >5 avec status 422 et message clair
3. **Validation dates cohérentes** : Endpoint rejette date_range.end ≤ date_range.start avec ValidationError explicite
4. **Validation dates futures** : Endpoint rejette date_range.start dans le passé (< date du jour) avec ValidationError
5. **Mock data retourné** : Endpoint retourne toujours exactement 10 FlightResult avec prix variés (800€-2500€)
6. **Tri prix garanti** : results triés par price croissant (results[0].price < results[9].price toujours vérifié)
7. **Routes cohérentes** : Chaque FlightResult.route correspond exactement à SearchRequest.destinations (même ordre)
8. **Métadonnées exactes** : search_stats.total_results = 10, destinations_searched = request.destinations, search_time_ms > 0

## Critères techniques

9. **Modèles Pydantic v2** : SearchRequest et SearchResponse héritent BaseModel avec validation automatique
10. **field_validator configurés** : destinations (min/max length, trim whitespace), dates (ISO 8601 format), price (≥ 0)
11. **model_validator cross-champs** : DateRange vérifie end > start et start ≥ today
12. **Type hints PEP 695 complets** : list[str] (pas List[str]), Annotated, type hints sur validators
13. **Nested models** : DateRange, FlightResult, SearchStats correctement typés et validés
14. **Dependency Injection** : SearchService injecté via Depends() FastAPI (testable, mockable)
15. **Endpoint synchrone** : Route implémentée avec `def` (pas `async def`) car SearchService sync en Phase 1
16. **OpenAPI schema** : Endpoint documenté automatiquement dans /docs avec modèles request/response

## Critères qualité

17. **Coverage ≥90%** : Tests couvrent 100% modèles validation, 100% SearchService mock, 95%+ route (43 tests)
18. **Tous tests passent** : 43 tests (39 unitaires + 4 intégration) exécutés avec succès (0 échecs)
19. **Standards projet conformes** : Ruff lint clean, Mypy strict mode clean, Type hints PEP 695 respectés
20. **Docstrings PEP 257** : Modèles, service et route documentés avec docstrings 1 ligne minimum
21. **Tests AAA/Given-When-Then** : Tests unitaires format AAA, tests intégration format BDD

## Critères production

22. **Logging observabilité** : Endpoint log INFO avec extra fields (destinations, search_time_ms, total_results)
23. **Response time acceptable** : < 200ms au p95 pour mock data (baseline performance avant scraping Phase 5)
24. **Validation errors clairs** : Messages 422 explicites indiquant champ et contrainte violée (UX developer-friendly)
25. **Compatible frontend** : Response JSON sérialisable directement en frontend sans transformation (snake_case cohérent)

---

**Note importante** : Story complexe (8 story points) → 25 critères couvrent exhaustivement validation stricte (8 fonctionnels), architecture Pydantic/FastAPI solide (8 techniques), qualité tests rigoureuse (5 qualité), production-ready logging (4 production).

**Principe SMART** : Chaque critère est **S**pécifique (10 résultats triés prix), **M**esurable (43 tests passent, coverage ≥90%), **A**tteignable (Pydantic patterns connus), **R**elevant (contrat API foundation MVP), **T**emporel (Phase 1, avant scraping réel).
