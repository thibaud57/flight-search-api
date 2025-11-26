---
title: "Story 9: Routes Distinctes + KayakUrlBuilder + Renommages"
epic: "Epic 4: Kayak Integration"
story_points: 8
dependencies: ["epic-3/story-7"]
date: "2025-11-26"
keywords: ["kayak", "url", "builder", "validation", "iata", "routes", "api", "google-flights", "renaming", "refactoring"]
scope: ["specs"]
technologies: ["kayak", "pydantic", "fastapi"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- Construire des URLs Kayak valides à partir de paramètres de recherche multi-city
- Valider les codes aéroports IATA avant construction d'URL (éviter erreurs 404)
- Disposer de 2 routes API distinctes `/search-google-flights` et `/search-kayak` (pas de paramètre provider)
- Renommer les composants Google Flights existants pour clarifier la séparation (FlightParser → GoogleFlightParser)

## Contraintes métier

- **Codes IATA stricts** : Kayak rejette codes non valides (3 lettres uppercase uniquement)
- **Format dates ISO** : `YYYY-MM-DD` obligatoire dans le path URL
- **Multi-city 6 segments max** : Kayak limite à 6 segments par recherche
- **2 routes distinctes** : Pas de paramètre `provider` dans SearchRequest, route détermine le provider
- **Renommages cohérents** : Tous fichiers, imports, tests et fixtures doivent être mis à jour

## Valeur business

- ✅ **Foundation Epic 4** : Première story, bloque toutes les suivantes (dépendance critique)
- ✅ **Validation précoce** : Évite crawls inutiles avec URLs invalides (économie bandwidth Decodo)
- ✅ **URL lisibles** : Format Kayak simple `/PAR-TYO/date` (vs Google base64) = debug facile
- ✅ **Testabilité** : Composants purs (pas d'async ni dépendances externes) = TDD simple
- ✅ **Clarté API** : 2 routes distinctes = client sait exactement quel provider il appelle
- ✅ **Évolutivité** : Paramètres provider-specific possibles (ex: Kayak polling config)
- ✅ **Clean architecture** : Renommages explicites (GoogleFlightParser) préparent ajout KayakFlightParser

## Métriques succès

- **Temps construction URL** : <1ms pour URLs 6 segments (fonction pure)
- **Taux validation IATA** : 100% codes valides acceptés, 100% codes invalides rejetés
- **Coverage tests** : ≥95% (composants critiques pour Epic 4)
- **Taux erreur 404 Kayak** : 0% après validation (mesuré en Story 10)
- **Routes accessibles** : 2 endpoints distincts fonctionnels (`/search-google-flights`, `/search-kayak`)
- **Tests routes** : 4 tests intégration routes passent (2 par provider + 2 cross-URL)
- **Renommages complets** : 0 référence à `FlightParser` ou `/search-flights` après story

---

# 📋 Spécifications Techniques

## 1. KayakSegment (Dataclass)

**Rôle** : Représente un segment de vol avec validation IATA stricte

**Interface** :
```python
class KayakSegment:
    """Segment de vol Kayak avec validation IATA."""

    origin: str
    destination: str
    date: str
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `origin` | `str` | Code IATA aéroport départ | 3 lettres, uppercase (ex: `PAR`) |
| `destination` | `str` | Code IATA aéroport arrivée | 3 lettres, uppercase (ex: `TYO`) |
| `date` | `str` | Date vol au format ISO | `YYYY-MM-DD` (ex: `2026-01-14`) |

**Comportement** :

- **Dataclass ou Pydantic BaseModel** : Implémenté avec `@dataclass` ou Pydantic BaseModel selon choix design
- Valide format IATA à la construction (3 lettres uppercase)
- Rejette codes mixedcase (`Par`) ou trop longs (`PARIS`)
- Valide format date ISO-8601 (pattern `^\d{4}-\d{2}-\d{2}$`)
- Lève `ValidationError` si contraintes non respectées

**Validations Pydantic** :

```python
@field_validator("origin", "destination")
@classmethod
def validate_iata_code(cls, v: str) -> str:
    """Valide code IATA 3 lettres uppercase."""

@field_validator("date")
@classmethod
def validate_date_format(cls, v: str) -> str:
    """Valide format date YYYY-MM-DD."""
```

**Erreurs levées** :

- `ValidationError` si origin/destination non conformes (longueur ≠ 3, lowercase)
- `ValidationError` si date non ISO format

---

## 2. KayakUrlBuilder

**Rôle** : Construit URLs Kayak valides à partir de segments validés

**Interface** :
```python
class KayakUrlBuilder:
    """Constructeur d'URLs Kayak multi-city."""

    def __init__(self, base_url: str = "https://www.kayak.fr") -> None:
        """Initialise builder avec URL de base."""

    def build_url(self, segments: list[KayakSegment]) -> str:
        """Construit URL Kayak complète depuis segments."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `base_url` | `str` | URL de base Kayak | Default `"https://www.kayak.fr"` |
| `segments` | `list[KayakSegment]` | Liste segments validés | 1 ≤ len ≤ 6 |

**Comportement** :

- Concatène segments au format `/origin-destination/date/origin-destination/date/...`
- Ajoute query param `?sort=bestflight_a` (tri par pertinence Kayak)
- Rejette listes vides (`len(segments) == 0`)
- Rejette listes >6 segments (limite Kayak)
- Retourne URL complète prête à crawler

**Exemples sorties** :

```python
# 1 segment (aller simple)
"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"

# 2 segments (aller-retour)
"https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"

# 3 segments (multi-city)
"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"
```

**Erreurs levées** :

- `ValueError` si `len(segments) == 0`
- `ValueError` si `len(segments) > 6`

---

## 3. Renommages (FlightParser → GoogleFlightParser)

**Rôle** : Clarifier le code existant pour distinguer les composants Google Flights des futurs composants Kayak

### 3.1 Fichiers à renommer

| Fichier source | Fichier destination | Type |
|----------------|---------------------|------|
| `app/services/flight_parser.py` | `app/services/google_flight_parser.py` | Service |
| `tests/unit/test_flight_parser.py` | `tests/unit/test_google_flight_parser.py` | Test unitaire |

### 3.2 Classes et imports à renommer

| Élément | Avant | Après |
|---------|-------|-------|
| Classe parser | `FlightParser` | `GoogleFlightParser` |
| Import type checking | `from app.services.flight_parser import FlightParser` | `from app.services.google_flight_parser import GoogleFlightParser` |
| Export `__init__.py` | `"FlightParser"` | `"GoogleFlightParser"` |

### 3.3 Fichiers impactés (imports à mettre à jour)

**Code applicatif** :
- `app/services/__init__.py` : Export `GoogleFlightParser`
- `app/services/search_service.py` : Import TYPE_CHECKING
- `app/api/routes.py` : Import et instanciation

**Tests** :
- `tests/unit/test_search_service.py` : Mock du parser
- `tests/integration/test_crawler_parser.py` : Import parser
- `tests/integration/test_retry_integration.py` : Import parser
- `tests/integration/test_search_integration.py` : Import parser

**Fixtures** :
- `tests/fixtures/factories.py` : Renommer fixtures :
  - `flight_parser_mock_factory` → `google_flight_parser_mock_factory`
  - `flight_parser_factory` → `google_flight_parser_factory`

### 3.4 Route API à renommer

| Route | Avant | Après |
|-------|-------|-------|
| Endpoint Google | `POST /api/v1/search-flights` | `POST /api/v1/search-google-flights` |
| Constante helper | `SEARCH_FLIGHTS_ENDPOINT` | `SEARCH_GOOGLE_FLIGHTS_ENDPOINT` |

**Fichiers impactés** :
- `app/api/routes.py` : Annotation route
- `tests/fixtures/helpers.py` : Constante `SEARCH_FLIGHTS_ENDPOINT`
- Tests utilisant la constante

---

## 4. Routes API Distinctes

**Rôle** : Exposer 2 endpoints séparés pour Google Flights et Kayak au lieu d'une route unifiée avec paramètre `provider`

### Architecture des routes

**Route Google Flights (renommée)** :
```python
@router.post("/search-google-flights", response_model=SearchResponse)
async def search_google_flights(request: SearchRequest) -> SearchResponse:
    """Recherche vols multi-city via Google Flights."""
    return await google_search_service.search_flights(request)
```

**Route Kayak (nouvelle)** :
```python
@router.post("/search-kayak", response_model=SearchResponse)
async def search_kayak(request: SearchRequest) -> SearchResponse:
    """Recherche vols multi-city via Kayak."""
    return await kayak_search_service.search_flights(request)
```

### Changements par rapport à l'existant

| Aspect | AVANT | APRÈS |
|--------|-------|-------|
| Route Google | `POST /api/v1/search-flights` | `POST /api/v1/search-google-flights` |
| Route Kayak | N/A | `POST /api/v1/search-kayak` |
| Paramètre provider | `provider: "google_flights" \| "kayak"` dans request | **Supprimé** - route détermine provider |
| SearchRequest | Contient champ `provider` optionnel | **Simplifié** - sans champ `provider` |
| Validation | Literal["google_flights", "kayak"] | Par route (pas de validation runtime) |

### SearchRequest Simplifié

**Interface** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city (format unifié Google/Kayak)."""

    template_url: str
    segments_date_ranges: list[DateRange]
    # Pas de champ provider - déterminé par la route appelée

    model_config = ConfigDict(extra="forbid")
```

**Note** : `template_url` accepte tout format d'URL. C'est le provider appelé qui l'interprète. Techniquement on peut passer une URL Kayak à la route Google (mais le scraping échouera logiquement).

### SearchService avec Injection Provider

**Option retenue** : 1 SearchService réutilisable avec provider injecté

```python
class SearchService:
    """Service orchestration recherche vols."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        crawler_service: CrawlerService,
        flight_parser: GoogleFlightParser,  # Renommé depuis FlightParser
    ) -> None:
        """Provider injecté à l'instanciation."""
```

**Instanciation dans main.py** :
```python
# Services Google Flights (renommés)
google_search_service = SearchService(
    combination_generator,
    crawler_service,
    google_flight_parser  # Renommé depuis flight_parser
)

# Services Kayak (nouveaux après Stories 10-11)
kayak_search_service = SearchService(
    combination_generator,
    crawler_service,      # Réutilisé avec get_kayak_session() (Story 10)
    kayak_flight_parser,  # Story 11
)
```

### Avantages Architecture 2 Routes

1. **Clarté** : Client sait exactement quel provider il appelle
2. **Validation spécifique** : Possibilité future d'ajouter validation URL par provider
3. **Paramètres provider-specific** : Kayak peut avoir `polling_max_wait`, Google non
4. **OpenAPI doc** : 2 endpoints distincts dans Swagger (meilleure UX)
5. **Évolution indépendante** : Ajouter param Kayak n'impacte pas route Google
6. **Pas de validation runtime provider** : Erreur 404 si route inexistante (plus clair que 422)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### KayakSegment (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_segment_valid` | Segment valide avec codes uppercase | `origin="PAR"`, `destination="TYO"`, `date="2026-01-14"` | `segment.origin == "PAR"` | Vérifie création segment nominal |
| 2 | `test_segment_invalid_origin_lowercase` | Code origine lowercase | `origin="par"`, `destination="TYO"`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie validation IATA stricte |
| 3 | `test_segment_invalid_origin_length` | Code origine trop long | `origin="PARIS"`, `destination="TYO"`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie longueur 3 lettres |
| 4 | `test_segment_invalid_destination_empty` | Code destination vide | `origin="PAR"`, `destination=""`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie non-empty destination |
| 5 | `test_segment_invalid_date_format` | Date non ISO | `origin="PAR"`, `destination="TYO"`, `date="14/01/2026"` | Lève `ValidationError` | Vérifie format YYYY-MM-DD |
| 6 | `test_segment_invalid_date_partial` | Date incomplète | `origin="PAR"`, `destination="TYO"`, `date="2026-01"` | Lève `ValidationError` | Vérifie date complète |
| 7 | `test_segment_valid_mixedcase_normalized` | Codes mixedcase normalisés uppercase | `origin="Par"`, `destination="tyo"`, `date="2026-01-14"` | `segment.origin == "PAR"` ou Lève `ValidationError` | Vérifie normalisation ou rejet strict (décision design) |
| 8 | `test_segment_valid_future_date` | Date future lointaine | `origin="PAR"`, `destination="TYO"`, `date="2030-12-31"` | `segment.date == "2030-12-31"` | Vérifie pas de limite date future |

### KayakUrlBuilder (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_build_url_single_segment` | URL aller simple | `[KayakSegment("PAR", "SLZ", "2026-01-14")]` | `"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"` | Vérifie format URL 1 segment |
| 2 | `test_build_url_two_segments` | URL aller-retour | `[segment1, segment2]` avec dates différentes | `"https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"` | Vérifie format URL 2 segments |
| 3 | `test_build_url_three_segments_multicity` | URL multi-city 3 segments | `[segment1, segment2, segment3]` | `"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"` | Vérifie format URL multi-city |
| 4 | `test_build_url_six_segments_max` | URL 6 segments (limite max) | Liste 6 segments | URL valide avec 6 segments concaténés | Vérifie limite supérieure Kayak |
| 5 | `test_build_url_empty_segments` | Liste segments vide | `[]` | Lève `ValueError` | Vérifie validation liste non vide |
| 6 | `test_build_url_seven_segments_exceeds_limit` | Liste >6 segments | Liste 7 segments | Lève `ValueError` | Vérifie limite max 6 segments |
| 7 | `test_build_url_custom_base_url` | Base URL personnalisée | `base_url="https://www.kayak.com"`, 1 segment | URL commence par `"https://www.kayak.com/flights/..."` | Vérifie flexibilité domaine |
| 8 | `test_build_url_sort_param_present` | Query param sort présent | 1 segment | URL finit par `"?sort=bestflight_a"` | Vérifie ajout tri automatique |
| 9 | `test_build_url_segment_separator` | Séparateurs corrects | 2 segments | URL contient `-` entre codes et `/` entre segments | Vérifie séparateurs conformes |
| 10 | `test_build_url_no_trailing_slash` | Pas de slash final | 1 segment | URL ne finit pas par `/` (avant `?sort`) | Vérifie format propre |

### Renommages (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_google_flight_parser_import` | Import GoogleFlightParser | `from app.services import GoogleFlightParser` | Import réussit sans erreur | Vérifie renommage classe |
| 2 | `test_google_flight_parser_file_exists` | Fichier renommé existe | Check `app/services/google_flight_parser.py` | Fichier présent | Vérifie renommage fichier |
| 3 | `test_old_flight_parser_import_fails` | Ancien import échoue | `from app.services import FlightParser` | Lève `ImportError` | Vérifie suppression ancien nom |
| 4 | `test_search_google_flights_endpoint` | Nouvelle route fonctionne | `POST /api/v1/search-google-flights` | Status 200 | Vérifie renommage route |
| 5 | `test_old_search_flights_endpoint_404` | Ancienne route supprimée | `POST /api/v1/search-flights` | Status 404 | Vérifie suppression ancienne route |
| 6 | `test_google_flight_parser_factory_exists` | Factory renommée | Appel `google_flight_parser_factory()` | Retourne mock parser | Vérifie renommage fixtures |

### Routes API (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_route_google_flights_exists` | Route Google Flights accessible | `GET /api/v1/search-google-flights` (405 Method Not Allowed car POST) | Status 405 (route existe) | Vérifie endpoint renommé existe |
| 2 | `test_route_kayak_exists` | Route Kayak accessible | `GET /api/v1/search-kayak` (405 Method Not Allowed) | Status 405 (route existe) | Vérifie nouvel endpoint existe |
| 3 | `test_route_old_search_flights_removed` | Ancienne route supprimée | `POST /api/v1/search-flights` | Status 404 (route n'existe plus) | Vérifie migration complète |
| 4 | `test_search_request_no_provider_field` | SearchRequest sans champ provider | Request avec `{"provider": "google"}` | Status 422 (extra field forbidden) | Vérifie SearchRequest simplifié |

**Total tests unitaires** : 8 + 10 + 6 + 4 = **28 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

### Composants Kayak (1 test)

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_url_builder_with_valid_segments` | 3 segments KayakSegment valides | Appel `builder.build_url(segments)` | URL Kayak complète retournée, format conforme |

### Routes API (4 tests)

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 2 | `test_search_google_flights_route` | App running, mocks configurés | `POST /api/v1/search-google-flights` avec request valide | Status 200 + SearchResponse avec `results` |
| 3 | `test_search_kayak_route` | App running, mocks configurés | `POST /api/v1/search-kayak` avec request valide | Status 200 + SearchResponse avec `results` |
| 4 | `test_google_route_with_kayak_url_works` | App running | `POST /api/v1/search-google-flights` avec URL Kayak | Status 200 (validation passe, scraping échoue) |
| 5 | `test_kayak_route_with_google_url_works` | App running | `POST /api/v1/search-kayak` avec URL Google | Status 200 (validation passe, scraping échoue) |

**Total tests intégration** : 1 + 4 = **5 tests**

**TOTAL STORY 9** : 28 tests unitaires + 5 tests intégration = **33 tests**

---

## Exemples JSON

**Exemple 1 : KayakSegment valide** :
```json
{
  "origin": "PAR",
  "destination": "TYO",
  "date": "2026-03-15"
}
```

**Exemple 2 : Liste segments multi-city** :
```json
[
  {
    "origin": "PAR",
    "destination": "SLZ",
    "date": "2026-01-14"
  },
  {
    "origin": "SLZ",
    "destination": "LIM",
    "date": "2026-03-28"
  },
  {
    "origin": "LIM",
    "destination": "PAR",
    "date": "2026-04-10"
  }
]
```

**Exemple 3 : URL Kayak construite** :
```json
{
  "url": "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a",
  "segments_count": 3,
  "base_url": "https://www.kayak.fr"
}
```

**Exemple 4 : Validation error (code IATA invalide)** :
```json
{
  "error": "ValidationError",
  "detail": [
    {
      "loc": ["origin"],
      "msg": "Code IATA must be 3 uppercase letters",
      "input": "paris"
    }
  ]
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Validation IATA stricte** : KayakSegment rejette codes non conformes (longueur ≠ 3, lowercase, vide)
2. **Validation dates ISO** : KayakSegment rejette dates non ISO-8601 (`DD/MM/YYYY`, dates partielles)
3. **Construction URL 1 segment** : `builder.build_url([segment])` retourne URL aller simple valide
4. **Construction URL multi-city** : `builder.build_url([s1, s2, s3])` retourne URL multi-city avec segments concaténés
5. **Limite 6 segments** : `builder.build_url([s1...s7])` lève `ValueError`
6. **Query param sort** : Toutes URLs finissent par `?sort=bestflight_a`
7. **Route Google Flights renommée** : `POST /api/v1/search-google-flights` remplace `/search-flights`
8. **Route Kayak créée** : `POST /api/v1/search-kayak` disponible et fonctionnelle
9. **SearchRequest simplifié** : Pas de champ `provider`, route détermine le provider
10. **Ancienne route supprimée** : `/search-flights` retourne 404
11. **Classe renommée** : `FlightParser` → `GoogleFlightParser` dans tout le code
12. **Fichier renommé** : `flight_parser.py` → `google_flight_parser.py`
13. **Fixtures renommées** : `flight_parser_factory` → `google_flight_parser_factory`

## Critères techniques

14. **Type safety strict** : Utiliser Literal types pour `base_url`, annotations complètes PEP 695
15. **Pydantic validators** : `@field_validator` pour validation IATA et dates
16. **Fonction pure builder** : Pas d'effets de bord, déterministe (mêmes inputs → même output)
17. **Dataclass ou Pydantic** : KayakSegment implémenté avec Pydantic BaseModel pour validations
18. **Pas de dépendance DB/API** : Composants purs (URL builder, validation IATA)
19. **2 services distincts** : `google_search_service` et `kayak_search_service` instanciés séparément
20. **Imports mis à jour** : Tous imports `FlightParser` remplacés par `GoogleFlightParser`

## Critères qualité

21. **Coverage ≥95%** : Tests unitaires couvrent tous chemins (nominal + edge cases)
22. **28 tests unitaires + 5 intégration** : Tous verts avant merge
23. **Ruff + Mypy** : Code conforme standards projet (PEP 8, type hints)
24. **Docstrings 1 ligne** : Toutes classes/méthodes publiques documentées
25. **Pas de commentaires inline** : Code self-explanatory (sauf justification explicite)
26. **Fixtures réutilisables** : Fixtures `kayak_segment_factory`, `google_flight_parser_factory` dans `conftest.py`
27. **0 référence anciens noms** : Grep `FlightParser` et `/search-flights` retourne 0 résultat

## Critères production

28. **Logs provider** : Logger provider dans routes (`extra={"provider": "google_flights" | "kayak"}`)

---

**💡 Note** : Cette story contient **28 critères** pour 8 story points (story complexité élevée avec composants critiques pour Epic 4 + setup routes + renommages).

**Principe SMART** : Tous critères vérifiables via tests automatisés (pas de validation manuelle nécessaire).
