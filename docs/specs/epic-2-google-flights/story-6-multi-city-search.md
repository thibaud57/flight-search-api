---
title: "Story 6: Multi-city Search (CombinationGenerator)"
epic: "Epic 2: Google Flights Scraping"
story_points: 5
dependencies: ["epic-2/story-4", "epic-2/story-5"]
date: "2025-20-11"
keywords: ["multi-city", "combination-generator", "flight-segment", "itertools-product", "cartesian-product", "asyncio-gather", "parallel-crawls", "orchestration", "ranking", "top-10"]
scope: ["specs"]
technologies: ["Python", "itertools", "asyncio", "FastAPI", "Pydantic v2"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Utilisateurs business** : Planifier itinéraires multi-city complexes avec flexibilité dates par segment (ex: Paris→New Delhi 10-20 jan, Tokyo→San Francisco 15-20 fev, etc.)
- **Optimisation budgets voyage** : Tester automatiquement toutes combinaisons dates possibles (produit cartésien) et identifier le top 10 des options les plus économiques
- **Gain temps recherche** : Éviter recherches manuelles multiples sur Google Flights (N combinaisons pour N segments avec M dates = explosion exponentielle)
- **Itinéraires fixes avec dates flexibles** : Ordre segments fixe (Paris→Tokyo→NYC toujours), mais dates départ chaque segment varient (explorer meilleures fenêtres temporelles)

## Contraintes métier

- **MVP limité 2-5 segments** : Focus MVP sur 2-5 segments (contrainte SearchRequest.segments min 2, max 5), aligné limite Google Flights
- **Explosion combinatoire** : Produit cartésien dates segments = volume requêtes important (ex: 5 segments × [10, 5, 6, 2, 8] jours = 4,800 URLs potentielles → limite 1000 validée Story 3)
- **Coûts bandwidth Decodo** : Chaque crawl = ~200-500KB HTML téléchargé via proxies résidentiels ($2.60-3.50/GB), nécessite optimisation nombre de crawls
- **Rate limiting Google Flights** : Requêtes massives simultanées peuvent déclencher rate limiting (status 429) ou captchas, nécessite throttling intelligent
- **Timeout total acceptable** : Recherche multi-city doit compléter en <60 secondes au p95 (user experience web) en mode POC dev local

## Valeur business

- **Économies utilisateur quantifiables** : Algorithme ranking trouve différences prix jusqu'à 30-40% entre meilleure et pire combinaison dates (économies moyennes 200-400€ par recherche)
- **Foundation orchestration scalable** : CombinationGenerator + SearchService établissent patterns réutilisables pour futures optimisations (caching, parallélisation avancée, webhooks)
- **Différenciation compétitive** : Fonctionnalité multi-city avec dates flexibles par segment et ranking automatique absente des outils grand public (Kayak, Skyscanner limités à 2-3 étapes sans flexibilité dates granulaire)
- **Métriques observables actionables** : Logging structuré fournit insights sur combinaisons populaires, taux succès crawl par route, patterns prix pour amélioration continue

## Métriques succès

- **Génération combinaisons correcte** : 100% produit cartésien dates généré (ex: [7, 6] jours = 42 combinaisons, [10, 5, 6, 2, 8] jours = 4,800 combinaisons avant limite 1000)
- **Taux succès crawl global POC** : Baseline POC dev local sans retry logic (taux succès variable selon captchas Google)
- **Précision ranking Top 10** : Top 1 résultat toujours prix minimum réel sur ensemble combinaisons testées (validation manuelle échantillon)
- **Temps exécution total** : <60 secondes au p95 pour recherche 3 segments × [7, 6, 5] jours (210 combinaisons × crawl + parsing + ranking)
- **Coverage tests** : ≥80% sur CombinationGenerator et SearchService (unitaires + intégration)
- **Qualité extraction vols** : ≥95% des combinaisons retournent ≥5 vols parsés par route (dépend FlightParser Story 4)

---

# 📋 Spécifications Techniques

## 1. CombinationGenerator

**Rôle** : Générer toutes les combinaisons dates possibles depuis une liste de segments FlightSegment, en utilisant itertools.product pour produit cartésien (ordre segments fixe, dates varient).

**Interface** :
```python
class CombinationGenerator:
    """Générateur de combinaisons multi-city (produit cartésien dates par segment)."""

    def generate_combinations(
        self,
        segments: list[FlightSegment]
    ) -> list[DateCombination]:
        """
        Génère produit cartésien dates pour N segments (ordre fixe).

        Returns:
            Liste de DateCombination avec dates distribuées par segment
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `segments` | `list[FlightSegment]` | Liste segments itinéraire (ex: [Paris→Tokyo, Tokyo→NYC]) | min_length=2, max_length=5 (validé SearchRequest Story 3) |
| **Retour** | `list[DateCombination]` | Liste combinaisons dates | Length = produit cartésien jours (range1 × range2 × ... × rangeN) |

**Modèle DateCombination** :
```python
class DateCombination(BaseModel):
    """Représente une combinaison dates pour itinéraire multi-city fixe."""

    segment_dates: list[str]
```

| Champ DateCombination | Type | Description | Contraintes |
|-------------------|------|-------------|-------------|
| `segment_dates` | `list[str]` | Dates départ chaque segment (format YYYY-MM-DD) | Length = len(segments), chaque date dans date_range segment correspondant |

**Comportement** :

- **Génération nominale** :
  1. Extraire date_range de chaque segment
  2. Générer liste dates pour chaque segment (start à end inclusif)
  3. Calculer produit cartésien toutes listes dates avec `itertools.product(*all_dates)`
  4. Retourner liste de DateCombination avec chaque combinaison dates

- **Algorithme produit cartésien** :
  - 2 segments [7 jours, 6 jours] → 7 × 6 = 42 combinaisons
  - 3 segments [7 jours, 6 jours, 5 jours] → 7 × 6 × 5 = 210 combinaisons
  - 5 segments [10, 5, 6, 2, 8] jours → 10 × 5 × 6 × 2 × 8 = 4,800 combinaisons (→ rejeté limite 1000 Story 3)

- **Distribution dates** :
  - segment.date_range = "2025-06-01" à "2025-06-07" → 7 dates possibles
  - Chaque combinaison teste une date par segment (ex: [2025-06-01, 2025-06-15], [2025-06-01, 2025-06-16], ...)

- **Edge cases** :
  - **2 segments minimum** : 2 date ranges minimum (validé SearchRequest)
  - **5 segments max MVP** : Produit cartésien max 1000 combinaisons (validé SearchRequest)
  - **date_range 1 jour** : Si segment.date_range.start = end → 1 date (range 1 jour = date exacte), si 2 jours → 2 dates
  - **Asymétrie ranges** : Supporte [15, 2, 2, 2, 2] jours = 15 × 2⁴ = 240 combinaisons (optimisation validée Story 3)

- **Optimisations futures** :
  - Post-MVP : Filtrer combinaisons symétriques si aller-retour même point départ/arrivée
  - Post-MVP : Limiter dates testées à jours spécifiques semaine (ex: vendredis uniquement)

**Erreurs levées** :
- Aucune exception levée (validation données effectuée en amont par SearchRequest Story 3)

**Logging structuré** :
- INFO : Nombre segments, jours par segment, total combinaisons créées
- DEBUG : Première et dernière combinaison générée (sample pour vérification)

---

## 2. SearchService (Orchestration Multi-City)

**Rôle** : Orchestrer la recherche multi-city complète : génération combinaisons, crawling parallèle de toutes les URLs Google Flights, parsing vols, ranking Top 10 résultats par prix croissant.

**Interface** :
```python
class SearchService:
    """Service orchestration recherche vols multi-city."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        crawler_service: CrawlerService,
        flight_parser: FlightParser
    ):
        """Initialise service avec dépendances injectées."""

    async def search_flights(
        self,
        request: SearchRequest
    ) -> SearchResponse:
        """
        Orchestre recherche complète multi-city avec ranking Top 10.

        Returns:
            SearchResponse avec top 10 résultats triés par prix total croissant
        """
```

**Dépendances Services** :

| Service | Rôle | Défini dans |
|---------|------|-------------|
| `CombinationGenerator` | Génère produit cartésien dates par segment | Story 6 (ce document) |
| `CrawlerService` | Crawle Google Flights avec stealth mode | Story 4 |
| `FlightParser` | Parse HTML Google Flights en liste Flight | Story 4 |

**Comportement Orchestration** :

**Étape 1 : Génération Combinaisons**
1. Appeler `combination_generator.generate_combinations(request.segments)`
2. Recevoir liste de DateCombination (ex: 210 combinaisons pour 3 segments × [7, 6, 5] jours)
3. Logger INFO : nombre total combinaisons à crawler

**Étape 2 : Construction URLs Google Flights**
Pour chaque DateCombination :
1. Construire URL multi-city Google Flights avec paramètre `multi_city_json`
2. Format JSON segments : `[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-06-01"}, ...]`
3. Mapper FlightSegment → multi_city_json :
   - `segment.from_city` → `departure_id` (support multi-aéroports "Paris,Francfort" transformé en "CDG,FRA")
   - `segment.to_city` → `arrival_id`
   - `date_combination.segment_dates[i]` → `date` (date spécifique pour ce segment dans cette combinaison)
4. URL-encoder JSON et ajouter paramètres localisation `hl=fr&curr=EUR`
5. Exemple URL : `https://www.google.com/travel/flights?flight_type=3&multi_city_json=[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-06-01"},{"departure_id":"NRT","arrival_id":"JFK","date":"2025-06-15"}]&hl=fr&curr=EUR`

**Étape 3 : Crawling Parallèle**
1. Appeler `crawler_service.crawl_google_flights(url)` pour chaque combinaison
2. Stratégie parallélisation : `asyncio.gather()` avec limite concurrence (ex: 5-10 requêtes simultanées max pour éviter rate limiting)
3. Gérer erreurs crawl :
   - CrawlerService tente automatiquement 3 fois (retry logic Story 7 via @retry decorator)
   - Si échec persistant (exception finale après max retries) → Logger WARNING, skip combinaison
   - Continuer autres combinaisons (gestion erreurs gracieuse, pas d'exception bloquante)
4. Logger INFO : Nombre crawls réussis vs échecs

**Étape 4 : Parsing Vols**
Pour chaque HTML crawlé avec succès :
1. Appeler `flight_parser.parse(html)` (retourne `list[GoogleFlightDTO]` = N options de vol)
2. Sélectionner meilleure option : `best = flights[0]` (Google retourne options triées par prix)
3. Créer résultat : `CombinationResult(date_combination=combo, best_flight=best)`
4. Gérer erreurs parsing : Si ParsingError → Logger WARNING, skip combinaison
5. Logger INFO : Nombre combinaisons parsées avec succès

**Étape 5 : Ranking Top 10**
1. Trier tous les `CombinationResult` par `best_flight.price` croissant
2. Sélectionner top 10 résultats (ou moins si <10 combinaisons réussies)
3. Logger INFO : Prix min/max trouvés

**Étape 6 : Construction SearchResponse**
1. Transformer top 10 CombinationResult en FlightResult (format SearchResponse Story 3)
2. Calculer SearchStats : total_results, search_time_ms, segments_count
3. Retourner SearchResponse

**Edge cases** :
- **Aucun crawl réussi** : Retourner SearchResponse vide avec search_stats.total_results=0
- **Erreurs partielles** : Si ≥50% combinaisons échouent → Logger ERROR mais retourner top résultats disponibles
- **Timeout global** : Si durée totale >60s → Logger WARNING, retourner résultats partiels déjà crawlés
- **Combinaisons ex-aequo prix** : Départager par durée totale trajet (sum flight.duration), puis par nombre escales (sum flight.stops)

**Erreurs levées** :
- Aucune exception levée par search_flights (gestion erreurs gracieuse, retourne résultats partiels)
- Logging ERROR si tous les crawls échouent (mais response vide retournée)

**Logging structuré** :
- INFO : Début search avec segments, date_ranges
- INFO : Combinaisons générées (count), URLs construites
- INFO : Crawls terminés (succès/échecs), parsing terminé (count vols)
- INFO : Top 10 sélectionné avec prix min/max
- ERROR : Taux échec crawl >50%

---

## 3. Top 10 Ranking (Algorithme)

**Rôle** : Sélectionner et trier les 10 meilleures combinaisons de vols par prix croissant.

**Critère de Ranking** : **Prix total uniquement** (`best_flight.price`)

**Algorithme Sélection Top 10** :

1. **Trier** tous les `CombinationResult` par `best_flight.price` croissant
2. **Sélectionner** les 10 premiers résultats
3. **Retourner** liste triée (prix min en position 0)

**Exemple Concret Ranking** :

**Input (3 combinaisons)** :

| # | Dates segments | Prix Total |
|---|----------------|-----------|
| 1 | [2025-06-01, 2025-06-15] | 1250€ |
| 2 | [2025-06-03, 2025-06-17] | 1800€ |
| 3 | [2025-06-05, 2025-06-20] | 980€ |

**Output Top 10 (trié par prix)** :

1. Dates [2025-06-05, 2025-06-20] (980€)
2. Dates [2025-06-01, 2025-06-15] (1250€)
3. Dates [2025-06-03, 2025-06-17] (1800€)

**Edge cases** :
- **<10 combinaisons totales** : Retourner toutes les combinaisons disponibles (ex: 5 combinaisons → top 5)
- **Combinaisons même prix** : Ordre stable (premier crawlé en premier)

---

## 4. Modèles Pydantic

### FlightSegment et SearchRequest (Référence Story 3)

**Défini dans** : `docs/specs/epic-1-api-foundation/story-3-search-endpoint.md`

**Champs réutilisés** :
- `FlightSegment` : from_city, to_city, date_range (max 15 jours/segment)
- `SearchRequest.segments` : list[FlightSegment] (min 2, max 5, max 1000 combinaisons)

**Validations réutilisées** :
- `field_validator('segments')` : 2 ≤ len ≤ 5
- `model_validator` : Explosion combinatoire ≤ 1000
- `model_validator` sur FlightSegment : date_range max 15 jours

---

### DateCombination (Nouveau Modèle Story 6)

**Rôle** : Modèle représentant une combinaison dates pour itinéraire multi-city (ordre segments fixe, dates spécifiques par segment).

**Interface** :
```python
class DateCombination(BaseModel):
    """Combinaison dates pour itinéraire multi-city fixe."""

    segment_dates: list[str]
```

**Champs** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `segment_dates` | `list[str]` | Dates départ chaque segment (format YYYY-MM-DD) | Length = len(segments request), chaque date ISO 8601 valide |

**Validations Pydantic** :

- `field_validator('segment_dates', mode='after')` : Vérifier toutes dates format ISO 8601 (YYYY-MM-DD)
- `field_validator('segment_dates', mode='after')` : Vérifier len(segment_dates) ≥ 2 (cohérence SearchRequest min 2 segments)

**Comportement** :
- Modèle généré automatiquement par CombinationGenerator
- Utilisé pour construction URLs Google Flights multi_city_json

---

### CombinationResult (Nouveau Modèle Story 6)

**Rôle** : Modèle intermédiaire pour stocker résultat crawl + parsing d'une combinaison avant ranking.

**Interface** :
```python
class CombinationResult(BaseModel):
    """Résultat intermédiaire pour une combinaison dates."""

    date_combination: DateCombination
    best_flight: GoogleFlightDTO
```

**Champs** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `date_combination` | `DateCombination` | Combinaison dates testée | Modèle nested DateCombination |
| `best_flight` | `GoogleFlightDTO` | Meilleure option vol sélectionnée | Requis, contient price (total itinéraire), duration, stops |

**Notes importantes** :
- `best_flight.price` = prix TOTAL de l'itinéraire (pas par segment, fourni par Google Flights)
- `best_flight.duration` et `best_flight.stops` = données du segment affiché (limitation Google Flights multi-city)
- Pas de champs calculés (`total_price`, etc.) car accès direct via `best_flight.price`

**Comportement** :
- Modèle créé par SearchService après parsing avec `best_flight=flights[0]`
- Utilisé pour ranking (tri par `best_flight.price`) avant transformation en FlightResult

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CombinationGenerator (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_generate_combinations_two_segments` | Génère produit cartésien pour 2 segments | `segments=[seg1(7j), seg2(6j)]` | 42 combinaisons (7 × 6) | Vérifie calcul produit cartésien |
| 2 | `test_generate_combinations_three_segments` | Génère produit cartésien pour 3 segments | `segments=[seg1(7j), seg2(6j), seg3(5j)]` | 210 combinaisons (7 × 6 × 5) | Vérifie algorithme produit cartésien complet |
| 3 | `test_generate_combinations_five_segments_asymmetric` | Génère combinaisons asymétriques optimisées | `segments` 5 segments [15, 2, 2, 2, 2] jours | 240 combinaisons (15 × 2⁴) | Vérifie asymétrie valide |
| 4 | `test_generate_combinations_segment_dates_format` | Dates générées format ISO 8601 | `segments=[seg1, seg2]` | Toutes segment_dates format YYYY-MM-DD | Vérifie format dates |
| 5 | `test_generate_combinations_dates_within_ranges` | Dates générées dans plages segments | `seg1.date_range="2025-06-01" à "2025-06-07"` | Toutes dates combinaisons segment 1 entre 01 et 07 juin | Vérifie dates respectent ranges |
| 6 | `test_generate_combinations_date_range_single_day` | Segment avec 2 jours génère 2 dates | `seg.date_range` start="2025-06-01", end="2025-06-02" | 2 dates possibles pour ce segment | Vérifie edge case minimum range |
| 7 | `test_date_combination_model_valid_fields` | Modèle DateCombination valide | `segment_dates=["2025-06-01", "2025-06-15"]` | DateCombination instance créée | Vérifie validation Pydantic |
| 8 | `test_combinations_unique_dates` | Toutes combinaisons sont uniques | `segments=[seg1(3j), seg2(3j)]` | 9 combinaisons avec 9 tuples dates distinctes | Vérifie absence doublons |
| 9 | `test_combinations_dates_ordered_chronologically` | Dates générées ordre chronologique par segment | `seg.date_range` "2025-06-01" à "2025-06-07" | Dates segment triées 01, 02, ..., 07 | Vérifie ordre dates respecté |
| 10 | `test_generate_combinations_logging` | Logging INFO avec statistiques génération | `segments` 3 segments | Logs contiennent segments_count=3, days_per_segment=[7,6,5], total_combinations=210 | Vérifie logging structuré observabilité |

### SearchService (15 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 11 | `test_search_flights_orchestration_success` | Orchestration complète avec tous crawls réussis | `SearchRequest` 2 segments × [7j, 6j], mock CrawlerService/FlightParser succès | `SearchResponse` avec top 10 résultats triés prix croissant | Vérifie flow nominal complet |
| 12 | `test_search_flights_calls_combination_generator` | SearchService appelle CombinationGenerator | `SearchRequest` avec segments valides | `combination_generator.generate_combinations()` appelé 1 fois avec segments | Vérifie intégration CombinationGenerator |
| 13 | `test_search_flights_crawls_all_urls` | Crawle toutes URLs générées | Mock 42 combinaisons générées (2 segments × [7j, 6j]) | `crawler_service.crawl_google_flights()` appelé 42 fois (1 par combinaison) | Vérifie crawl exhaustif toutes combinaisons |
| 14 | `test_search_flights_parallel_crawling_asyncio_gather` | Crawling parallèle avec asyncio.gather | Mock 10 combinaisons | asyncio.gather utilisé avec liste 10 tasks async | Vérifie parallélisation async |
| 15 | `test_search_flights_parses_all_html` | Parse HTML de tous crawls réussis | Mock 42 HTML valides crawlés | `flight_parser.parse()` appelé 42 fois avec chaque HTML | Vérifie parsing systématique après crawl |
| 16 | `test_search_flights_ranking_top_10` | Sélectionne top 10 résultats par prix | Mock 50 combinaisons avec prix variés 800-2000€ | `SearchResponse.results` length=10, trié prix croissant (results[0].price < results[9].price) | Vérifie algorithme ranking prix |
| 17 | `test_search_flights_ranking_price_only` | Tri par prix uniquement | Mock 3 combinaisons : 1000€, 1200€, 900€ | Top 1 = 900€, top 2 = 1000€, top 3 = 1200€ | Vérifie tri prix croissant |
| 18 | `test_search_flights_ranking_same_price_stable` | Ordre stable si même prix | Mock 2 combinaisons même prix 1000€ | Ordre préservé (premier crawlé en premier) | Vérifie stabilité tri |
| 19 | `test_search_flights_handles_partial_crawl_failures` | Gestion erreurs crawl partielles (50% échecs) | Mock 42 combinaisons : 21 crawls succès, 21 CaptchaDetectedError | `SearchResponse` avec 10 résultats (meilleurs parmi 21 crawls réussis), logs WARNING pour 21 échecs | Vérifie résilience erreurs partielles |
| 20 | `test_search_flights_returns_empty_all_crawls_failed` | Retourne response vide si tous crawls échouent | Mock 42 combinaisons : toutes lèvent NetworkError | `SearchResponse.results=[]`, `search_stats.total_results=0`, logs ERROR | Vérifie edge case échec total |
| 21 | `test_search_flights_constructs_google_flights_urls` | Construction URLs multi-city correctes | `DateCombination` segment_dates=["2025-06-01", "2025-06-15"], segments=[Paris→Tokyo, Tokyo→NYC] | URL contient `flight_type=3`, `multi_city_json=[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-06-01"},{"departure_id":"NRT","arrival_id":"JFK","date":"2025-06-15"}]`, `hl=fr`, `curr=EUR` | Vérifie format URL Google Flights Story 4 ref |
| 22 | `test_search_flights_logging_structured` | Logging structuré toutes étapes orchestration | `SearchRequest` nominal | Logs contiennent combinations_generated, crawls_success, crawls_failed, parsing_success, top_price_min, top_price_max | Vérifie observabilité complète |
| 23 | `test_search_flights_search_stats_accurate` | search_stats cohérentes avec résultats | Mock 38 combinaisons réussies sur 42 | `search_stats.total_results=10` (top 10), `segments_count=len(request.segments)` | Vérifie métadonnées SearchResponse |
| 24 | `test_search_flights_less_than_10_results` | Retourne <10 résultats si <10 combinaisons réussies | Mock 5 combinaisons crawlées avec succès | `SearchResponse.results` length=5 (tous résultats disponibles) | Vérifie edge case <10 résultats |

**Total tests unitaires** : 10 (CombinationGenerator) + 14 (SearchService) = **24 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_two_segments_success` | Mock AsyncWebCrawler avec HTML Google Flights valide (10 vols par combinaison), 2 segments × [7j, 6j] = 42 combinaisons | Appeler `search_service.search_flights(SearchRequest)` avec Paris→Tokyo, Tokyo→NYC | `SearchResponse` avec 10 résultats (top 10 parmi 42), triés prix croissant, tous Flight validés Pydantic, pas d'exception |
| 2 | `test_integration_search_five_segments_asymmetric` | Mock AsyncWebCrawler HTML valide, 5 segments × [15, 2, 2, 2, 2] jours = 240 combinaisons | Appeler `search_service.search_flights(SearchRequest)` avec 5 segments | `SearchResponse` avec top 10 résultats (sur 240 combinaisons générées), prix min dans top 1, logs INFO count 240 combinaisons |
| 3 | `test_integration_search_with_captcha_partial_failures` | Mock AsyncWebCrawler : 60% combinaisons HTML valide, 40% CaptchaDetectedError, 2 segments × [10j, 8j] = 80 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~10 résultats (crawls réussis), logs WARNING captcha détecté pour 32 combinaisons échouées |
| 4 | `test_integration_search_dates_ranking` | Mock AsyncWebCrawler HTML valide avec prix variés par date combinaison, 2 segments × [7j, 6j] = 42 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` top 10 triés prix croissant, combinaisons dates différentes présentes, meilleures dates identifiées dans top 1 |
| 5 | `test_integration_end_to_end_search_endpoint` | Application FastAPI running avec TestClient, mock CrawlerService/FlightParser injectés | POST `/api/v1/search-flights` avec body JSON 3 segments × [5j, 4j, 3j] = 60 combinaisons | Status 200 + JSON response conforme SearchResponse schema avec top 10 results triés prix, search_stats.total_results=10, execution_time_seconds <10s |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 24 unitaires + 5 intégration = **29 tests**

---

## Exemples JSON

**Exemple 1 : SearchRequest multi-city (2 segments)**

```json
{
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
}
```

**Combinaisons générées** : 7 dates × 6 dates = 42 combinaisons totales

---

**Exemple 2 : DateCombination générée**

```json
{
  "segment_dates": ["2025-06-01", "2025-06-15"]
}
```

**Correspondance** : segment 1 Paris→Tokyo départ 01 juin, segment 2 Tokyo→NYC départ 15 juin

---

**Exemple 3 : CombinationResult (intermédiaire)**

```json
{
  "date_combination": {
    "segment_dates": ["2025-06-01", "2025-06-15"]
  },
  "best_flight": {
    "price": 1250.0,
    "airline": "Air France",
    "departure_time": "2025-06-01T10:30:00Z",
    "arrival_time": "2025-06-02T06:45:00Z",
    "duration": "10h 15min",
    "stops": 0,
    "departure_airport": "CDG",
    "arrival_airport": "NRT"
  }
}
```

---

**Exemple 4 : SearchResponse Top 10 (succès)**

```json
{
  "results": [
    {
      "price": 1250.0,
      "airline": "Mixed",
      "departure_date": "2025-06-01",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-01"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-15"}
      ]
    },
    {
      "price": 1300.0,
      "airline": "Mixed",
      "departure_date": "2025-06-03",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-03"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-17"}
      ]
    },
    {
      "price": 1450.0,
      "airline": "Mixed",
      "departure_date": "2025-06-05",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-05"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-20"}
      ]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 45230,
    "segments_count": 2
  }
}
```

**Note** : Array `results` contient top 10 (ici seulement 3 montrés pour lisibilité). En production : exactement 10 FlightResult sauf si <10 combinaisons réussies.

---

**Exemple 5 : SearchResponse échec partiel (crawl errors)**

```json
{
  "results": [
    {
      "price": 1250.0,
      "airline": "Mixed",
      "departure_date": "2025-06-01",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-01"},
        {"from": "Tokyo", "to": "New York", "date": "2025-06-15"}
      ]
    }
  ],
  "search_stats": {
    "total_results": 1,
    "search_time_ms": 38500,
    "segments_count": 2
  }
}
```

**Context** : Sur 42 combinaisons (2 segments × [7j, 6j]), seulement 1 crawl réussi (41 captchas détectés). Response retourne 1 résultat disponible.

---

**Exemple 6 : SearchStats avec métriques avancées**

```json
{
  "total_results": 10,
  "search_time_ms": 52400,
  "segments_count": 2,
  "combinations_generated": 42,
  "crawls_success": 38,
  "crawls_failed": 4,
  "parsing_errors": 2,
  "top_price_min": 1250.0,
  "top_price_max": 2100.0
}
```

**Note** : Métriques étendues pour observabilité (optionnel MVP, utile monitoring).

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Génération combinaisons exhaustive** : CombinationGenerator génère exactement N₁ × N₂ × ... × Nₖ combinaisons pour k segments avec Nᵢ jours par segment (vérifié : [7, 6]=42, [7, 6, 5]=210, [15, 2, 2, 2, 2]=240)

2. **Produit cartésien dates correct** : Toutes combinaisons dates testent chaque date segment 1 avec chaque date segment 2, etc. (vérifié : 42 combinaisons [7j, 6j] contiennent 7 dates segment 1 × 6 dates segment 2)

3. **Orchestration complète SearchService** : search_flights() appelle séquentiellement CombinationGenerator → CrawlerService (N fois) → FlightParser (N fois) → Ranking sans exception bloquante

4. **Crawling parallèle efficace** : SearchService utilise asyncio.gather() pour crawler multiples URLs simultanément (limite concurrence 5-10 requêtes max, vérifié logs async tasks)

5. **Top 10 ranking prix dominant** : Top 1 résultat SearchResponse contient toujours prix total minimum réel parmi toutes combinaisons testées (vérifié assertion top1.price ≤ all_other_prices)

6. **Tri prix croissant garanti** : results[0].price ≤ results[1].price ≤ ... ≤ results[9].price (vérifié boucle assertion)

7. **Gestion erreurs crawl partielles** : Si 30% combinaisons échouent (captcha/timeout) → SearchService retourne top résultats disponibles avec logs WARNING (pas d'exception levée)

8. **Construction URLs Google Flights multi-city** : URLs générées contiennent `flight_type=3`, `multi_city_json` URL-encodé avec segments + dates spécifiques combinaison, `hl=fr&curr=EUR` (vérifié regex matching)

9. **Dates combinaisons cohérentes** : Chaque DateCombination.segment_dates[i] appartient à segments[i].date_range (vérifié : date entre start et end inclusif)

## Critères techniques

10. **Type hints PEP 695** : CombinationGenerator, SearchService, DateCombination, CombinationResult annotés avec type hints modernes (`list[DateCombination]`, `async def`, `str | None`)

11. **Async/Await cohérent** : SearchService.search_flights async, utilise `await crawler_service.crawl_google_flights()`, `await asyncio.gather()` pour parallélisation

12. **Dependency Injection services** : SearchService reçoit CombinationGenerator, CrawlerService, FlightParser via constructeur (testable, mockable)

13. **Pydantic v2 modèles** : DateCombination et CombinationResult héritent BaseModel avec `ConfigDict(extra="forbid")`, CombinationResult simplifié avec `best_flight: GoogleFlightDTO`

14. **Réutilisation Story 3 modèles** : SearchRequest, FlightSegment, SearchResponse, FlightResult référencés sans redéfinition (imports depuis `app/models/request.py`, `response.py`)

15. **Réutilisation Story 4 services** : CrawlerService et FlightParser utilisés tels quels avec leurs interfaces définies Story 4 (crawl_google_flights, parse methods)

16. **Logging structuré JSON complet** : Tous logs incluent contexte métier : combinations_generated, crawls_success, crawls_failed, parsing_success, top_price_min, top_price_max, execution_time

17. **itertools.product usage** : CombinationGenerator utilise `itertools.product(*all_dates)` pour produit cartésien (pas de nested loops manuels)

18. **Mapping FlightSegment → multi_city_json** : Transformation correcte from_city → departure_id, to_city → arrival_id, date_combination.segment_dates[i] → date (vérifié format JSON Google Flights)

## Critères qualité

19. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de CombinationGenerator et SearchService (pytest-cov)

20. **29 tests passent** : 24 tests unitaires (10 CombinationGenerator + 14 SearchService) + 5 tests intégration tous verts (pytest -v)

21. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

22. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

23. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks CrawlerService/FlightParser configurés

24. **Docstrings 1 ligne** : CombinationGenerator et SearchService avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

25. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON, formules ranking (pas d'implémentation complète de méthodes)

26. **Commits conventional** : Story 6 committée avec message `feat(services): add multi-city search and top 10 ranking` conforme Conventional Commits

---

**Note importante** : Story moyenne complexité (5 story points) → 26 critères couvrent exhaustivement orchestration multi-city (9 fonctionnels), architecture services modulaires (10 techniques), qualité tests TDD (7 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (top 10 triés prix, produit cartésien dates), **M**esurable (29 tests passent, coverage ≥80%), **A**tteignable (réutilisation Story 3, 4, 5), **R**elevant (foundation scalable multi-city), **T**emporel (MVP Phase 5, avant intégration API complète Phase 6).
