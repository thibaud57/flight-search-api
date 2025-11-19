---
title: "Story 5: Multi-destinations (CombinationGenerator)"
epic: "Epic 2: Google Flights Scraping"
story_points: 5
dependencies: ["story-4"]
date: "2025-19-11"
keywords: ["multi-destinations", "combination-generator", "multi-city", "permutations", "itertools", "asyncio-gather", "parallel-crawls", "orchestration", "ranking", "top-10"]
scope: ["specs"]
technologies: ["Python", "itertools", "asyncio", "FastAPI", "Pydantic v2"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Utilisateurs business** : Trouver la meilleure combinaison de vols multi-destinations parmi toutes les permutations possibles de destinations (ex: Paris→Tokyo→NYC vs Paris→NYC→Tokyo)
- **Optimisation budgets voyage** : Comparer automatiquement toutes les routes possibles et identifier le top 10 des options les plus économiques
- **Gain temps recherche** : Éviter recherches manuelles multiples sur Google Flights (N! permutations pour N destinations = 6 recherches pour 3 destinations, 24 pour 4, 120 pour 5)
- **Flexibilité plages dates** : Explorer plusieurs dates de départ dans une plage donnée (date_range.start à date_range.end) pour trouver les meilleurs prix

## Contraintes métier

- **MVP limité 2-10 destinations** : Focus MVP sur 2-5 destinations (contrainte SearchRequest.destinations max 5), extensible jusqu'à 10 destinations en post-MVP
- **Explosion combinatoire** : N! permutations destinations × D dates possibles = volume requêtes important (ex: 5 destinations × 15 jours = 120 × 15 = 1800 URLs Google Flights potentielles)
- **Coûts bandwidth Decodo** : Chaque crawl = ~200-500KB HTML téléchargé via proxies résidentiels ($2.60-3.50/GB), nécessite optimisation nombre de crawls
- **Rate limiting Google Flights** : Requêtes massives simultanées peuvent déclencher rate limiting (status 429) ou captchas, nécessite throttling intelligent
- **Timeout total acceptable** : Recherche multi-destinations doit compléter en <60 secondes au p95 (user experience web), même avec retry logic

## Valeur business

- **Économies utilisateur quantifiables** : Algorithme ranking trouve différences prix jusqu'à 30-40% entre meilleure et pire combinaison (économies moyennes 200-400€ par recherche)
- **Foundation orchestration scalable** : CombinationGenerator + SearchService établissent patterns réutilisables pour futures optimisations (caching, parallélisation avancée, webhooks)
- **Différenciation compétitive** : Fonctionnalité multi-destinations avec ranking automatique absente des outils grand public (Kayak, Skyscanner limités à 2-3 étapes sans ranking)
- **Métriques observables actionables** : Logging structuré fournit insights sur combinaisons populaires, taux succès crawl par route, patterns prix pour amélioration continue

## Métriques succès

- **Génération combinaisons correcte** : 100% des permutations destinations générées (2! = 2 pour 2 destinations, 5! = 120 pour 5 destinations)
- **Taux succès crawl global** : ≥85% des URLs crawlées avec succès (HTML valide sans captcha), même avec retry logic inclus
- **Précision ranking Top 10** : Top 1 résultat toujours prix minimum réel sur ensemble combinaisons testées (validation manuelle échantillon)
- **Temps exécution total** : <60 secondes au p95 pour recherche 3 destinations × 7 jours (21 combinaisons × crawl + parsing + ranking)
- **Coverage tests** : ≥80% sur CombinationGenerator et SearchService (unitaires + intégration)
- **Qualité extraction vols** : ≥95% des combinaisons retournent ≥5 vols parsés par route (dépend FlightParser Story 4)

---

# 📋 Spécifications Techniques

## 1. CombinationGenerator

**Rôle** : Générer toutes les permutations multi-city possibles depuis une liste de destinations et une plage de dates, en utilisant itertools.product pour combinaisons cartésiennes dates × permutations.

**Interface** :
```python
class CombinationGenerator:
    """Générateur de combinaisons multi-destinations."""

    def generate_combinations(
        self,
        destinations: list[str],
        date_range: DateRange
    ) -> list[Combination]:
        """
        Génère toutes les permutations destinations × dates possibles.

        Returns:
            Liste de Combination avec permutations destinations et dates distribuées
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `destinations` | `list[str]` | Liste destinations (ex: ["Paris", "Tokyo", "NYC"]) | min_length=2, max_length=5 (MVP) |
| `date_range` | `DateRange` | Plage dates voyage (start/end format YYYY-MM-DD) | Modèle DateRange Story 3, end > start |
| **Retour** | `list[Combination]` | Liste combinaisons (permutations × dates) | Length = permutations(destinations) × days_range |

**Modèle Combination** :
```python
class Combination(BaseModel):
    """Représente une combinaison route + date de départ."""

    route: list[str]
    departure_date: str
```

| Champ Combination | Type | Description | Contraintes |
|-------------------|------|-------------|-------------|
| `route` | `list[str]` | Permutation destinations (ex: ["Paris", "Tokyo", "NYC"]) | Même length que destinations input |
| `departure_date` | `str` | Date départ premier vol (format YYYY-MM-DD) | Doit être dans date_range [start, end] |

**Comportement** :

- **Génération nominale** :
  1. Calculer toutes permutations destinations avec `itertools.permutations(destinations)`
  2. Calculer toutes dates dans plage avec range `date_range.start` à `date_range.end` (inclusif)
  3. Générer produit cartésien permutations × dates avec `itertools.product()`
  4. Retourner liste de Combination avec chaque (route, departure_date)

- **Algorithme permutations** :
  - 2 destinations → 2! = 2 permutations (ex: [Paris, Tokyo], [Tokyo, Paris])
  - 3 destinations → 3! = 6 permutations
  - 4 destinations → 4! = 24 permutations
  - 5 destinations → 5! = 120 permutations

- **Distribution dates** :
  - date_range = "2025-06-01" à "2025-06-15" → 15 dates possibles
  - Chaque permutation testée avec chaque date (ex: 6 permutations × 15 dates = 90 combinaisons totales)

- **Edge cases** :
  - **1 destination unique** : 1! = 1 permutation (route = [destination]), multiplié par nombre dates
  - **5 destinations max MVP** : 120 permutations × dates (ex: 120 × 7 jours = 840 combinaisons)
  - **date_range même jour** : 1 date unique (start = end après validation DateRange)
  - **Liste vide destinations** : Ne doit jamais arriver (validation SearchRequest en amont rejette)

- **Optimisations futures** :
  - Post-MVP : Filtrer permutations symétriques si aller-retour même point départ/arrivée
  - Post-MVP : Limiter dates testées à jours spécifiques (ex: vendredis uniquement)

**Erreurs levées** :
- Aucune exception levée (validation données effectuée en amont par SearchRequest)

**Logging structuré** :
- INFO : Nombre permutations destinations générées, nombre dates dans plage, total combinaisons créées
- DEBUG : Première et dernière combinaison générée (sample pour vérification)

---

## 2. SearchService (Orchestration Multi-Destinations)

**Rôle** : Orchestrer la recherche multi-destinations complète : génération combinaisons, crawling parallèle de toutes les URLs Google Flights, parsing vols, ranking Top 10 résultats par prix croissant.

**Interface** :
```python
class SearchService:
    """Service orchestration recherche vols multi-destinations."""

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
        Orchestre recherche complète multi-destinations avec ranking Top 10.

        Returns:
            SearchResponse avec top 10 résultats triés par prix total croissant
        """
```

**Dépendances Services** :

| Service | Rôle | Défini dans |
|---------|------|-------------|
| `CombinationGenerator` | Génère permutations destinations × dates | Story 5 (ce document) |
| `CrawlerService` | Crawle Google Flights avec retry logic et proxy rotation | Story 4 |
| `FlightParser` | Parse HTML Google Flights en liste Flight | Story 4 |

**Comportement Orchestration** :

**Étape 1 : Génération Combinaisons**
1. Appeler `combination_generator.generate_combinations(request.destinations, request.date_range)`
2. Recevoir liste de Combination (ex: 90 combinaisons pour 3 destinations × 15 jours)
3. Logger INFO : nombre total combinaisons à crawler

**Étape 2 : Construction URLs Google Flights**
Pour chaque Combination :
1. Construire URL multi-city Google Flights avec paramètre `multi_city_json`
2. Format JSON segments : `[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-06-01"}, ...]`
3. URL-encoder JSON et ajouter paramètres localisation `hl=fr&curr=EUR`
4. Exemple URL : `https://www.google.com/travel/flights?flight_type=3&multi_city_json=[...]&hl=fr&curr=EUR`

**Étape 3 : Crawling Parallèle**
1. Appeler `crawler_service.crawl_google_flights(url)` pour chaque combinaison
2. Stratégie parallélisation : `asyncio.gather()` avec limite concurrence (ex: 5-10 requêtes simultanées max pour éviter rate limiting)
3. Retry automatique via Tenacity (déjà intégré dans CrawlerService Story 4)
4. Gérer erreurs crawl partielles : Si captcha/timeout → Logger WARNING, continuer autres combinaisons
5. Logger INFO : Nombre crawls réussis vs échecs

**Étape 4 : Parsing Vols**
Pour chaque HTML crawlé avec succès :
1. Appeler `flight_parser.parse(html)` (retourne `list[Flight]`)
2. Agréger vols par combinaison : `CombinationResult(combination=combo, flights=parsed_flights)`
3. Gérer erreurs parsing : Si ParsingError → Logger WARNING, skip combinaison
4. Logger INFO : Nombre combinaisons parsées avec succès

**Étape 5 : Ranking Top 10**
1. Calculer prix total pour chaque CombinationResult : `sum(flight.price for flight in flights)`
2. Trier CombinationResult par prix total croissant
3. Sélectionner top 10 résultats (ou moins si <10 combinaisons réussies)
4. Logger INFO : Prix min/max trouvés, top 1 combinaison

**Étape 6 : Construction SearchResponse**
1. Transformer top 10 CombinationResult en FlightResult (format SearchResponse Story 3)
2. Calculer SearchStats : total_results, search_time_ms, destinations_searched
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
- INFO : Début search avec destinations, date_range
- INFO : Combinaisons générées (count), URLs construites
- INFO : Crawls terminés (succès/échecs), parsing terminé (count vols)
- INFO : Top 10 sélectionné avec prix min/max
- ERROR : Taux échec crawl >50%

---

## 3. Top 10 Ranking (Algorithme)

**Rôle** : Sélectionner et trier les 10 meilleures combinaisons de vols selon critères pondérés (prix principal, durée, escales).

**Critères de Ranking** :

| Critère | Poids | Description | Calcul |
|---------|-------|-------------|--------|
| **Prix total** | 70% | Somme prix tous vols de la combinaison | `sum(flight.price for flight in flights)` |
| **Durée totale** | 20% | Somme durées tous vols (en minutes) | `sum(parse_duration(flight.duration) for flight in flights)` |
| **Nombre escales** | 10% | Somme escales tous vols | `sum(flight.stops or 0 for flight in flights)` |

**Formule Pondération** :

Score final (plus bas = meilleur) :
```
score = (prix_total * 0.7) + (durée_totale_minutes * 0.002) + (nombre_escales * 50)
```

**Justification pondération** :
- Prix dominant (70%) car critère principal utilisateurs
- Durée secondaire (20%) pour confort voyage
- Escales tertiaire (10%) pour fluidité itinéraire

**Algorithme Sélection Top 10** :

1. **Calculer score** pour chaque CombinationResult
2. **Trier** par score croissant (meilleur score = score le plus bas)
3. **Sélectionner** top 10 résultats
4. **Départager ex-aequo** :
   - Si 2+ combinaisons même score → trier par prix total croissant
   - Si même prix → trier par durée totale croissante
   - Si même durée → trier par nombre escales croissant

**Exemple Concret Ranking** :

**Input (3 combinaisons)** :

| # | Route | Prix Total | Durée Total | Escales | Score |
|---|-------|-----------|-------------|---------|-------|
| 1 | Paris→Tokyo→NYC | 1250€ | 18h 30min (1110 min) | 1 | 875 + 2.22 + 50 = **927.22** |
| 2 | Paris→NYC→Tokyo | 1800€ | 15h 00min (900 min) | 0 | 1260 + 1.80 + 0 = **1261.80** |
| 3 | Tokyo→Paris→NYC | 1300€ | 20h 15min (1215 min) | 2 | 910 + 2.43 + 100 = **1012.43** |

**Output Top 10 (trié)** :

1. Paris→Tokyo→NYC (score 927.22, 1250€)
2. Tokyo→Paris→NYC (score 1012.43, 1300€)
3. Paris→NYC→Tokyo (score 1261.80, 1800€)

**Edge cases** :
- **<10 combinaisons totales** : Retourner toutes les combinaisons disponibles (ex: 5 combinaisons → top 5)
- **Toutes combinaisons même prix** : Départager par durée puis escales
- **Vols avec champs manquants** : Si flight.duration ou flight.stops manquants → utiliser valeurs par défaut (duration=0, stops=0) et logger WARNING

---

## 4. Modèles Pydantic

### SearchRequest (Référence Story 3)

**Défini dans** : `docs/specs/epic-1-api-foundation/story-3-search-endpoint.md`

**Champs réutilisés** :
- `destinations: list[str]` (min_length=1, max_length=5)
- `date_range: DateRange` (start/end YYYY-MM-DD)

**Validations réutilisées** :
- `field_validator('destinations')` : 1 ≤ len ≤ 5, chaque ville min 2 caractères
- `model_validator` sur DateRange : end > start, start ≥ today

---

### CombinationResult (Nouveau Modèle Story 5)

**Rôle** : Modèle intermédiaire pour stocker résultat crawl + parsing d'une combinaison avant ranking.

**Interface** :
```python
class CombinationResult(BaseModel):
    """Résultat intermédiaire pour une combinaison route + date."""

    combination: Combination
    flights: list[Flight]
    total_price: float
    total_duration_minutes: int
    total_stops: int
```

**Champs** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `combination` | `Combination` | Combinaison testée (route + date) | Modèle nested Combination |
| `flights` | `list[Flight]` | Vols extraits par FlightParser | min_length=1 (au moins 1 vol) |
| `total_price` | `float` | Somme prix tous vols | ≥ 0.0, calculé automatiquement |
| `total_duration_minutes` | `int` | Somme durées en minutes | ≥ 0, calculé automatiquement |
| `total_stops` | `int` | Somme escales tous vols | ≥ 0, calculé automatiquement |

**Validations Pydantic** :

- `model_validator(mode='after')` : Calculer automatiquement `total_price`, `total_duration_minutes`, `total_stops` depuis liste flights
- `field_validator('flights', mode='after')` : Vérifier min_length ≥ 1 (au moins 1 vol extrait)
- `field_validator('total_price', mode='after')` : Vérifier ≥ 0.0

**Comportement** :
- Modèle calculé automatiquement par SearchService après parsing
- Utilisé pour ranking avant transformation en FlightResult final (format SearchResponse)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CombinationGenerator (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_generate_combinations_two_destinations` | Génère 2 permutations pour 2 destinations | `destinations=["Paris", "Tokyo"]`, `date_range={"start": "2025-06-01", "end": "2025-06-01"}` | 2 combinaisons : [Paris→Tokyo], [Tokyo→Paris] avec même date | Vérifie calcul 2! = 2 permutations |
| 2 | `test_generate_combinations_three_destinations` | Génère 6 permutations pour 3 destinations | `destinations=["Paris", "Tokyo", "NYC"]`, `date_range` 1 jour | 6 combinaisons (3! permutations) | Vérifie algorithme permutations complet |
| 3 | `test_generate_combinations_five_destinations_max` | Génère 120 permutations pour 5 destinations (max MVP) | `destinations` 5 villes, `date_range` 1 jour | 120 combinaisons (5! = 120) | Vérifie edge case max destinations MVP |
| 4 | `test_generate_combinations_single_destination` | Génère 1 combinaison pour 1 destination | `destinations=["Paris"]`, `date_range` 1 jour | 1 combinaison [Paris] | Vérifie edge case minimum destinations |
| 5 | `test_generate_combinations_multiple_dates` | Multiplie permutations par nombre dates | `destinations=["Paris", "Tokyo"]`, `date_range` 7 jours | 2 permutations × 7 dates = 14 combinaisons | Vérifie produit cartésien permutations × dates |
| 6 | `test_generate_combinations_date_range_15_days` | Plage dates 15 jours génère 15 dates | `destinations` 2 villes, `date_range` "2025-06-01" à "2025-06-15" | 2 permutations × 15 dates = 30 combinaisons | Vérifie calcul dates inclusif (start et end inclus) |
| 7 | `test_combination_model_valid_fields` | Modèle Combination valide avec tous champs | `route=["Paris", "Tokyo"]`, `departure_date="2025-06-01"` | Combination instance créée sans erreur | Vérifie validation Pydantic Combination |
| 8 | `test_combinations_unique_routes` | Toutes permutations sont uniques | `destinations=["Paris", "Tokyo", "NYC"]` | 6 combinaisons avec 6 routes distinctes | Vérifie absence doublons dans permutations |
| 9 | `test_combinations_dates_ordered` | Dates générées dans ordre chronologique | `date_range` "2025-06-01" à "2025-06-07" | Combinaisons avec dates triées 01, 02, ..., 07 | Vérifie ordre dates respecté |
| 10 | `test_generate_combinations_logging` | Logging INFO avec statistiques génération | `destinations` 3 villes, `date_range` 5 jours | Logs contiennent permutations_count=6, dates_count=5, total_combinations=30 | Vérifie logging structuré observabilité |

### SearchService (15 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 11 | `test_search_flights_orchestration_success` | Orchestration complète avec tous crawls réussis | `SearchRequest` 2 destinations × 3 dates, mock CrawlerService/FlightParser succès | `SearchResponse` avec top 10 résultats triés prix croissant | Vérifie flow nominal complet |
| 12 | `test_search_flights_calls_combination_generator` | SearchService appelle CombinationGenerator | `SearchRequest` avec destinations valides | `combination_generator.generate_combinations()` appelé 1 fois avec destinations + date_range | Vérifie intégration CombinationGenerator |
| 13 | `test_search_flights_crawls_all_urls` | Crawle toutes URLs générées | Mock 6 combinaisons générées | `crawler_service.crawl_google_flights()` appelé 6 fois (1 par combinaison) | Vérifie crawl exhaustif toutes combinaisons |
| 14 | `test_search_flights_parallel_crawling_asyncio_gather` | Crawling parallèle avec asyncio.gather | Mock 10 combinaisons | asyncio.gather utilisé avec liste 10 tasks async | Vérifie parallélisation async |
| 15 | `test_search_flights_parses_all_html` | Parse HTML de tous crawls réussis | Mock 5 HTML valides crawlés | `flight_parser.parse()` appelé 5 fois avec chaque HTML | Vérifie parsing systématique après crawl |
| 16 | `test_search_flights_ranking_top_10` | Sélectionne top 10 résultats par prix | Mock 20 combinaisons avec prix variés 800-2000€ | `SearchResponse.results` length=10, trié prix croissant (results[0].price < results[9].price) | Vérifie algorithme ranking prix |
| 17 | `test_search_flights_ranking_price_primary` | Prix total est critère dominant ranking | Mock 3 combinaisons : 1000€ (lent), 1200€ (rapide), 900€ (moyen) | Top 1 = 900€ (prix min), top 2 = 1000€, top 3 = 1200€ | Vérifie pondération prix 70% |
| 18 | `test_search_flights_ranking_tie_breaker_duration` | Départage ex-aequo prix par durée | Mock 2 combinaisons même prix 1000€ : durée 10h vs 15h | Top 1 = combinaison 10h (durée min) | Vérifie tie-breaker durée |
| 19 | `test_search_flights_handles_partial_crawl_failures` | Gestion erreurs crawl partielles (50% échecs) | Mock 10 combinaisons : 5 crawls succès, 5 CaptchaDetectedError | `SearchResponse` avec 5 résultats (crawls réussis), logs WARNING pour 5 échecs | Vérifie résilience erreurs partielles |
| 20 | `test_search_flights_returns_empty_all_crawls_failed` | Retourne response vide si tous crawls échouent | Mock 5 combinaisons : toutes lèvent NetworkError | `SearchResponse.results=[]`, `search_stats.total_results=0`, logs ERROR | Vérifie edge case échec total |
| 21 | `test_search_flights_retry_logic_integrated` | Retry automatique via CrawlerService Tenacity | Mock CrawlerService avec retry_count trackable | CrawlerService retry logic déclenché (vérifié via mock spy) | Vérifie intégration retry Story 4 |
| 22 | `test_search_flights_constructs_google_flights_urls` | Construction URLs multi-city correctes | `Combination` route ["Paris", "Tokyo"], date "2025-06-01" | URL contient `flight_type=3`, `multi_city_json=[...]`, `hl=fr`, `curr=EUR` | Vérifie format URL Google Flights Story 4 ref |
| 23 | `test_search_flights_logging_structured` | Logging structuré toutes étapes orchestration | `SearchRequest` nominal | Logs contiennent combinations_generated, crawls_success, crawls_failed, parsing_success, top_price_min, top_price_max | Vérifie observabilité complète |
| 24 | `test_search_flights_search_stats_accurate` | search_stats cohérentes avec résultats | Mock 8 combinaisons réussies sur 10 | `search_stats.total_results=8`, `destinations_searched=request.destinations` | Vérifie métadonnées SearchResponse |
| 25 | `test_search_flights_less_than_10_results` | Retourne <10 résultats si <10 combinaisons réussies | Mock 3 combinaisons crawlées avec succès | `SearchResponse.results` length=3 (tous résultats disponibles) | Vérifie edge case <10 résultats |

**Total tests unitaires** : 10 (CombinationGenerator) + 15 (SearchService) = **25 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_two_destinations_success` | Mock AsyncWebCrawler avec HTML Google Flights valide (10 vols par combinaison), 2 destinations × 1 date = 2 combinaisons | Appeler `search_service.search_flights(SearchRequest)` avec Paris/Tokyo | `SearchResponse` avec 2 résultats (1 par combinaison), triés prix croissant, tous Flight validés Pydantic, pas d'exception |
| 2 | `test_integration_search_five_destinations_max` | Mock AsyncWebCrawler HTML valide, 5 destinations × 1 date = 120 combinaisons | Appeler `search_service.search_flights(SearchRequest)` avec 5 destinations | `SearchResponse` avec top 10 résultats (sur 120 combinaisons générées), prix min dans top 1, logs INFO count 120 combinaisons |
| 3 | `test_integration_search_with_captcha_partial_failures` | Mock AsyncWebCrawler : 60% combinaisons HTML valide, 40% CaptchaDetectedError, 3 destinations × 5 dates = 18 combinaisons | Appeler `search_service.search_flights(SearchRequest)` | `SearchResponse` avec ~10 résultats (crawls réussis), logs WARNING captcha détecté pour 7 combinaisons, retry logic CrawlerService utilisé |
| 4 | `test_integration_search_multi_dates_ranking` | Mock AsyncWebCrawler HTML valide avec prix variés, 2 destinations × 7 dates = 14 combinaisons | Appeler `search_service.search_flights(SearchRequest)` date_range 7 jours | `SearchResponse` top 10 triés prix croissant, combinaisons avec dates différentes présentes, meilleure date identifiée dans top 1 |
| 5 | `test_integration_end_to_end_search_endpoint` | Application FastAPI running avec TestClient, mock CrawlerService/FlightParser injectés | POST `/api/v1/search-flights` avec body JSON 3 destinations × 3 dates | Status 200 + JSON response conforme SearchResponse schema avec top 10 results triés prix, search_stats.total_results=9, execution_time_seconds <10s |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 25 unitaires + 5 intégration = **30 tests**

---

## Exemples JSON

**Exemple 1 : SearchRequest multi-destinations (3 destinations)**

```json
{
  "destinations": ["Paris", "Tokyo", "New York"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-07"
  }
}
```

**Combinaisons générées** : 3! × 7 dates = 6 × 7 = 42 combinaisons totales

---

**Exemple 2 : Combination générée**

```json
{
  "route": ["Paris", "Tokyo", "New York"],
  "departure_date": "2025-06-01"
}
```

---

**Exemple 3 : CombinationResult (intermédiaire)**

```json
{
  "combination": {
    "route": ["Paris", "Tokyo", "New York"],
    "departure_date": "2025-06-01"
  },
  "flights": [
    {
      "price": 650.0,
      "airline": "Air France",
      "departure_time": "2025-06-01T10:30:00Z",
      "arrival_time": "2025-06-02T06:45:00Z",
      "duration": "10h 15min",
      "stops": 0,
      "departure_airport": "CDG",
      "arrival_airport": "NRT"
    },
    {
      "price": 600.0,
      "airline": "United Airlines",
      "departure_time": "2025-06-03T14:00:00Z",
      "arrival_time": "2025-06-03T18:30:00Z",
      "duration": "13h 30min",
      "stops": 1,
      "departure_airport": "NRT",
      "arrival_airport": "JFK"
    }
  ],
  "total_price": 1250.0,
  "total_duration_minutes": 1425,
  "total_stops": 1
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
      "route": ["Paris", "Tokyo", "New York"]
    },
    {
      "price": 1300.0,
      "airline": "Mixed",
      "departure_date": "2025-06-03",
      "route": ["Tokyo", "Paris", "New York"]
    },
    {
      "price": 1450.0,
      "airline": "Mixed",
      "departure_date": "2025-06-05",
      "route": ["Paris", "New York", "Tokyo"]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 45230,
    "destinations_searched": ["Paris", "Tokyo", "New York"]
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
      "route": ["Paris", "Tokyo"]
    }
  ],
  "search_stats": {
    "total_results": 1,
    "search_time_ms": 38500,
    "destinations_searched": ["Paris", "Tokyo"]
  }
}
```

**Context** : Sur 14 combinaisons (2 destinations × 7 dates), seulement 1 crawl réussi (13 captchas détectés). Response retourne 1 résultat disponible.

---

**Exemple 6 : SearchStats avec métriques avancées**

```json
{
  "total_results": 10,
  "search_time_ms": 52400,
  "destinations_searched": ["Paris", "Tokyo", "New York"],
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

1. **Génération combinaisons exhaustive** : CombinationGenerator génère exactement N! permutations pour N destinations (vérifié : 2!=2, 3!=6, 5!=120)

2. **Produit cartésien dates correct** : Chaque permutation destinations testée avec chaque date dans date_range (vérifié : 3 destinations × 7 jours = 42 combinaisons)

3. **Orchestration complète SearchService** : search_flights() appelle séquentiellement CombinationGenerator → CrawlerService (N fois) → FlightParser (N fois) → Ranking sans exception bloquante

4. **Crawling parallèle efficace** : SearchService utilise asyncio.gather() pour crawler multiples URLs simultanément (limite concurrence 5-10 requêtes max, vérifié logs async tasks)

5. **Top 10 ranking prix dominant** : Top 1 résultat SearchResponse contient toujours prix total minimum réel parmi toutes combinaisons testées (vérifié assertion top1.price ≤ all_other_prices)

6. **Tri prix croissant garanti** : results[0].price ≤ results[1].price ≤ ... ≤ results[9].price (vérifié boucle assertion)

7. **Gestion erreurs crawl partielles** : Si 30% combinaisons échouent (captcha/timeout) → SearchService retourne top résultats disponibles avec logs WARNING (pas d'exception levée)

8. **Construction URLs Google Flights multi-city** : URLs générées contiennent `flight_type=3`, `multi_city_json` URL-encodé avec segments route, `hl=fr&curr=EUR` (vérifié regex matching)

## Critères techniques

9. **Type hints PEP 695** : CombinationGenerator, SearchService, Combination, CombinationResult annotés avec type hints modernes (`list[Combination]`, `async def`, `str | None`)

10. **Async/Await cohérent** : SearchService.search_flights async, utilise `await crawler_service.crawl_google_flights()`, `await asyncio.gather()` pour parallélisation

11. **Dependency Injection services** : SearchService reçoit CombinationGenerator, CrawlerService, FlightParser via constructeur (testable, mockable)

12. **Pydantic v2 modèles** : Combination et CombinationResult héritent BaseModel avec Field validation, model_validator pour calculs automatiques (total_price, total_duration_minutes)

13. **Réutilisation Story 3 modèles** : SearchRequest, DateRange, SearchResponse, FlightResult référencés sans redéfinition (imports depuis `app/models/request.py`, `response.py`)

14. **Réutilisation Story 4 services** : CrawlerService et FlightParser utilisés tels quels avec leurs interfaces définies Story 4 (crawl_google_flights, parse methods)

15. **Logging structuré JSON complet** : Tous logs incluent contexte métier : combinations_generated, crawls_success, crawls_failed, parsing_success, top_price_min, top_price_max, execution_time

16. **itertools.permutations usage** : CombinationGenerator utilise `itertools.permutations(destinations)` pour générer permutations (pas de boucles manuelles)

17. **itertools.product usage** : CombinationGenerator utilise `itertools.product(permutations, dates)` pour produit cartésien (pas de nested loops manuels)

## Critères qualité

18. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% du code de CombinationGenerator et SearchService (pytest-cov)

19. **30 tests passent** : 25 tests unitaires (10 CombinationGenerator + 15 SearchService) + 5 tests intégration tous verts (pytest -v)

20. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

21. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

22. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks CrawlerService/FlightParser configurés

23. **Docstrings 1 ligne** : CombinationGenerator et SearchService avec docstring descriptive, méthodes principales documentées, focus POURQUOI pas QUOI

24. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON, formules ranking (pas d'implémentation complète de méthodes)

25. **Commits conventional** : Story 5 committée avec message `docs(specs): add story 5 specifications` conforme Conventional Commits

---

**Note importante** : Story moyenne complexité (5 story points) → 25 critères couvrent exhaustivement orchestration multi-destinations (8 fonctionnels), architecture services modulaires (9 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (top 10 triés prix), **M**esurable (30 tests passent, coverage ≥80%), **A**tteignable (réutilisation Story 3-4), **R**elevant (foundation scalable multi-destinations), **T**emporel (MVP Phase 5, avant intégration API complète Phase 6).
