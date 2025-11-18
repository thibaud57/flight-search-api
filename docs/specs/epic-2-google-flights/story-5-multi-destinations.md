---
title: "Story 5: Multi-destinations (CombinationGenerator)"
epic: "Epic 2: Google Flights Scraping"
story_points: 5
dependencies: ["story-4"]
date: "2025-18-11"
keywords: ["multi-destinations", "combination-generator", "multi-city", "permutations", "itertools", "asyncio-gather", "parallel-crawls", "orchestration", "ranking", "top-10"]
scope: ["specs"]
technologies: ["Python", "itertools", "asyncio", "FastAPI", "Pydantic v2"]
---

# 🎯 Contexte Business

## Besoin utilisateur

### Persona 1: Product Owner
- Besoin de MVP complet multi-destinations pour démo clients réels (2-10 villes)
- Validation technique orchestration crawls parallèles avec performance acceptable (<30s pour 3 destinations)
- Feedback early sur contraintes combinatoires (nombre crawls exponentiels vs performance)
- Démonstration feature signature du produit (multi-city itinéraires complexes)

### Persona 2: Développeur Backend (ce projet)
- Besoin d'orchestrer crawls multiples en parallèle avec asyncio.gather pour performance
- Génération combinaisons intelligente avec itertools.product sans explosion combinatoire
- Réutilisation services Story 4 (CrawlerService, FlightParser) sans modification
- Implémentation ranking Top 10 global (agrégation résultats multi-crawls)

### Persona 3: Utilisateur Final API
- Besoin de recherche multi-destinations réelle (ex: Paris → Tokyo → New York → Paris)
- Top 10 meilleurs prix agrégés sur toutes combinaisons possibles
- Résultats triés par prix croissant avec itinéraires multi-city cohérents
- Temps réponse acceptable (<30s pour 3 destinations, <90s pour 5+ destinations)

## Contraintes métier

### Contraintes fonctionnelles
- **2-10 destinations** : Validation Pydantic déjà implémentée (Story 3), contrainte min 2 villes
- **Combinaisons exponentielles** : 3 destinations → 6 combinaisons aller-retour, 5 destinations → ~20 combinaisons
- **Limite Top 10 global** : Agrégation résultats multi-crawls → tri prix croissant → 10 meilleurs
- **Itinéraires aller-retour complets** : Chaque combinaison termine par ville origine (Paris → Tokyo → Paris)

### Contraintes techniques
- **Crawls parallèles obligatoires** : asyncio.gather pour exécution simultanée, timeout 30s par crawl
- **Gestion échecs partiels** : Continue si 1+ crawls échouent (captcha, timeout), retourne résultats disponibles
- **Pas de cache combinaisons** : Génération dynamique à chaque requête (préparation optimisations Phase 6+)
- **URL multi_city_json format** : JSON segments encodés selon docs/references/google-flights.md

### Contraintes performance et coûts
- **Bandwidth Decodo** : N crawls parallèles = N×500KB-2MB, optimiser nombre combinaisons si > 10
- **Timeout global** : Max 30-90s recherche complète (dépend nb combinaisons)
- **Pas de retry dans cette story** : Retry logic Tenacity reporté Story 6+
- **Type safety strict** : PEP 695, Mypy strict mode, asyncio types annotés

## Valeur business

- ✅ **MVP Feature Complet** : Démo multi-city fonctionnelle pour clients, différenciation concurrents (feature unique)
- ✅ **Validation Performance Crawls Parallèles** : Proof of concept asyncio.gather sur cas réel, mesure temps réponse
- ✅ **Foundation Scalable** : Architecture orchestration prête pour optimisations Phase 6+ (caching, rate limiting)
- ✅ **Feedback Contraintes Combinatoires** : Données réelles pour décision seuil max destinations (ex: limiter à 5 si >20 crawls)
- ✅ **Réutilisation Services Story 4** : Aucune modification CrawlerService/FlightParser nécessaire, principe DRY

## Métriques succès

