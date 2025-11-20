---
title: "Story 3: Search endpoint (mock data)"
epic: "Epic 1: API Foundation"
story_points: 8
dependencies: ["epic-1/story-1", "epic-1/story-2"]
date: "2025-20-11"
keywords: ["api", "search", "endpoint", "mock", "pydantic", "fastapi", "validation", "multi-city", "flight-segment", "itinerary", "tdd", "testing"]
scope: ["specs"]
technologies: ["FastAPI", "Pydantic", "pytest", "TestClient"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Développeurs Frontend** : Endpoint API mock pour développer interface utilisateur en parallèle backend (évite blocage attente scraping réel)
- **Product Owner** : Validation UX et format données dès Phase 1 sans dépendance infrastructure scraping complexe
- **QA/Testeurs** : Données mock prévisibles pour tester scénarios edge cases (2 segments minimum, 5 segments maximum, plages dates variables par segment)
- **Équipe Backend** : Contrat API fixé (modèles request/response) avant implémentation scraping réel Phase 5

## Contraintes métier

- **Itinéraires multi-city flexibles** : Support 2-5 segments (vols) avec dates flexibles par segment (ex: Paris→New Delhi 10-20 jan, Tokyo→San Francisco 15-20 fev)
- **Validation explosion combinatoire** : Limite 1000 combinaisons max (produit cartésien dates de tous segments)
- **Données mock réalistes** : 10 résultats hardcodés avec variations prix (800€ - 2500€), compagnies multiples, itinéraires cohérents
- **Performance acceptable** : Response time < 200ms même avec mock data (préparation scalabilité future)
- **Sans dépendances externes** : Aucun appel DB/API/scraping dans cette story (pure mock en mémoire)

## Valeur business

- ✅ **Déblocage développement frontend** : Frontend peut commencer intégration API dès Phase 1 (gain temps ~2 semaines sur planning global)
- ✅ **Validation contrat API early** : Product Owner valide format données avant investissement scraping complexe (dérisquage architectural majeur)
- ✅ **Foundation TDD rigoureuse** : 47 tests (43 unitaires + 4 intégration) définissent comportements attendus pour Phase 5 (tests réutilisables, juste swap mock→scraping)
- ✅ **Feedback rapide stakeholders** : Démo fonctionnelle avec données réalistes dès fin Phase 1 (confiance investisseurs, validation product-market fit)
- ✅ **Documentation vivante** : Modèles Pydantic servent de référence auto-documentée (OpenAPI schema généré automatiquement)

## Métriques succès

- **Couverture tests** : ≥90% sur modèles et endpoint (47 tests couvrent validation, edge cases, intégration)
- **Response time** : < 200ms au p95 pour mock data (baseline performance avant scraping)
- **Adoption frontend** : 100% endpoints frontend utilisent ce contrat API mock (pas de divergence schéma)
- **Taux validation errors détectés** : 100% requêtes invalides rejetées avec messages clairs (segments invalides, dates incohérentes, explosion combinatoire)

---

# 📋 Spécifications Techniques

## 1. FlightSegment Model

**Rôle** : Modèle Pydantic représentant un segment de vol dans un itinéraire multi-city (1 segment = 1 vol unitaire).

**Interface** :

```python
class DateRange(BaseModel):
    """Plage de dates pour recherche vols."""

    start: str
    end: str

class FlightSegment(BaseModel):
    """Segment de vol dans itinéraire multi-city."""

    from_city: Annotated[str, "Ville(s) départ (ex: 'Paris' ou 'Paris,Francfort')"]
    to_city: Annotated[str, "Ville(s) arrivée (ex: 'Tokyo' ou 'Tokyo,Osaka')"]
    date_range: DateRange
```

**Champs FlightSegment** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `from_city` | `str` | Ville(s) départ, séparées par virgule si multiples aéroports | min_length=2, support multi-aéroports "Paris,Francfort" | Requis |
| `to_city` | `str` | Ville(s) arrivée, séparées par virgule si multiples aéroports | min_length=2, support multi-aéroports "Tokyo,Osaka" | Requis |
| `date_range` | `DateRange` | Plage dates voyage pour CE segment | Modèle nested DateRange, max 15 jours par segment | Requis |

**Champs DateRange** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `start` | `str` | Date début voyage au format ISO 8601 | Format YYYY-MM-DD, doit être ≥ date du jour | Requis |
| `end` | `str` | Date fin voyage au format ISO 8601 | Format YYYY-MM-DD, doit être > start | Requis |

**Comportement** :

- **Validation automatique** : Pydantic valide types et contraintes à instanciation
- **Multi-aéroports** : Support format "Paris,Francfort" (virgule-separated) pour flexibilité départ/arrivée
- **Limite date range** : Max 15 jours par segment (évite explosion combinatoire)
- **Erreurs levées** : `ValidationError` si from_city/to_city trop courts, date_range > 15 jours, end ≤ start
- **Normalisation** : Villes trim whitespace (field_validator avec .strip())

**Validations Pydantic** :

- `field_validator('from_city', 'to_city', mode='after')` : Vérifier min 2 caractères après strip
- `field_validator('start', 'end', mode='before')` sur `DateRange` : Valider format ISO 8601 (YYYY-MM-DD), convertir en date objects pour comparaison
- `model_validator(mode='after')` sur `DateRange` : Vérifier end > start (dates cohérentes)
- `model_validator(mode='after')` sur `DateRange` : Vérifier start ≥ date du jour (pas de voyages passés)
- `model_validator(mode='after')` sur `FlightSegment` : Vérifier date_range max 15 jours

**Type hints** :

- ✅ Type hints PEP 695 : `Annotated[str, ...]` pour documentation inline
- ✅ Nested models : DateRange typé explicitement
- ✅ Validators classmethod : `@field_validator @classmethod def validate_field(cls, v: str) -> str:`

---

## 2. SearchRequest Model

**Rôle** : Modèle Pydantic représentant requête utilisateur pour recherche vols multi-city avec segments et validation explosion combinatoire.

**Interface** :

```python
class SearchRequest(BaseModel):
    """Requête de recherche vols multi-city (itinéraire segments fixe, dates flexibles)."""

    segments: Annotated[list[FlightSegment], "Liste segments itinéraire (2-5 segments)"]
```

**Champs SearchRequest** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `segments` | `list[FlightSegment]` | Liste segments vols composant l'itinéraire multi-city | min_length=2, max_length=5, max 1000 combinaisons totales | Requis |

**Comportement** :

- **Validation automatique** : Pydantic valide types et contraintes à instanciation
- **Edge cases** : 2 segments minimum (aller simple = 1 vol non supporté multi-city), 5 segments max (limite Google Flights)
- **Validation explosion combinatoire** : Total combinaisons = range1 × range2 × ... × rangeN ≤ 1000
- **Erreurs levées** : `ValidationError` si <2 segments, >5 segments, >1000 combinaisons totales

**Validations Pydantic** :

- `field_validator('segments', mode='after')` : Vérifier 2 ≤ len(segments) ≤ 5
- `model_validator(mode='after')` sur `SearchRequest` : Calculer total combinaisons et vérifier ≤ 1000 avec message UX-friendly

**Validation explosion combinatoire (algorithme)** :

1. Calculer nombre total combinaisons = produit cartésien de toutes les plages dates des segments
2. Pour chaque segment, extraire nombre de jours dans sa plage (end - start + 1)
3. Multiplier tous les nombres de jours : `total = jours_seg1 × jours_seg2 × ... × jours_segN`
4. Si total > 1000, rejeter avec message UX-friendly suggérant quel segment réduire

**Message erreur format** :
```
Too many combinations: {total}. Max 1000 allowed.
Current ranges: [{jours_seg1}, {jours_seg2}, ...] days per segment.
Suggestion: Reduce segment {index_segment_plus_long} (currently {max_jours} days).
```

**Type hints** :

- ✅ Type hints PEP 695 : `list[FlightSegment]` (pas `List[FlightSegment]`)
- ✅ Nested models : FlightSegment typé explicitement
- ✅ Annotated pour documentation

---

## 3. SearchResponse Model

**Rôle** : Modèle Pydantic représentant réponse API avec top 10 résultats vols et statistiques recherche.

**Interface** :

```python
class FlightResult(BaseModel):
    """Résultat individuel vol (1 sur 10 retournés)."""

    price: Annotated[float, "Prix total itinéraire en EUR"]
    airline: str
    departure_date: str
    segments: list[dict[str, str]]

class SearchStats(BaseModel):
    """Statistiques métadonnées recherche."""

    total_results: int
    search_time_ms: int
    segments_count: int

class SearchResponse(BaseModel):
    """Réponse API contenant top 10 résultats + stats."""

    results: Annotated[list[FlightResult], "Top 10 résultats triés par prix croissant"]
    search_stats: SearchStats
```

**Champs FlightResult** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `price` | `float` | Prix total itinéraire en EUR (ex: 1250.50) | ≥ 0.0, précision 2 décimales | Requis |
| `airline` | `str` | Nom compagnie aérienne (ou "Mixed" si multiples) | min_length=2, max_length=100 | Requis |
| `departure_date` | `str` | Date départ premier segment au format ISO 8601 (YYYY-MM-DD) | Format ISO 8601 valide | Requis |
| `segments` | `list[dict[str, str]]` | Liste segments itinéraire (ex: [{"from": "Paris", "to": "Tokyo", "date": "2025-06-01"}]) | min_length=1, cohérent avec SearchRequest.segments | Requis |

**Champs SearchStats** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `total_results` | `int` | Nombre total résultats trouvés (mock: toujours 10) | ≥ 0, ≤ 10 (Phase 1 mock limité) | Requis |
| `search_time_ms` | `int` | Temps recherche en millisecondes (mock: ~50ms) | ≥ 0, < 10000 (< 10s timeout) | Requis |
| `segments_count` | `int` | Nombre segments dans requête (copie len(SearchRequest.segments)) | ≥ 2, ≤ 5 | Requis |

**Champs SearchResponse** :

| Champ | Type | Description | Contraintes | Default |
|-------|------|-------------|-------------|---------|
| `results` | `list[FlightResult]` | Liste top 10 résultats triés prix croissant | max_length=10, sorted by price ASC | Requis |
| `search_stats` | `SearchStats` | Métadonnées recherche (total, temps, segments) | Modèle nested SearchStats | Requis |

**Comportement** :

- **Tri automatique** : results triés par price croissant (mock data pré-triée)
- **Limitation top 10** : results.length ≤ 10 toujours (Phase 1 mock, Phase 5 scraping top 10 réels)
- **Segments cohérents** : FlightResult.segments doit refléter structure SearchRequest.segments
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

## 4. SearchService (Mock)

**Rôle** : Service métier générant mock data de 10 résultats vols pour Phase 1 (sera remplacé par scraping réel Phase 5).

**Interface** :

```python
class SearchService:
    """Service recherche vols multi-city (mock Phase 1)."""

    def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Retourne 10 résultats mock triés par prix."""
```

**Comportement** :

- **Mock data hardcodé** : Retourne toujours même liste de 10 FlightResult avec variations réalistes
- **Tri prix croissant** : Mock data pré-triée de 800€ à 2500€ environ
- **Compagnies variées** : Air France, Lufthansa, Emirates, Delta, United, British Airways, Qatar Airways, Singapore Airlines, Cathay Pacific, ANA
- **Segments cohérents** : Chaque FlightResult.segments reprend structure SearchRequest.segments avec dates variées
- **Statistiques mock** : search_stats.total_results = 10, search_time_ms = random 30-80ms, segments_count = len(request.segments)

**Mock Data Comportement** :

La méthode `search_flights()` retourne une liste pré-définie de 10 résultats respectant les caractéristiques suivantes :

- **Nombre résultats** : Exactement 10 FlightResult dans tous les cas
- **Prix range** : Variation réaliste entre ~800€ (résultat 1) et ~2500€ (résultat 10)
- **Tri automatique** : Résultats pré-triés par prix croissant
- **Compagnies variées** : Mix compagnies européennes, moyen-orientales, asiatiques, américaines
- **Dates départ** : Distribution sur plages date_range de chaque segment
- **Segments cohérents** : Chaque FlightResult.segments reflète itinéraire SearchRequest.segments

**Contraintes techniques** :

- **Fonction synchrone** : `def search_flights()` (pas async, pas d'I/O externe)
- **Stateless** : Aucun état partagé, chaque appel indépendant
- **Déterministe** : Mock data identique pour inputs identiques (sauf search_time_ms random)
- **Pas de dépendances** : Aucun import crawl4ai, decodo, DB

---

## 5. Route POST /api/v1/search-flights

**Rôle** : Endpoint FastAPI acceptant SearchRequest et retournant SearchResponse via SearchService mock.

**Interface** :

```python
def search_flights_endpoint(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)]
) -> SearchResponse:
    """Endpoint recherche vols multi-city (mock Phase 1)."""
```

**Configuration route** :
- Méthode HTTP : POST
- Endpoint : `/api/v1/search-flights`
- Response model : `SearchResponse` (validation automatique output)
- Status code succès : `200 OK`
- Router : Prefix `/api/v1` avec tag `search` pour documentation OpenAPI

**Paramètres** :

| Paramètre | Type | Description | Contraintes |
|-----------|------|-------------|-------------|
| `request` | `SearchRequest` | Body JSON requête validée par Pydantic | Validation automatique FastAPI, 422 si invalide |
| `search_service` | `SearchService` | Service injecté via Depends() | Singleton ou factory injection |

**Response** :

| Status Code | Body | Description |
|-------------|------|-------------|
| `200 OK` | `SearchResponse` JSON | Recherche succès, top 10 résultats retournés |
| `422 Unprocessable Entity` | Error details JSON | Validation failed (segments invalides, dates incohérentes, explosion combinatoire) |
| `500 Internal Server Error` | Error details JSON | Erreur serveur inattendue (ne devrait pas arriver en Phase 1 mock) |

**Comportement** :

- **Validation automatique** : FastAPI valide SearchRequest body, retourne 422 si invalide
- **Injection SearchService** : SearchService fourni via Depends() (testable, mockable)
- **Response 200 systématique** : Mock data toujours disponible, pas d'erreur attendue Phase 1
- **Logging** : Log info avec extra fields (segments_count, search_time) pour observabilité

**Exemple appel** :

```bash
curl -X POST http://localhost:8000/api/v1/search-flights \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": {"start": "2025-06-01", "end": "2025-06-07"}
      },
      {
        "from_city": "Tokyo",
        "to_city": "New York",
        "date_range": {"start": "2025-06-15", "end": "2025-06-20"}
      }
    ]
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

### FlightSegment + DateRange (15 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_flight_segment_valid_single_cities` | Segment valide avec villes uniques | `{"from_city": "Paris", "to_city": "Tokyo", "date_range": {"start": "2025-06-01", "end": "2025-06-07"}}` | FlightSegment instance créée sans erreur | Vérifie champs obligatoires présents |
| 2 | `test_flight_segment_valid_multi_airports` | Support multi-aéroports séparés virgule | `{"from_city": "Paris,Francfort", "to_city": "Tokyo,Osaka", ...}` | FlightSegment valide | Vérifie format "City1,City2" accepté |
| 3 | `test_flight_segment_city_too_short_fails` | Ville 1 caractère rejetée | `{"from_city": "P", ...}` | Lève `ValidationError` | Vérifie validation min_length=2 |
| 4 | `test_flight_segment_cities_whitespace_trimmed` | Villes avec espaces nettoyées | `{"from_city": "  Paris  ", "to_city": "Tokyo ", ...}` | from_city="Paris", to_city="Tokyo" (trimmed) | Vérifie field_validator .strip() |
| 5 | `test_date_range_valid_dates` | DateRange dates valides | `{"start": "2025-06-01", "end": "2025-06-15"}` | DateRange instance créée | Vérifie parsing dates ISO 8601 |
| 6 | `test_date_range_end_before_start_fails` | End avant start rejetée | `{"start": "2025-06-15", "end": "2025-06-01"}` | Lève `ValidationError` | Vérifie model_validator end > start |
| 7 | `test_date_range_same_day_fails` | Start = end rejetée | `{"start": "2025-06-01", "end": "2025-06-01"}` | Lève `ValidationError` | Vérifie end strictement > start |
| 8 | `test_date_range_start_past_fails` | Start dans le passé rejetée | `{"start": "2020-01-01", "end": "2020-01-15"}` | Lève `ValidationError` | Vérifie model_validator start ≥ today |
| 9 | `test_date_range_invalid_format_fails` | Format date invalide rejeté | `{"start": "01-06-2025", "end": "15-06-2025"}` | Lève `ValidationError` | Vérifie field_validator ISO 8601 strict |
| 10 | `test_date_range_non_existent_date_fails` | Date inexistante rejetée | `{"start": "2025-02-30", "end": "2025-03-01"}` | Lève `ValidationError` | Vérifie validation date réelle |
| 11 | `test_flight_segment_date_range_max_15_days` | Max 15 jours par segment accepté | `{"from_city": "Paris", ..., "date_range": {"start": "2025-06-01", "end": "2025-06-15"}}` | FlightSegment valide (15 jours exactement) | Vérifie limite 15 jours respectée |
| 12 | `test_flight_segment_date_range_over_15_days_fails` | Plus de 15 jours rejeté | `{"date_range": {"start": "2025-06-01", "end": "2025-06-17"}}` | Lève `ValidationError` | Vérifie model_validator max 15 jours |
| 13 | `test_flight_segment_nested_date_range_valid` | FlightSegment avec DateRange nested | Segment complet valide | FlightSegment.date_range instance DateRange | Vérifie nested model parsing |
| 14 | `test_flight_segment_missing_from_city_fails` | Champ from_city manquant | `{"to_city": "Tokyo", "date_range": {...}}` | Lève `ValidationError` | Vérifie champ requis |
| 15 | `test_date_range_future_dates_valid` | Dates très futures acceptées | `{"start": "2030-01-01", "end": "2030-01-10"}` | DateRange valide | Vérifie pas de limite max date future |

### SearchRequest (12 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 16 | `test_search_request_valid_two_segments` | Request valide avec 2 segments (minimum) | `{"segments": [segment1, segment2]}` | SearchRequest instance créée | Vérifie edge case minimum segments (2) |
| 17 | `test_search_request_valid_five_segments` | Request valide avec 5 segments (maximum) | `{"segments": [seg1, seg2, seg3, seg4, seg5]}` | SearchRequest valide | Vérifie edge case maximum segments (5) |
| 18 | `test_search_request_single_segment_fails` | 1 segment rejeté (multi-city minimum 2) | `{"segments": [segment1]}` | Lève `ValidationError` | Vérifie validation min_length=2 |
| 19 | `test_search_request_too_many_segments_fails` | Plus de 5 segments rejetés | `{"segments": [seg1, ..., seg6]}` | Lève `ValidationError` | Vérifie validation max_length=5 |
| 20 | `test_search_request_empty_segments_fails` | Segments vide rejetée | `{"segments": []}` | Lève `ValidationError` | Vérifie validation min_length=2 |
| 21 | `test_search_request_explosion_combinatoire_ok` | 1000 combinaisons exactement accepté | 5 segments avec ranges [10, 2, 5, 2, 5] jours | SearchRequest valide (10×2×5×2×5 = 1000) | Vérifie limite exacte 1000 |
| 22 | `test_search_request_explosion_combinatoire_fails` | Plus de 1000 combinaisons rejeté | 5 segments avec ranges [15, 15, 15, 2, 2] jours | Lève `ValidationError` avec message UX-friendly | Vérifie validation explosion combinatoire |
| 23 | `test_search_request_explosion_message_suggests_reduction` | Message erreur suggère segment à réduire | 3 segments [10, 20, 5] jours (1000+ combos) | ValidationError contient "Reduce segment 2 (currently 20 days)" | Vérifie suggestion intelligente UX |
| 24 | `test_search_request_asymmetric_ranges_valid` | Ranges asymétriques optimisés acceptés | 5 segments [15, 2, 2, 2, 2] jours | SearchRequest valide (15×2⁴ = 240 combos) | Vérifie asymétrie valide |
| 25 | `test_search_request_missing_segments_fails` | Champ segments manquant | `{}` | Lève `ValidationError` | Vérifie champ requis |
| 26 | `test_search_request_model_dump_json_valid` | Serialization JSON valide | SearchRequest instance | JSON parsable et conforme schéma | Vérifie model_dump_json() fonctionne |
| 27 | `test_search_request_type_hints_pep695_compliant` | Type hints code conforme PEP 695 | Code source | list[FlightSegment] (pas List), Annotated utilisé | Vérifie standards projet CLAUDE.md |

### SearchResponse Model (5 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 28 | `test_flight_result_valid_fields` | FlightResult valide | `{"price": 1250.50, "airline": "Air France", "departure_date": "2025-06-01", "segments": [...]}` | FlightResult instance créée | Vérifie champs obligatoires présents |
| 29 | `test_flight_result_negative_price_fails` | Prix négatif rejeté | `{"price": -100.0, ...}` | Lève `ValidationError` | Vérifie field_validator price ≥ 0 |
| 30 | `test_search_stats_valid_fields` | SearchStats valide | `{"total_results": 10, "search_time_ms": 50, "segments_count": 2}` | SearchStats instance créée | Vérifie nested model validé |
| 31 | `test_search_response_results_sorted_by_price` | Results triés prix croissant | Liste FlightResult désordonnée | ValidationError si pas triée (ou auto-sort) | Vérifie model_validator tri prix |
| 32 | `test_search_response_max_10_results` | Max 10 results respecté | 11 FlightResult dans results | Lève `ValidationError` | Vérifie field_validator len ≤ 10 |

### SearchService Mock (6 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 33 | `test_search_service_returns_10_results` | Service retourne 10 résultats | SearchRequest valide | len(response.results) == 10 | Vérifie mock data complet |
| 34 | `test_search_service_results_sorted_by_price` | Résultats triés prix croissant | SearchRequest valide | response.results[0].price < response.results[9].price | Vérifie tri mock data |
| 35 | `test_search_service_segments_match_request` | Segments mock matchent structure request | SearchRequest(segments=[seg1, seg2]) | Tous FlightResult.segments ont 2 segments | Vérifie cohérence mock data |
| 36 | `test_search_service_search_stats_accurate` | search_stats cohérentes | SearchRequest avec 3 segments | search_stats.total_results == 10, segments_count == 3 | Vérifie métadonnées correctes |
| 37 | `test_search_service_deterministic_output` | Mock data identique pour inputs identiques | Même SearchRequest appelée 2x | response1.results == response2.results (sauf search_time_ms) | Vérifie déterminisme mock |
| 38 | `test_search_service_handles_max_segments` | Service gère 5 segments max | SearchRequest avec 5 segments | response.results[0].segments length == 5 | Vérifie edge case max segments |

### Route POST /search-flights (5 tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 39 | `test_endpoint_accepts_valid_request` | Endpoint accepte request valide | POST body SearchRequest valide | Status 200 + SearchResponse JSON | Vérifie comportement nominal |
| 40 | `test_endpoint_validates_request_body` | Body invalide rejeté | POST body segments vide | Status 422 + validation error details | Vérifie validation automatique FastAPI |
| 41 | `test_endpoint_returns_10_results` | Endpoint retourne 10 résultats | POST request valide | response.results.length == 10 | Vérifie intégration SearchService |
| 42 | `test_endpoint_response_matches_schema` | Response conforme SearchResponse schema | POST request valide | JSON validé par SearchResponse model | Vérifie response_model FastAPI |
| 43 | `test_endpoint_injects_search_service_dependency` | SearchService injecté via Depends() | Mock SearchService fourni | Mock service utilisé (vérifiable via spy) | Vérifie dependency injection |

**Total tests unitaires** : 15 (FlightSegment/DateRange) + 12 (SearchRequest) + 5 (SearchResponse) + 6 (SearchService) + 5 (Route) = **43 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**Format tableau descriptif** (5 colonnes) :

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_end_to_end_search_request_valid` | Application FastAPI running avec TestClient, SearchService mock injecté | POST `/api/v1/search-flights` avec body JSON valide (2 segments, dates futures) | Status 200 + JSON response conforme SearchResponse schema avec 10 results triés prix croissant |
| 2 | `test_end_to_end_validation_error_empty_segments` | TestClient configuré | POST `/api/v1/search-flights` avec segments=[] | Status 422 + error details JSON indiquant validation segments failed |
| 3 | `test_end_to_end_validation_error_invalid_dates` | TestClient configuré | POST `/api/v1/search-flights` avec segment.date_range.end < start | Status 422 + error details JSON indiquant validation DateRange failed |
| 4 | `test_end_to_end_openapi_schema_includes_endpoint` | Application running, OpenAPI schema généré | GET `/openapi.json` | Schema contient endpoint POST `/api/v1/search-flights` avec SearchRequest/SearchResponse models documentés |

**Total tests intégration** : 4 tests

**Total tests Story 3** : 43 tests unitaires + 4 tests intégration = **47 tests**

---

## Exemples JSON

**Exemple 1 : Request valide (2 segments)**

```json
{
  "segments": [
    {
      "from_city": "Paris",
      "to_city": "Tokyo",
      "date_range": {
        "start": "2025-06-01",
        "end": "2025-06-07"
      }
    },
    {
      "from_city": "Tokyo",
      "to_city": "New York",
      "date_range": {
        "start": "2025-06-15",
        "end": "2025-06-20"
      }
    }
  ]
}
```

**Combinaisons générées** : 7 dates × 6 dates = 42 combinaisons totales

---

**Exemple 2 : Request valide (5 segments, limite Google Flights)**

```json
{
  "segments": [
    {
      "from_city": "Paris,Francfort",
      "to_city": "New Delhi",
      "date_range": {"start": "2025-01-10", "end": "2025-01-20"}
    },
    {
      "from_city": "New Delhi",
      "to_city": "Tokyo",
      "date_range": {"start": "2025-02-01", "end": "2025-02-05"}
    },
    {
      "from_city": "Tokyo",
      "to_city": "San Francisco",
      "date_range": {"start": "2025-02-15", "end": "2025-02-20"}
    },
    {
      "from_city": "San Francisco",
      "to_city": "New York",
      "date_range": {"start": "2025-03-01", "end": "2025-03-02"}
    },
    {
      "from_city": "New York",
      "to_city": "Paris,Francfort",
      "date_range": {"start": "2025-03-25", "end": "2025-04-01"}
    }
  ]
}
```

**Combinaisons générées** : 11 × 5 × 6 × 2 × 8 = 5,280 combinaisons → **Rejetée** (> 1000 max)

**Message erreur attendu** :
```
Too many combinations: 5280. Max 1000 allowed.
Current ranges: [11, 5, 6, 2, 8] days per segment.
Suggestion: Reduce segment 1 (currently 11 days).
```

---

**Exemple 3 : Request valide (asymétrie optimisée)**

```json
{
  "segments": [
    {
      "from_city": "Paris",
      "to_city": "New Delhi",
      "date_range": {"start": "2025-01-10", "end": "2025-01-24"}
    },
    {
      "from_city": "New Delhi",
      "to_city": "Tokyo",
      "date_range": {"start": "2025-02-01", "end": "2025-02-02"}
    },
    {
      "from_city": "Tokyo",
      "to_city": "San Francisco",
      "date_range": {"start": "2025-02-15", "end": "2025-02-16"}
    },
    {
      "from_city": "San Francisco",
      "to_city": "New York",
      "date_range": {"start": "2025-03-01", "end": "2025-03-02"}
    },
    {
      "from_city": "New York",
      "to_city": "Paris",
      "date_range": {"start": "2025-03-25", "end": "2025-03-26"}
    }
  ]
}
```

**Combinaisons générées** : 15 × 2 × 2 × 2 × 2 = 240 combinaisons → **Acceptée** (≤ 1000)

**Stratégie** : Concentrer flexibilité (15 jours) sur segment 1 (Paris→New Delhi), rigidifier autres segments (2 jours)

---

**Exemple 4 : Response succès (structure avec 10 résultats mock)**

```json
{
  "results": [
    {
      "price": 825.50,
      "airline": "Air France",
      "departure_date": "2025-06-01",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-01"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-15"}
      ]
    },
    {
      "price": 1250.00,
      "airline": "Lufthansa",
      "departure_date": "2025-06-03",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-03"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-17"}
      ]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 50,
    "segments_count": 2
  }
}
```

**Note** : Array `results` contient exactement 10 FlightResult (seulement 2 montrés ici pour lisibilité). Mock data suit pattern : prix croissant (800-2500€), compagnies variées, dates distribuées sur plages, tri automatique par prix.

---

**Exemple 5 : Error 422 (segments vide)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "segments"],
      "msg": "List should have at least 2 items after validation, not 0",
      "input": [],
      "ctx": {
        "min_length": 2
      }
    }
  ]
}
```

