---
title: "SPECS - Spécifications Techniques Détaillées"
description: "Spécifications techniques détaillées pour implémentation MVP (Models, Services, API Routes, Tests). Consulter avant développement Phase 5."
date: "2025-11-17"
keywords: ["specs", "specifications", "technical", "models", "services", "api", "tests", "mvp"]
scope: ["docs"]
technologies: []
---

# Spécifications Techniques Détaillées

_À compléter en Phase 4_

---

# 1. Models (Pydantic v2)

## 1.1 DateRange

**Description** : Représente une plage de dates pour la recherche de vols.

**Fichier** : `app/models/request.py`

**Schéma** :

```python
class DateRange(BaseModel):
    start: str
    end: str
```

**Champs** :

| Champ | Type | Requis | Description | Format | Contraintes |
|-------|------|--------|-------------|--------|-------------|
| `start` | `str` | Oui | Date de début de la plage | ISO 8601 `YYYY-MM-DD` | Doit être < `end` |
| `end` | `str` | Oui | Date de fin de la plage | ISO 8601 `YYYY-MM-DD` | Doit être > `start` |

**Formats acceptés** :
- ✅ `"2025-06-01"` (ISO 8601)
- ❌ `"01/06/2025"` (format français)
- ❌ `"2025-6-1"` (sans zéros leading)

**Validation cross-champs** :

```python
@model_validator(mode='after')
def validate_date_order(self) -> 'DateRange':
    """Valide que start < end."""
    if self.start >= self.end:
        raise ValueError('start date must be before end date')
    return self
```

**Comportement** :
- Validation exécutée **après** parsing des champs individuels
- Utilise `mode='after'` pour accéder aux valeurs validées
- Lève `ValueError` si `start >= end`

**Exemple erreur** :

```python
# Input invalide
DateRange(start="2025-06-15", end="2025-06-01")

# Erreur levée
ValidationError: 1 validation error for DateRange
  Value error, start date must be before end date
```

## 1.2 Flight

**Description** : Représente un vol individuel dans la recherche multi-destinations.

**Fichier** : `app/models/request.py`

**Schéma** :

```python
class Flight(BaseModel):
    origin: str
    destination: str
    departure_date: str | None = None
    return_date: str | None = None
```

**Champs** :

| Champ | Type | Requis | Défaut | Description | Format |
|-------|------|--------|--------|-------------|--------|
| `origin` | `str` | Oui | - | Ville de départ | Nom de ville (ex: "Paris") |
| `destination` | `str` | Oui | - | Ville de destination | Nom de ville (ex: "Tokyo") |
| `departure_date` | `str \| None` | Non | `None` | Date de départ | ISO 8601 `YYYY-MM-DD` ou `None` |
| `return_date` | `str \| None` | Non | `None` | Date de retour | ISO 8601 `YYYY-MM-DD` ou `None` |

**Type hints** :
- ✅ Utilise syntaxe PEP 695 : `str | None` (pas `Optional[str]`)
- ✅ Défaut explicite : `= None` pour champs optionnels (Pydantic v2)

**Utilisation** :
- Généré automatiquement par `CombinationGenerator` à partir de `SearchRequest.destinations`
- Champs `departure_date` et `return_date` calculés depuis `SearchRequest.date_range`

## 1.3 SearchRequest

**Description** : Requête principale pour rechercher des vols multi-destinations.

**Fichier** : `app/models/request.py`

**Schéma** :

```python
class SearchRequest(BaseModel):
    destinations: list[str]
    date_range: DateRange
    max_results: int = 10
```

**Champs** :

| Champ | Type | Requis | Défaut | Description | Contraintes |
|-------|------|--------|--------|-------------|-------------|
| `destinations` | `list[str]` | Oui | - | Liste des destinations | Min: 2, Max: 10, Unicité requise, Non-vides |
| `date_range` | `DateRange` | Oui | - | Plage de dates de recherche | Objet `DateRange` validé |
| `max_results` | `int` | Non | `10` | Nombre maximum de résultats | Min: 1, Max: 50 |

**Contraintes détaillées** :

### `destinations`
- **Minimum** : 2 destinations (recherche multi-city nécessite au moins 2 villes)
- **Maximum** : 10 destinations (limite performance + coût proxies)
- **Unicité** : Pas de doublons (ex: `["Paris", "Paris"]` invalide)
- **Non-vides** : Chaque destination doit être non-vide après strip (ex: `["  "]` invalide)

### `max_results`
- **Minimum** : 1 (au moins un résultat)
- **Maximum** : 50 (limite raisonnable pour éviter surcharge)
- **Défaut** : 10 (Top 10 résultats)