### Métriques fonctionnelles
- **Recherche 3 destinations < 30s** : p95 temps réponse ≤ 30 secondes (6 crawls parallèles)
- **Top 10 résultats triés** : 100% responses retournent ≤10 FlightResult triés prix croissant
- **Combinaisons cohérentes** : 100% itinéraires terminent par ville origine (validation aller-retour)
- **Handling échecs partiels** : Si 2/6 crawls échouent, retourne 4 résultats disponibles (pas d'erreur 500)

### Métriques qualité
- **Coverage ≥ 80%** : pytest --cov=app atteint 80%+ sur CombinationGenerator, SearchService orchestration
- **21 tests passent** : 6 Generator + 8 Service + 3 Ranking + 4 intégration tous verts
- **Mypy strict mode** : 0 erreur de type
- **Ruff lint/format** : 0 erreur

### Métriques production
- **Logs structurés combinaisons** : Chaque recherche loggée avec nb_combinations, crawls_success, crawls_failed, top_10_price_range
- **Monitoring temps crawls** : Log duration_ms par crawl pour identifier timeouts récurrents
- **Taux échecs crawls** : Calcul `crawls_failed / nb_combinations` pour décision retry logic Phase 6+

---

# 📋 Spécifications Techniques

## 1. CombinationGenerator

**Rôle** : Service générant toutes permutations multi-city aller-retour depuis liste destinations.

**Interface** :
```python
import itertools

class CombinationGenerator:
    """Génère combinaisons multi-city aller-retour."""

    def generate_combinations(
        self,
        destinations: list[str],
        date_range: DateRange
    ) -> list[list[str]]:
        """Génère toutes permutations multi-city aller-retour.

        Args:
            destinations: Liste villes (min 2)
            date_range: Plage dates recherche

        Returns:
            Liste combinaisons format [["Paris", "Tokyo", "Paris"], ...]

        Example:
            >>> gen = CombinationGenerator()
            >>> destinations = ["Paris", "Tokyo", "New York"]
            >>> date_range = DateRange(start="2025-06-01", end="2025-06-15")
            >>> combinations = gen.generate_combinations(destinations, date_range)
            >>> len(combinations)
            6
        """
```

**Algorithme avec itertools.product** :

```python
def generate_combinations(
    self,
    destinations: list[str],
    date_range: DateRange
) -> list[list[str]]:
    """Génère combinaisons multi-city aller-retour."""
    if len(destinations) < 2:
        raise ValueError("destinations must contain at least 2 cities")

    origin = destinations[0]
    other_cities = destinations[1:]

    combinations = []
    for dest in other_cities:
        for intermediate in other_cities:
            if dest != intermediate:
                combinations.append([origin, dest, intermediate, origin])

    if len(combinations) > 10:
        combinations = combinations[:10]

    return combinations
```

**Note Algorithme** : Exemple simplifié ci-dessus génère combinaisons 4 villes. Pour généralisation N destinations, utiliser `itertools.product(destinations, repeat=2)` puis filtrer doublons et ajouter retour origine.

**Règles métier** :

1. **Déduplication** : Éviter combinaisons redondantes (Paris→Tokyo→Paris ≠ Tokyo→Paris→Tokyo car dates différentes)
2. **Limite max 10 combinaisons** : Si > 10 possibilités, prioriser paires directes (origine → destination_i → origine)
3. **Dates utilisées** : Paramètre `date_range` passé pour construction URLs (pas utilisé dans génération combinaisons)

**Exemple génération 3 destinations** :

Input:
```python
destinations = ["Paris", "Tokyo", "New York"]
date_range = DateRange(start="2025-06-01", end="2025-06-15")
```

Output:
```python
[
    ["Paris", "Tokyo", "Paris"],
    ["Paris", "New York", "Paris"],
    ["Paris", "Tokyo", "New York", "Paris"],
    ["Paris", "New York", "Tokyo", "Paris"],
    # ... 6 combinaisons totales
]
```

---

## 2. SearchService Orchestration Multi-Crawls

**Rôle** : Orchestrer génération combinaisons → construction URLs multi-city → crawls parallèles → parsing → ranking Top 10.

**Nouvelle signature (modification Story 3)** :
```python
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlerService
from app.services.flight_parser import FlightParser

class SearchService:
    """Service orchestration recherche vols multi-city."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        crawler_service: CrawlerService,
        flight_parser: FlightParser
    ) -> None:
        """Initialise SearchService avec dépendances injectées."""

    async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
        """Recherche vols multi-city avec crawls parallèles.

        Args:
            request: SearchRequest avec destinations (2-10) et date_range

        Returns:
            Liste FlightResult Top 10 triée prix croissant

        Raises:
            ValueError: Si destinations < 2
            CrawlException: Si tous crawls échouent
        """
```

**Workflow orchestration (6 étapes)** :

1. **Génération combinaisons** :
   ```python
   combinations = self.combination_generator.generate_combinations(
       destinations=request.destinations,
       date_range=request.date_range
   )
   logger.info("Combinations generated", extra={"nb_combinations": len(combinations)})
   ```

2. **Construction URLs multi-city** :
   ```python
   urls = [
       build_multi_city_url(combination=combo, date_range=request.date_range)
       for combo in combinations
   ]
   ```

3. **Crawls parallèles avec asyncio.gather** :
   ```python
   crawl_tasks = [
       self.crawler_service.crawl_google_flights(url)
       for url in urls
   ]
   crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
   ```

4. **Filtrer échecs + Parser HTML** :
   ```python
   parsed_flights = []
   for i, result in enumerate(crawl_results):
       if isinstance(result, Exception):
           logger.warning(
               "Crawl failed",
               extra={"url": urls[i], "error": str(result)}
           )
           continue

       flights = self.flight_parser.parse_flights(
           html=result,
           destinations=combinations[i]
       )
       parsed_flights.extend(flights)
   ```

5. **Ranking Top 10 prix croissant** :
   ```python
   top_10 = rank_flights_by_price(parsed_flights)
   ```

6. **Retour résultats** :
   ```python
   logger.info(
       "Search completed",
       extra={
           "search_id": str(uuid.uuid4()),
           "nb_combinations": len(combinations),
           "crawls_success": sum(1 for r in crawl_results if not isinstance(r, Exception)),
           "crawls_failed": sum(1 for r in crawl_results if isinstance(r, Exception)),
           "total_flights_parsed": len(parsed_flights),
           "top_10_count": len(top_10),
           "price_range": f"{top_10[0].price}-{top_10[-1].price}" if top_10 else "N/A"
       }
   )
   return top_10
   ```

---

## 3. URL Construction Helper Multi-City

**Rôle** : Construire URL Google Flights multi-city avec paramètre `multi_city_json`.

**Interface** :
```python
import json
from urllib.parse import urlencode

def build_multi_city_url(combination: list[str], date_range: DateRange) -> str:
    """Construit URL Google Flights multi-city avec segments JSON.

    Args:
        combination: Liste villes itinéraire (ex: ["Paris", "Tokyo", "Paris"])
        date_range: Plage dates recherche

    Returns:
        URL Google Flights encodée avec multi_city_json

    Example:
        >>> combination = ["Paris", "Tokyo", "New York", "Paris"]
        >>> date_range = DateRange(start="2025-06-01", end="2025-06-15")
        >>> url = build_multi_city_url(combination, date_range)
        >>> print(url)
        https://www.google.com/travel/flights?flight_type=3&multi_city_json=%5B%7B%22departure_id%22%3A%22CDG%22...
    """
```

**Format JSON segments** :
```json
[
  {
    "departure_id": "CDG",
    "arrival_id": "NRT",
    "date": "2025-06-01"
  },
  {
    "departure_id": "NRT",
    "arrival_id": "JFK",
    "date": "2025-06-08"
  },
  {
    "departure_id": "JFK",
    "arrival_id": "CDG",
    "date": "2025-06-15"
  }
]
```

**Implémentation** :
```python
from app.utils.iata_mapping import CITY_TO_IATA

def build_multi_city_url(combination: list[str], date_range: DateRange) -> str:
    """Construit URL multi-city avec segments JSON encodés."""
    segments = []
    num_segments = len(combination) - 1

    for i in range(num_segments):
        departure_city = combination[i]
        arrival_city = combination[i + 1]

        segment_date = date_range.start if i == 0 else date_range.end

        segments.append({
            "departure_id": CITY_TO_IATA.get(departure_city, departure_city),
            "arrival_id": CITY_TO_IATA.get(arrival_city, arrival_city),
            "date": segment_date
        })

    multi_city_json = json.dumps(segments)

    params = {
        "flight_type": "3",
        "multi_city_json": multi_city_json,
        "hl": "fr",
        "curr": "EUR"
    }

    base_url = "https://www.google.com/travel/flights"
    return f"{base_url}?{urlencode(params)}"
```

**Note URL Encoding** : `urlencode()` encode automatiquement JSON (`{` → `%7B`, `"` → `%22`).

---

## 4. Crawls Parallèles avec asyncio.gather

**Pattern asyncio.gather** :
```python
import asyncio

async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
    """Recherche vols avec crawls parallèles."""
    urls = [...]

    crawl_tasks = [
        self.crawler_service.crawl_google_flights(url)
        for url in urls
    ]

    crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

    for i, result in enumerate(crawl_results):
        if isinstance(result, Exception):
            logger.warning(
                "Crawl failed, continuing with other results",
                extra={
                    "url": urls[i],
                    "error_type": type(result).__name__,
                    "error_message": str(result)
                }
            )
            continue
```

**Gestion erreurs** :
- **`return_exceptions=True`** : Continue si 1+ crawls échouent, retourne Exception dans liste résultats
- **Log WARNING** : Logger chaque échec crawl avec URL + error type + error message
- **Pas d'arrêt complet** : Continue traitement résultats valides même si échecs partiels

**Timeout global** :
- Timeout par crawl : 30s (CrawlerService config)
- Timeout global recherche : ~30-90s selon nombre combinaisons (3 destinations ≈ 30s, 5+ destinations ≈ 60-90s)

---

## 5. Top 10 Ranking

**Rôle** : Trier résultats agrégés multi-crawls par prix croissant et limiter à Top 10.

**Interface** :
```python
def rank_flights_by_price(flights: list[FlightResult]) -> list[FlightResult]:
    """Trie vols par prix croissant et limite Top 10.

    Args:
        flights: Liste FlightResult agrégée depuis multi-crawls

    Returns:
        Liste FlightResult Top 10 triée prix croissant

    Example:
        >>> flights = [
        ...     FlightResult(price=1500.00, ...),
        ...     FlightResult(price=1200.00, ...),
        ...     FlightResult(price=1800.00, ...)
        ... ]
        >>> top_10 = rank_flights_by_price(flights)
        >>> top_10[0].price
        1200.00
    """
    sorted_flights = sorted(flights, key=lambda f: f.price)
    return sorted_flights[:10]
```

**Règles métier ranking** :

1. **Priorité prix croissant** : Vol moins cher en premier (index 0)
2. **Égalité prix** : Ordre arbitraire si prix identiques (pas de tri secondaire MVP)
3. **Devise EUR fixe** : Validation déjà faite par FlightResult.currency (Literal["EUR", "USD"]), pas de conversion

**Edge cases** :
- Si `len(flights) == 0` → Retourne `[]`
- Si `len(flights) < 10` → Retourne tous résultats disponibles triés
- Si `len(flights) > 10` → Limite stricte Top 10 meilleurs prix

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CombinationGenerator (6 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_generate_combinations_3_destinations` | 3 destinations | 6 combinaisons aller-retour | Vérifier `len(combinations) == 6` |
| 2 | `test_generate_combinations_2_destinations` | 2 destinations (min) | 1 combinaison aller-retour | Vérifier `len(combinations) == 1` |
| 3 | `test_generate_combinations_respects_max_limit` | 10 destinations | Max 10 combinaisons | Vérifier `len(combinations) <= 10` |
| 4 | `test_generate_combinations_includes_return_to_origin` | 3 destinations | Toutes combinaisons terminent par origine | Vérifier `all(combo[-1] == origin)` |
| 5 | `test_generate_combinations_empty_destinations_raises_error` | `destinations=[]` | ValueError levée | Vérifier exception message |
| 6 | `test_generate_combinations_date_range_used` | date_range fourni | Dates dans combinaisons = date_range | Vérifier cohérence dates |

**Exemple code test AAA** :
```python
import pytest
from app.services.combination_generator import CombinationGenerator
from app.models.request import DateRange

def test_generate_combinations_3_destinations():
    # Arrange: Setup generator with 3 destinations
    generator = CombinationGenerator()
    destinations = ["Paris", "Tokyo", "New York"]
    date_range = DateRange(start="2025-06-01", end="2025-06-15")

    # Act: Generate combinations
    combinations = generator.generate_combinations(
        destinations=destinations,
        date_range=date_range
    )

    # Assert: Verify 6 combinations generated
    assert len(combinations) == 6
    assert all(isinstance(combo, list) for combo in combinations)

def test_generate_combinations_includes_return_to_origin():
    # Arrange: Setup generator
    generator = CombinationGenerator()
    destinations = ["Paris", "Tokyo", "New York"]
    date_range = DateRange(start="2025-06-01", end="2025-06-15")
    origin = destinations[0]

    # Act: Generate combinations
    combinations = generator.generate_combinations(
        destinations=destinations,
        date_range=date_range
    )

    # Assert: Verify all combinations return to origin
    assert all(combo[-1] == origin for combo in combinations)

def test_generate_combinations_empty_destinations_raises_error():
    # Arrange: Setup generator with empty destinations
    generator = CombinationGenerator()
    destinations = []
    date_range = DateRange(start="2025-06-01", end="2025-06-15")

    # Act & Assert: Verify ValueError raised
    with pytest.raises(ValueError) as exc_info:
        generator.generate_combinations(
            destinations=destinations,
            date_range=date_range
        )

    assert "at least 2 cities" in str(exc_info.value).lower()
```

**Total tests unitaires CombinationGenerator** : 6 tests

---

### SearchService Multi-City (8 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_search_service_generates_combinations` | SearchRequest 3 destinations | CombinationGenerator appelé | Vérifier `mock_generator.generate_combinations.called` |
| 2 | `test_search_service_crawls_all_urls` | 6 combinaisons | CrawlerService.crawl appelé 6 fois | Vérifier `mock_crawler.crawl.call_count == 6` |
| 3 | `test_search_service_parses_all_html` | 6 HTML results | FlightParser.parse appelé 6 fois | Vérifier `mock_parser.parse.call_count == 6` |
| 4 | `test_search_service_aggregates_results` | 3 résultats par crawl | Liste agrégée 18 résultats | Vérifier `len(all_results) == 18` |
| 5 | `test_search_service_handles_crawl_failure` | 2/6 crawls échouent | Continue avec 4 résultats | Vérifier log WARNING + résultats partiels |
| 6 | `test_search_service_returns_top_10` | 18 résultats agrégés | Max 10 résultats retournés | Vérifier `len(results) == 10` |
| 7 | `test_search_service_async_execution` | Appel async | Service exécute sans blocage | Vérifier fonction async fonctionne |
| 8 | `test_search_service_dependency_injection` | Mocks injectés | Dépendances utilisées correctement | Vérifier mocks appelés |

**Exemple code test AAA** :
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.search_service import SearchService
from app.models.request import SearchRequest, DateRange

@pytest.mark.asyncio
async def test_search_service_generates_combinations():
    # Arrange: Setup mocks
    mock_generator = MagicMock()
    mock_generator.generate_combinations.return_value = [
        ["Paris", "Tokyo", "Paris"],
        ["Paris", "New York", "Paris"]
    ]
    mock_crawler = AsyncMock()
    mock_parser = MagicMock()

    service = SearchService(
        combination_generator=mock_generator,
        crawler_service=mock_crawler,
        flight_parser=mock_parser
    )

    request = SearchRequest(
        destinations=["Paris", "Tokyo", "New York"],
        date_range=DateRange(start="2025-06-01", end="2025-06-15")
    )

    # Act: Call search_flights
    await service.search_flights(request)

    # Assert: Verify generator called
    mock_generator.generate_combinations.assert_called_once_with(
        destinations=request.destinations,
        date_range=request.date_range
    )

@pytest.mark.asyncio
async def test_search_service_handles_crawl_failure():
    # Arrange: Setup mocks with partial failures
    mock_generator = MagicMock()
    mock_generator.generate_combinations.return_value = [
        ["Paris", "Tokyo", "Paris"],
        ["Paris", "New York", "Paris"]
    ]

    mock_crawler = AsyncMock()
    mock_crawler.crawl_google_flights.side_effect = [
        "<html>Valid HTML</html>",
        Exception("Crawl timeout")
    ]

    mock_parser = MagicMock()
    mock_parser.parse_flights.return_value = [
        MagicMock(price=1200.00)
    ]

    service = SearchService(
        combination_generator=mock_generator,
        crawler_service=mock_crawler,
        flight_parser=mock_parser
    )

    request = SearchRequest(
        destinations=["Paris", "Tokyo", "New York"],
        date_range=DateRange(start="2025-06-01", end="2025-06-15")
    )

    # Act: Call search_flights
    results = await service.search_flights(request)

    # Assert: Verify partial results returned (1 success, 1 failure)
    assert len(results) >= 1
    mock_crawler.crawl_google_flights.assert_called()
```

**Total tests unitaires SearchService** : 8 tests

---

### Ranking (3 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_rank_flights_by_price_sorts_ascending` | Liste 5 vols prix aléatoires | Vols triés prix croissant | Vérifier `results[i].price <= results[i+1].price` |
| 2 | `test_rank_flights_by_price_limits_to_10` | Liste 15 vols | Max 10 résultats | Vérifier `len(results) == 10` |
| 3 | `test_rank_flights_by_price_empty_list` | Liste vide `[]` | Liste vide retournée | Vérifier `len(results) == 0` |

**Exemple code test AAA** :
```python
from app.services.ranking import rank_flights_by_price
from app.models.response import FlightResult

def test_rank_flights_by_price_sorts_ascending():
    # Arrange: Setup flights with random prices
    flights = [
        FlightResult(
            itinerary=["Paris", "Tokyo"],
            price=1500.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        ),
        FlightResult(
            itinerary=["Paris", "New York"],
            price=1200.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        ),
        FlightResult(
            itinerary=["Paris", "Tokyo", "New York"],
            price=1800.00,
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        )
    ]

    # Act: Rank flights
    ranked = rank_flights_by_price(flights)

    # Assert: Verify ascending price order
    assert ranked[0].price == 1200.00
    assert ranked[1].price == 1500.00
    assert ranked[2].price == 1800.00

def test_rank_flights_by_price_limits_to_10():
    # Arrange: Setup 15 flights
    flights = [
        FlightResult(
            itinerary=["Paris", "Tokyo"],
            price=1000.00 + (i * 100),
            currency="EUR",
            departure_date="2025-06-01",
            return_date="2025-06-15"
        )
        for i in range(15)
    ]

    # Act: Rank flights
    ranked = rank_flights_by_price(flights)

    # Assert: Verify Top 10 limit
    assert len(ranked) == 10
```

**Total tests unitaires Ranking** : 3 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**End-to-end** (4 tests) :

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_multi_city_search_3_destinations` | Mocks configurés | POST /api/v1/search-flights avec 3 destinations | 200 + Top 10 résultats triés prix |
| 2 | `test_integration_multi_city_crawls_parallel` | Logs activés | Recherche 3 destinations | Logs montrent crawls parallèles (timestamps simultanés) |
| 3 | `test_integration_multi_city_handles_partial_failures` | 2/6 crawls échouent | Recherche continue | Retourne résultats disponibles (4/6) |
| 4 | `test_integration_multi_city_api_route` | App running | POST endpoint avec 3 destinations | 200 + SearchResponse JSON valide |

**Exemple code test Given/When/Then** :
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app

client = TestClient(app)

def test_integration_multi_city_search_3_destinations():
    # Given: Application configured with mocked services
    with patch('app.services.crawler_service.AsyncWebCrawler') as mock_crawler, \
         patch('app.services.flight_parser.FlightParser') as mock_parser:

        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun.return_value = MagicMock(
            html="<html>Mock flights</html>",
            success=True
        )
        mock_crawler.return_value = mock_crawler_instance

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_flights.return_value = [
            MagicMock(price=1200.00, itinerary=["Paris", "Tokyo"])
        ]
        mock_parser.return_value = mock_parser_instance

        request_data = {
            "destinations": ["Paris", "Tokyo", "New York"],
            "date_range": {
                "start": "2025-06-01",
                "end": "2025-06-15"
            }
        }

        # When: Client sends POST request
        response = client.post("/api/v1/search-flights", json=request_data)

        # Then: Response contains Top 10 sorted results
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 10
        assert all(data["results"][i]["price"] <= data["results"][i+1]["price"] for i in range(len(data["results"])-1))

def test_integration_multi_city_handles_partial_failures():
    # Given: Application with partial crawl failures
    with patch('app.services.crawler_service.AsyncWebCrawler') as mock_crawler:
        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun.side_effect = [
            MagicMock(html="<html>Success 1</html>", success=True),
            Exception("Timeout"),
            MagicMock(html="<html>Success 2</html>", success=True),
            Exception("Captcha detected")
        ]
        mock_crawler.return_value = mock_crawler_instance

        request_data = {
            "destinations": ["Paris", "Tokyo"],
            "date_range": {
                "start": "2025-06-01",
                "end": "2025-06-15"
            }
        }

        # When: Client sends request with partial failures
        response = client.post("/api/v1/search-flights", json=request_data)

        # Then: Response contains available results (no 500 error)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
```

**Total tests intégration** : 4 tests

---

## Fixtures Partagées

**tests/conftest.py** :
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.combination_generator import CombinationGenerator

@pytest.fixture
def mock_combination_generator():
    """Mock CombinationGenerator retournant 3 combinaisons prédéfinies."""
    generator = MagicMock(spec=CombinationGenerator)
    generator.generate_combinations.return_value = [
        ["Paris", "Tokyo", "Paris"],
        ["Paris", "New York", "Paris"],
        ["Paris", "Tokyo", "New York", "Paris"]
    ]
    return generator

@pytest.fixture
def mock_crawler_multiple_urls():
    """Mock CrawlerService retournant HTML différent par URL."""
    crawler = AsyncMock()
    crawler.crawl_google_flights.side_effect = [
        "<html>Flights Paris-Tokyo</html>",
        "<html>Flights Paris-NY</html>",
        "<html>Flights Paris-Tokyo-NY</html>"
    ]
    return crawler

@pytest.fixture
def mock_parser_multiple_flights():
    """Mock FlightParser retournant 3-5 FlightResult par HTML."""
    parser = MagicMock()
    parser.parse_flights.return_value = [
        MagicMock(price=1200.00),
        MagicMock(price=1350.00),
        MagicMock(price=1500.00)
    ]
    return parser
```

---

## Workflow TDD Story 5

**Phase 1 - TDD CombinationGenerator (6 tests)** :
1. Écrire tests CombinationGenerator → Tests échouent (red)
2. Implémenter `generate_combinations()` → Tests passent (green)
3. Refactor si nécessaire

**Phase 2 - TDD SearchService Orchestration (8 tests)** :
1. Écrire tests SearchService multi-city → Tests échouent (red)
2. Implémenter orchestration (asyncio.gather, URL construction) → Tests passent (green)
3. Refactor si nécessaire

**Phase 3 - TDD Ranking (3 tests)** :
1. Écrire tests ranking → Tests échouent (red)
2. Implémenter `rank_flights_by_price()` → Tests passent (green)
3. Refactor si nécessaire

**Phase 4 - Tests Intégration (4 tests)** :
1. Écrire tests end-to-end → Tests échouent ou passent selon implémentation
2. Vérifier workflow complet (request → response)
3. Validation manuelle (curl)

**Total tests Story 5** : 21 tests (17 unitaires + 4 intégration), coverage ≥ 80%

---

# 📝 Exemples JSON et Données

## Exemple 1: Request multi-city 3 destinations

```json
{
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

## Exemple 2: URL multi_city_json encodée

**Combinaison** : `["Paris", "Tokyo", "New York", "Paris"]`

**JSON segments** :
```json
[
  {
    "departure_id": "CDG",
    "arrival_id": "NRT",
    "date": "2025-06-01"
  },
  {
    "departure_id": "NRT",
    "arrival_id": "JFK",
    "date": "2025-06-08"
  },
  {
    "departure_id": "JFK",
    "arrival_id": "CDG",
    "date": "2025-06-15"
  }
]
```

**URL encodée** :
```
https://www.google.com/travel/flights?flight_type=3&multi_city_json=%5B%7B%22departure_id%22%3A%22CDG%22%2C%22arrival_id%22%3A%22NRT%22%2C%22date%22%3A%222025-06-01%22%7D%2C%7B%22departure_id%22%3A%22NRT%22%2C%22arrival_id%22%3A%22JFK%22%2C%22date%22%3A%222025-06-08%22%7D%2C%7B%22departure_id%22%3A%22JFK%22%2C%22arrival_id%22%3A%22CDG%22%2C%22date%22%3A%222025-06-15%22%7D%5D&hl=fr&curr=EUR
```

## Exemple 3: Combinaisons générées (6 pour 3 destinations)

**Input** :
```python
destinations = ["Paris", "Tokyo", "New York"]
```

**Output** :
```python
[
    ["Paris", "Tokyo", "Paris"],
    ["Paris", "New York", "Paris"],
    ["Paris", "Tokyo", "New York", "Paris"],
    ["Paris", "New York", "Tokyo", "Paris"],
    ["Tokyo", "Paris", "New York", "Tokyo"],
    ["New York", "Paris", "Tokyo", "New York"]
]
```

## Exemple 4: SearchResponse Top 10 multi-city

```json
{
  "results": [
    {
      "itinerary": ["Paris", "Tokyo", "Paris"],
      "price": 1150.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Paris", "New York", "Paris"],
      "price": 1200.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Paris", "Tokyo", "New York", "Paris"],
      "price": 1350.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    }
  ],
  "search_id": "b2c3d4e5-f6g7-4890-b123-456789abcdef",
  "total_results": 3
}
```

## Exemple 5: Response partielle (échecs crawls)

**Contexte** : 6 combinaisons générées, 2 crawls échouent (captcha, timeout)

```json
{
  "results": [
    {
      "itinerary": ["Paris", "Tokyo", "Paris"],
      "price": 1200.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    },
    {
      "itinerary": ["Paris", "New York", "Paris"],
      "price": 1350.00,
      "currency": "EUR",
      "departure_date": "2025-06-01",
      "return_date": "2025-06-15"
    }
  ],
  "search_id": "c3d4e5f6-g7h8-4901-c234-567890abcdef",
  "total_results": 2
}
```

---

# 📊 Diagramme Workflow Multi-City

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. POST /api/v1/search-flights                                  │
│    {"destinations": ["Paris", "Tokyo", "New York"], ...}        │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CombinationGenerator.generate_combinations()                 │
│    → Génère 6 combinaisons aller-retour                         │
│    [["Paris", "Tokyo", "Paris"], ...]                           │
│    Timing: <1ms                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. build_multi_city_url() pour chaque combinaison               │
│    → 6 URLs multi_city_json encodées                            │
│    Timing: <10ms                                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. asyncio.gather(*crawl_tasks, return_exceptions=True)         │
│    → Crawl 6 URLs en parallèle                                  │
│    Timing: ~5-30s (timeout 30s/crawl)                           │
│                                                                  │
│    ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐             │
│    │Crawl 1 │  │Crawl 2 │  │Crawl 3 │  │Crawl 4 │ ... (6x)    │
│    └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘             │
│        │           │           │           │                    │
│    Success    Captcha ❌   Success    Timeout ❌               │
└────────┬───────────┬───────────┬───────────┬────────────────────┘
         │           │           │           │
         ↓           ↓           ↓           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Filtrer échecs + FlightParser.parse_flights()                │
│    → 4/6 crawls success = 4 listes FlightResult                 │
│    Timing: ~100-500ms (parsing CSS)                             │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Agrégation résultats multi-crawls                            │
│    → Liste unique 12-20 FlightResult                            │
│    Timing: <10ms                                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. rank_flights_by_price()                                      │
│    → Tri prix croissant + limite Top 10                         │
│    Timing: <10ms                                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. SearchResponse.create(results=top_10)                        │
│    → 200 + JSON Top 10 résultats                                │
│    Timing total: ~5-30s (dominé par crawls)                     │
└─────────────────────────────────────────────────────────────────┘

📌 Points échec possibles (error handling) :
   - Crawl timeout (30s) → Continue avec résultats disponibles
   - Captcha detection → Log WARNING + skip crawl
   - Parsing error → Log ERROR + skip résultat
   - Tous crawls échouent → CrawlException levée (500)

⏱️ Timeouts par étape :
   - CombinationGenerator : <1ms
   - URL construction : <10ms
   - Crawls parallèles : 5-30s (max 30s/crawl)
   - Parsing : 100-500ms
   - Ranking : <10ms
   - Total : ~5-30s (3 destinations), ~30-90s (5+ destinations)
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels (10)

1. **Combinaisons générées correctement** : `generate_combinations(["Paris", "Tokyo", "New York"])` retourne 6 combinaisons aller-retour
2. **Crawls parallèles exécutés** : `asyncio.gather()` exécute N crawls simultanément (N = nb combinaisons)
3. **Top 10 résultats triés prix** : SearchResponse.results contient ≤10 FlightResult triés prix croissant
4. **Itinéraires multi-city cohérents** : 100% FlightResult.itinerary respectent combinaisons générées
5. **Dates utilisées correctement** : URLs multi-city utilisent `date_range.start` et `date_range.end` fournis
6. **Devise EUR fixe** : 100% FlightResult.currency == "EUR"
7. **Max 10 résultats** : `len(SearchResponse.results) <= 10` même si 50+ résultats agrégés
8. **Recherche 3 destinations < 30s** : p95 temps réponse ≤ 30 secondes (6 crawls parallèles)
9. **Handling échecs partiels** : Si 2/6 crawls échouent, retourne 4 résultats disponibles (pas erreur 500)
10. **Validation Pydantic 2-10 destinations** : SearchRequest rejette < 2 destinations (status 422)

## Critères techniques (9)

11. **Type hints PEP 695 strict** : CombinationGenerator, SearchService utilisent `list[str]`, `async def`, type hints complets
12. **asyncio.gather parallélisme** : Crawls exécutés en parallèle (vérifiable via logs timestamps simultanés)
13. **itertools.product combinaisons** : CombinationGenerator utilise `itertools.product()` ou pattern équivalent
14. **Dependency injection services** : SearchService reçoit CombinationGenerator + CrawlerService + FlightParser via `__init__`
15. **URL encoding multi_city_json correct** : `urlencode()` appliqué sur JSON segments, `%7B`, `%22` présents dans URL
16. **Async def orchestration** : `SearchService.search_flights()` est async def avec await asyncio.gather
17. **Exceptions custom propagées** : CrawlException, CaptchaDetectedException propagées correctement depuis CrawlerService
18. **Pydantic validation active** : SearchRequest.destinations valide min_length=2 (déjà implémenté Story 3)
19. **Logging structuré JSON** : Logs contiennent `nb_combinations`, `crawls_success`, `crawls_failed`, `top_10_price_range`

## Critères qualité (8)

20. **Coverage ≥ 80%** : pytest --cov=app atteint 80%+ sur CombinationGenerator, SearchService, ranking modules
21. **21 tests passent** : 6 Generator + 8 Service + 3 Ranking + 4 intégration tous verts
22. **Mypy strict mode** : mypy app/ retourne 0 erreur de type
23. **Ruff lint/format** : ruff check . && ruff format . passent sans erreur
24. **Docstrings 1 ligne** : CombinationGenerator, SearchService, ranking helpers ont docstrings explicites
25. **Format tests AAA/Given-When-Then** : Tests unitaires AAA, tests intégration BDD respectés
26. **Fixtures pytest réutilisables** : `mock_combination_generator`, `mock_crawler_multiple_urls`, `mock_parser_multiple_flights` définis
27. **CI/CD bloque si échec** : GitHub Actions exécute lint + format + typecheck + tests, bloque merge si échec

---

**Note importante** : Cette story (5 story points) complète le MVP multi-destinations. Elle réutilise CrawlerService + FlightParser (Story 4) sans modification, applique orchestration asyncio.gather pour performance, et implémente ranking Top 10 global. Les optimisations (caching combinaisons, retry logic, rate limiting) sont reportées Phase 6+.

**Dépendances Story 4 réutilisées** :
- `CrawlerService.crawl_google_flights(url)` → Aucun changement
- `FlightParser.parse_flights(html, destinations)` → Aucun changement
- `CaptchaDetectedException`, `CrawlException` → Propagées directement

**Principe SMART** : Chaque critère est **S**pécifique (cible claire), **M**esurable (tests automatisés + métriques temps réponse), **A**tteignable (scope MVP multi-city), **R**elevant (valeur business feature signature), **T**emporel (Phase 4.6).