---

**Exemple 6 : Error 422 (explosion combinatoire)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Too many combinations: 5280. Max 1000 allowed.\nCurrent ranges: [11, 5, 6, 2, 8] days per segment.\nSuggestion: Reduce segment 1 (currently 11 days).",
      "input": {
        "segments": [...]
      }
    }
  ]
}
```

---

**Exemple 7 : Error 422 (date range > 15 jours)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "segments", 0, "date_range"],
      "msg": "Date range too large: 20 days. Max 15 days per segment.",
      "input": {
        "start": "2025-06-01",
        "end": "2025-06-20"
      }
    }
  ]
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Endpoint accessible** : POST `/api/v1/search-flights` accessible et retourne JSON valide pour requêtes conformes
2. **Validation segments stricte** : Endpoint accepte 2-5 segments, rejette <2 ou >5 avec status 422 et message clair
3. **Validation dates cohérentes** : Endpoint rejette date_range.end ≤ date_range.start avec ValidationError explicite
4. **Validation dates futures** : Endpoint rejette date_range.start dans le passé (< date du jour) avec ValidationError
5. **Validation explosion combinatoire** : Endpoint rejette >1000 combinaisons totales avec message UX-friendly suggérant segment à réduire
6. **Validation max 15 jours/segment** : Endpoint rejette date_range > 15 jours par segment avec ValidationError claire
7. **Support multi-aéroports** : Endpoint accepte format "Paris,Francfort" dans from_city/to_city
8. **Mock data retourné** : Endpoint retourne toujours exactement 10 FlightResult avec prix variés (800€-2500€)
9. **Tri prix garanti** : results triés par price croissant (results[0].price < results[9].price toujours vérifié)
10. **Segments cohérents** : Chaque FlightResult.segments reflète structure SearchRequest.segments avec dates variées
11. **Métadonnées exactes** : search_stats.total_results = 10, segments_count = len(request.segments), search_time_ms > 0

## Critères techniques

12. **Modèles Pydantic v2** : SearchRequest, FlightSegment, SearchResponse héritent BaseModel avec validation automatique
13. **field_validator configurés** : from_city/to_city (min length, trim whitespace), dates (ISO 8601 format), price (≥ 0), date_range (max 15 jours)
14. **model_validator cross-champs** : DateRange vérifie end > start et start ≥ today, SearchRequest vérifie max 1000 combinaisons
15. **Type hints PEP 695 complets** : list[FlightSegment] (pas List), Annotated, type hints sur validators
16. **Nested models** : DateRange, FlightSegment, FlightResult, SearchStats correctement typés et validés
17. **Dependency Injection** : SearchService injecté via Depends() FastAPI (testable, mockable)
18. **Endpoint synchrone** : Route implémentée avec `def` (pas `async def`) car SearchService sync en Phase 1
19. **OpenAPI schema** : Endpoint documenté automatiquement dans /docs avec modèles request/response

## Critères qualité

20. **Coverage ≥90%** : Tests couvrent 100% modèles validation, 100% SearchService mock, 95%+ route (47 tests)
21. **Tous tests passent** : 47 tests (43 unitaires + 4 intégration) exécutés avec succès (0 échecs)
22. **Standards projet conformes** : Ruff lint clean, Mypy strict mode clean, Type hints PEP 695 respectés
23. **Docstrings PEP 257** : Modèles, service et route documentés avec docstrings 1 ligne minimum
24. **Tests AAA/Given-When-Then** : Tests unitaires format AAA, tests intégration format BDD

## Critères production

25. **Logging observabilité** : Endpoint log INFO avec extra fields (segments_count, search_time_ms, total_results)
26. **Response time acceptable** : < 200ms au p95 pour mock data (baseline performance avant scraping Phase 5)
27. **Validation errors clairs** : Messages 422 explicites indiquant champ et contrainte violée, suggestions UX-friendly (UX developer-friendly)
28. **Compatible frontend** : Response JSON sérialisable directement en frontend sans transformation (snake_case cohérent)

---

**Note importante** : Story complexe (8 story points) → 28 critères couvrent exhaustivement validation stricte multi-segments (11 fonctionnels), architecture Pydantic/FastAPI solide (8 techniques), qualité tests rigoureuse (5 qualité), production-ready logging (4 production).

**Principe SMART** : Chaque critère est **S**pécifique (10 résultats triés prix, max 1000 combinaisons), **M**esurable (47 tests passent, coverage ≥90%), **A**tteignable (Pydantic patterns connus), **R**elevant (contrat API foundation MVP multi-city), **T**emporel (Phase 1, avant scraping réel).