**Type hints** :
- ✅ `list[str]` (PEP 695, pas `List[str]`)
- ✅ Pas de `Optional` pour `destinations` et `date_range` (obligatoires)

**Validations** :

### Validation 1 : Longueur liste destinations

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

**Exemple erreur** :
```python
SearchRequest(destinations=["Paris"], date_range=DateRange(...))
# → ValidationError: Value error, at least 2 destinations required
```

### Validation 2 : Unicité destinations

```python
@field_validator('destinations', mode='after')
@classmethod
def validate_destinations_unique(cls, v: list[str]) -> list[str]:
    """Valide que toutes les destinations sont uniques."""
    if len(v) != len(set(v)):
        raise ValueError('destinations must be unique')
    return v
```

**Exemple erreur** :
```python
SearchRequest(destinations=["Paris", "Tokyo", "Paris"], date_range=DateRange(...))
# → ValidationError: Value error, destinations must be unique
```

### Validation 3 : Destinations non-vides

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

**Exemple erreur** :
```python
SearchRequest(destinations=["Paris", "  ", "Tokyo"], date_range=DateRange(...))
# → ValidationError: Value error, destinations cannot be empty or whitespace
```

### Validation 4 : Contraintes max_results

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

**Exemple erreur** :
```python
SearchRequest(destinations=["Paris", "Tokyo"], date_range=DateRange(...), max_results=100)
# → ValidationError: Value error, max_results cannot exceed 50
```

## 1.4 FlightResult

**Description** : Représente un résultat de vol scraped depuis Google Flights.

**Fichier** : `app/models/response.py`

**Schéma** :

```python
class FlightResult(BaseModel):
    price: float
    airline: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    stops: int
```

**Champs** :

| Champ | Type | Requis | Description | Format | Exemple |
|-------|------|--------|-------------|--------|---------|
| `price` | `float` | Oui | Prix total du vol | Nombre décimal positif | `1250.50` |
| `airline` | `str` | Oui | Nom de la compagnie aérienne | Texte | `"Air France"` |
| `departure_time` | `str` | Oui | Heure de départ | ISO 8601 `YYYY-MM-DDTHH:MM:SS` | `"2025-06-01T10:30:00"` |
| `arrival_time` | `str` | Oui | Heure d'arrivée | ISO 8601 `YYYY-MM-DDTHH:MM:SS` | `"2025-06-01T22:15:00"` |
| `duration_minutes` | `int` | Oui | Durée totale du vol en minutes | Entier positif | `705` (11h45) |
| `stops` | `int` | Oui | Nombre d'escales | Entier >= 0 | `0` (direct), `1` (1 escale) |

**Type hints** :
- ✅ Types précis : `float`, `str`, `int` (pas de `Any`)
- ✅ Format ISO 8601 pour dates/heures (parsing facile côté client)

**Parsing** :
- Extrait depuis HTML Google Flights via `FlightParserService`
- Utilise `JsonCssExtractionStrategy` (pas de LLM)
- Sélecteurs CSS spécifiques à Google Flights

## 1.5 SearchStats

**Description** : Statistiques d'exécution de la recherche pour monitoring et debugging.

**Fichier** : `app/models/response.py`

**Schéma** :

```python
class SearchStats(BaseModel):
    total_combinations: int
    successful_searches: int
    failed_searches: int
    captcha_detected: int
    total_duration_seconds: float
```

**Champs** :

| Champ | Type | Requis | Description | Exemple |
|-------|------|--------|-------------|---------|
| `total_combinations` | `int` | Oui | Nombre total de combinaisons multi-city générées | `12` |
| `successful_searches` | `int` | Oui | Nombre de recherches réussies (parsing OK) | `10` |
| `failed_searches` | `int` | Oui | Nombre de recherches échouées (timeout, erreur) | `2` |
| `captcha_detected` | `int` | Oui | Nombre de captchas détectés | `1` |
| `total_duration_seconds` | `float` | Oui | Durée totale de la recherche en secondes | `45.32` |

**Utilisation** :
- **Monitoring** : Calculer taux de succès, taux de captcha, performance
- **Debugging** : Identifier problèmes (taux échec élevé → proxies/rate limits)
- **Business** : Estimer coûts (bandwidth proxies, 2Captcha si Phase 7)

**Métriques calculées** :
- **Taux de succès** : `successful_searches / total_combinations * 100`
- **Taux de captcha** : `captcha_detected / total_combinations * 100`
- **Moyenne par recherche** : `total_duration_seconds / total_combinations`

**Exemple valeurs** :
```json
{
  "total_combinations": 12,
  "successful_searches": 10,
  "failed_searches": 1,
  "captcha_detected": 1,
  "total_duration_seconds": 45.32
}
```

## 1.6 SearchResponse

**Description** : Réponse complète de l'endpoint `/api/v1/search-flights`.

**Fichier** : `app/models/response.py`

**Schéma** :

```python
class SearchResponse(BaseModel):
    results: list[FlightResult]
    stats: SearchStats
    search_id: str
```

**Champs** :

| Champ | Type | Requis | Description | Contraintes |
|-------|------|--------|-------------|-------------|
| `results` | `list[FlightResult]` | Oui | Liste des meilleurs vols trouvés | Max 10 résultats (Top 10) |
| `stats` | `SearchStats` | Oui | Statistiques d'exécution | Objet `SearchStats` complet |
| `search_id` | `str` | Oui | Identifiant unique de la recherche | UUID v4 |

**Contraintes** :
- `results` limité à 10 éléments maximum (Top 10)
- `search_id` généré automatiquement (UUID v4)
- `stats` toujours présent (même si `results` vide)

**Type hints** :
- ✅ `list[FlightResult]` (PEP 695)
- ✅ Composition de models (nested Pydantic models)

**Relations entre models** :
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
│   ├── captcha_detected
│   └── total_duration_seconds
└── search_id: str (UUID v4)
```

**Génération search_id** :
```python
import uuid

search_id = str(uuid.uuid4())
# Exemple: "550e8400-e29b-41d4-a716-446655440000"
```

**Comportement** :
- Triés par prix croissant (moins cher en premier)
- Maximum 10 résultats même si plus de vols trouvés
- Liste vide possible si aucun vol trouvé (stats toujours présent)

## 1.7 Tests Unitaires Models

**Fichier** : `tests/unit/test_models.py`

**Objectif** : Valider tous les models Pydantic avec happy path et edge cases.

**Liste exhaustive des tests** :

### DateRange (4 tests)

1. **`test_date_range_valid`**
   - Input : `{"start": "2025-06-01", "end": "2025-06-15"}`
   - Attendu : Objet `DateRange` créé sans erreur
   - Vérifie : Happy path basique

2. **`test_date_range_start_equals_end`**
   - Input : `{"start": "2025-06-01", "end": "2025-06-01"}`
   - Attendu : `ValidationError` avec message "start date must be before end date"
   - Vérifie : Validation cross-champs (start < end)

3. **`test_date_range_start_after_end`**
   - Input : `{"start": "2025-06-15", "end": "2025-06-01"}`
   - Attendu : `ValidationError` avec message "start date must be before end date"
   - Vérifie : Validation ordre dates inversé

4. **`test_date_range_missing_fields`**
   - Input : `{"start": "2025-06-01"}`
   - Attendu : `ValidationError` (champ `end` manquant)
   - Vérifie : Champs obligatoires

### Flight (2 tests)

5. **`test_flight_valid_all_fields`**
   - Input : `{"origin": "Paris", "destination": "Tokyo", "departure_date": "2025-06-01", "return_date": "2025-06-15"}`
   - Attendu : Objet `Flight` créé sans erreur
   - Vérifie : Happy path complet

6. **`test_flight_optional_dates_none`**
   - Input : `{"origin": "Paris", "destination": "Tokyo"}`
   - Attendu : Objet `Flight` créé avec `departure_date=None`, `return_date=None`
   - Vérifie : Champs optionnels avec défaut `None`

### SearchRequest (9 tests)

7. **`test_search_request_valid_minimal`**
   - Input : `{"destinations": ["Paris", "Tokyo"], "date_range": {"start": "2025-06-01", "end": "2025-06-15"}}`
   - Attendu : Objet `SearchRequest` créé avec `max_results=10` (défaut)
   - Vérifie : Happy path minimal

8. **`test_search_request_valid_custom_max_results`**
   - Input : Ajout `"max_results": 20`
   - Attendu : Objet `SearchRequest` créé avec `max_results=20`
   - Vérifie : Override défaut

9. **`test_search_request_destinations_too_few`**
   - Input : `{"destinations": ["Paris"], ...}`
   - Attendu : `ValidationError` avec message "at least 2 destinations required"
   - Vérifie : Validation longueur minimum

10. **`test_search_request_destinations_too_many`**
    - Input : `{"destinations": ["Paris", "Tokyo", "London", "NYC", "Berlin", "Rome", "Madrid", "Barcelona", "Amsterdam", "Vienna", "Prague"], ...}`
    - Attendu : `ValidationError` avec message "maximum 10 destinations allowed"
    - Vérifie : Validation longueur maximum

11. **`test_search_request_destinations_duplicates`**
    - Input : `{"destinations": ["Paris", "Tokyo", "Paris"], ...}`
    - Attendu : `ValidationError` avec message "destinations must be unique"
    - Vérifie : Validation unicité

12. **`test_search_request_destinations_empty_string`**
    - Input : `{"destinations": ["Paris", "  ", "Tokyo"], ...}`
    - Attendu : `ValidationError` avec message "destinations cannot be empty or whitespace"
    - Vérifie : Validation destinations non-vides

13. **`test_search_request_max_results_too_low`**
    - Input : `{"max_results": 0, ...}`
    - Attendu : `ValidationError` avec message "max_results must be at least 1"
    - Vérifie : Validation max_results minimum

14. **`test_search_request_max_results_too_high`**
    - Input : `{"max_results": 100, ...}`
    - Attendu : `ValidationError` avec message "max_results cannot exceed 50"
    - Vérifie : Validation max_results maximum

15. **`test_search_request_nested_date_range_invalid`**
    - Input : `{"destinations": ["Paris", "Tokyo"], "date_range": {"start": "2025-06-15", "end": "2025-06-01"}}`
    - Attendu : `ValidationError` (validation nested model `DateRange`)
    - Vérifie : Validation cascade modèles imbriqués

### FlightResult (2 tests)

16. **`test_flight_result_valid`**
    - Input : Tous champs valides
    - Attendu : Objet `FlightResult` créé sans erreur
    - Vérifie : Happy path

17. **`test_flight_result_missing_fields`**
    - Input : Omission champ `airline`
    - Attendu : `ValidationError` (champ obligatoire)
    - Vérifie : Tous champs requis

### SearchStats (1 test)

18. **`test_search_stats_valid`**
    - Input : Tous champs valides
    - Attendu : Objet `SearchStats` créé sans erreur
    - Vérifie : Happy path

### SearchResponse (3 tests)

19. **`test_search_response_valid_with_results`**
    - Input : `results` avec 5 `FlightResult`, `stats` valide, `search_id` UUID
    - Attendu : Objet `SearchResponse` créé sans erreur
    - Vérifie : Happy path complet

20. **`test_search_response_empty_results`**
    - Input : `results=[]`, `stats` valide, `search_id` UUID
    - Attendu : Objet `SearchResponse` créé sans erreur
    - Vérifie : Liste vide autorisée

21. **`test_search_response_nested_validation`**
    - Input : `results` avec `FlightResult` invalide (ex: `price` négatif)
    - Attendu : `ValidationError` (validation nested models)
    - Vérifie : Validation cascade models imbriqués

**Total** : **21 tests** (4 + 2 + 9 + 2 + 1 + 3)

**Coverage attendu** : 100% des validations Pydantic

## 1.8 Exemples JSON

### Exemple 1 : SearchRequest valide (minimal)

**Description** : Requête minimale avec 2 destinations et plage de dates.

```json
{
  "destinations": ["Paris", "Tokyo"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

**Note** : `max_results` prendra la valeur par défaut `10`.

### Exemple 2 : SearchRequest valide (complet)

**Description** : Requête complète avec 3 destinations et `max_results` personnalisé.

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

### Exemple 3 : SearchResponse attendue (succès)

**Description** : Réponse complète avec 3 résultats de vols, statistiques et UUID.

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
    "failed_searches": 1,
    "captcha_detected": 1,
    "total_duration_seconds": 45.32
  },
  "search_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Notes** :
- `results` triés par prix croissant (1250.50 < 1380.00 < 1425.75)
- Maximum 10 résultats (ici 3 seulement trouvés)
- `stats` toujours présent pour monitoring
- `search_id` est un UUID v4 unique

### Exemple 4 : SearchResponse attendue (aucun résultat)

**Description** : Réponse lorsque aucun vol n'a été trouvé.

```json
{
  "results": [],
  "stats": {
    "total_combinations": 12,
    "successful_searches": 0,
    "failed_searches": 12,
    "captcha_detected": 3,
    "total_duration_seconds": 38.21
  },
  "search_id": "7c3a8e2f-4b6d-4c1e-a9f3-2e5d6f8a9b0c"
}
```

**Notes** :
- `results` vide mais structure JSON valide
- `stats.failed_searches = 12` (toutes les tentatives ont échoué)
- `stats.captcha_detected = 3` indique problème possible (rate limiting)
- Utile pour debugging et monitoring
