---
title: "Story 8: Filtres & Tri par Vol"
epic: "Epic 3: Production Ready"
story_points: 3
dependencies: ["epic-2/story-6"]
date: "2025-21-11"
keywords: ["filters", "sort", "max-stops", "max-duration", "flight-selection", "search-request", "search-service"]
scope: ["specs"]
technologies: ["Python", "Pydantic v2", "FastAPI", "Enum"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Voyageurs confort** : Ne voir que les vols avec max N escales (ex: max_stops=1 pour éviter les 2+ escales)
- **Voyageurs pressés** : Filtrer les vols trop longs (ex: max 18h de vol par segment)
- **Flexibilité sélection** : Choisir le critère de sélection du meilleur vol (prix, durée, escales)

## Contraintes métier

- **Filtres par vol** : Filtres appliqués sur chaque vol retourné par Google Flights (pas sur le top 10 final)
- **Filtres optionnels** : Tous les filtres sont optionnels, aucun n'est requis
- **Sélection meilleur vol** : Parmi les vols filtrés, on sélectionne le meilleur selon critère choisi
- **Top 10 inchangé** : Le ranking final des combinaisons reste trié par prix croissant

## Valeur business

- ✅ **Résultats pertinents** : Chaque combinaison retourne un vol correspondant aux critères utilisateur
- ✅ **Économie temps** : Évite de proposer des vols avec 3 escales si l'utilisateur veut max 1
- ✅ **Personnalisation** : L'utilisateur peut privilégier durée ou escales plutôt que prix pour la sélection

## Métriques succès

- **Filtres fonctionnels** : Tous les vols sélectionnés respectent les filtres actifs (100% conformité)
- **Sélection correcte** : Le vol sélectionné est le meilleur selon critère choisi parmi les filtrés
- **Rétrocompatibilité** : Requêtes sans filtres fonctionnent comme avant
- **Coverage tests** : ≥80% sur composants modifiés

---

# 📋 Spécifications Techniques

## 1. Enum SortBy

**Rôle** : Définir le critère de sélection du meilleur vol parmi les vols filtrés d'une combinaison.

**Interface** :
```python
class SortBy(str, Enum):
    """Critère de sélection du meilleur vol parmi les filtrés."""

    BEST = "best"
    PRICE = "price"
    DURATION = "duration"
    STOPS = "stops"
```

**Valeurs** :

| Valeur | Description | Comportement |
|--------|-------------|--------------|
| `BEST` | Sélection Google (défaut) | Premier vol de la liste filtrée (algo Google) |
| `PRICE` | Sélection par prix | Vol le moins cher parmi les filtrés |
| `DURATION` | Sélection par durée | Vol le plus court parmi les filtrés |
| `STOPS` | Sélection par escales | Vol avec le moins d'escales parmi les filtrés |

**Comportement** :
- `BEST` est la valeur par défaut (conserve l'algorithme de tri Google)
- Hérite de `str` pour sérialisation JSON automatique
- Utilisé dans SearchRequest comme paramètre optionnel

---

## 2. SearchRequest (Extension)

**Rôle** : Ajouter paramètres optionnels de filtrage et sélection à la requête de recherche existante.

**Nouveaux champs** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `max_stops` | `int \| None` | Nombre max escales par vol | ≥ 0 si fourni (0 = direct), None = pas de filtre |
| `max_duration_hours` | `int \| None` | Durée max par vol en heures | > 0 si fourni, None = pas de filtre |
| `sort_by` | `SortBy` | Critère sélection meilleur vol | Défaut = `SortBy.BEST` |

**Validations Pydantic** :

- `field_validator('max_stops')` : Vérifier ≥ 0 si fourni
- `field_validator('max_duration_hours')` : Vérifier > 0 si fourni

**Comportement** :
- Champs optionnels avec valeur par défaut `None` (filtres) ou `SortBy.BEST` (sélection)
- Rétrocompatible : requêtes existantes sans ces champs fonctionnent identiquement (algo Google)
- Filtres cumulatifs : si plusieurs filtres fournis, tous doivent être satisfaits (AND logique)

---

## 3. SearchService (Extension)

**Rôle** : Appliquer filtres sur les vols parsés et sélectionner le meilleur selon critère.

**Modifications méthodes** :

### Nouvelle méthode `_filter_flights`

**Interface** :
```python
def _filter_flights(
    self,
    flights: list[GoogleFlightDTO],
    request: SearchRequest,
) -> list[GoogleFlightDTO]:
    """Filtre les vols selon critères optionnels request."""
```

**Comportement** :
- Applique filtres dans l'ordre : max_stops → max_duration_hours
- Si filtre est `None`, il est ignoré (pas de filtrage sur ce critère)
- Retourne liste filtrée (peut être vide si aucun vol ne match)

**Logique filtrage** :

| Filtre | Condition exclusion |
|--------|---------------------|
| `max_stops` | `flight.stops > max_stops` (ou flight.stops is None) |
| `max_duration_hours` | `parse_duration(flight.duration) > max_duration_hours * 60` |

### Nouvelle méthode `_select_best_flight`

**Interface** :
```python
def _select_best_flight(
    self,
    flights: list[GoogleFlightDTO],
    sort_by: SortBy,
) -> GoogleFlightDTO | None:
    """Sélectionne le meilleur vol selon critère."""
```

**Comportement** :
- Trie les vols selon `sort_by` (ordre croissant)
- Retourne le premier vol (le meilleur)
- Retourne `None` si liste vide

**Logique sélection** :

| SortBy | Clé de tri |
|--------|------------|
| `BEST` | Premier élément de la liste (algo Google) |
| `PRICE` | `flight.price` |
| `DURATION` | `parse_duration(flight.duration)` |
| `STOPS` | `flight.stops or 0` |

### Modification `_parse_all_results`

**Comportement modifié** :
1. Parse HTML → `list[GoogleFlightDTO]` (inchangé)
2. **NOUVEAU** : Filtrer avec `_filter_flights(flights, request)`
3. **NOUVEAU** : Sélectionner avec `_select_best_flight(filtered, request.sort_by)`
4. Si aucun vol après filtrage → skip cette combinaison (log WARNING)
5. Créer `CombinationResult` avec le vol sélectionné

**Notes importantes** :
- `CombinationResult.best_flight` = meilleure option filtrée et sélectionnée
- `best_flight.price` = prix TOTAL de l'itinéraire (pas par segment)
- `best_flight.duration` et `best_flight.stops` = données du PREMIER SEGMENT uniquement (limitation Google Flights multi-city)
- **Limitation filtres** : `max_duration_hours` et `max_stops` filtrent sur le premier segment, pas sur le trajet complet

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### SortBy Enum (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_sortby_best_value` | Valeur enum BEST | `SortBy.BEST` | `"best"` | Vérifie valeur string correcte |
| 2 | `test_sortby_price_value` | Valeur enum PRICE | `SortBy.PRICE` | `"price"` | Vérifie valeur string correcte |
| 3 | `test_sortby_duration_value` | Valeur enum DURATION | `SortBy.DURATION` | `"duration"` | Vérifie valeur string correcte |
| 4 | `test_sortby_stops_value` | Valeur enum STOPS | `SortBy.STOPS` | `"stops"` | Vérifie valeur string correcte |

### SearchRequest Filters (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 4 | `test_request_max_stops_valid` | max_stops valide | `max_stops=2` | Request créée | Vérifie acceptation valeur positive |
| 5 | `test_request_max_stops_zero_valid` | max_stops=0 (direct) valide | `max_stops=0` | Request créée | Vérifie acceptation vols directs |
| 6 | `test_request_max_stops_negative_invalid` | max_stops négatif invalide | `max_stops=-1` | `ValidationError` | Vérifie rejet valeur négative |
| 7 | `test_request_max_duration_valid` | max_duration_hours valide | `max_duration_hours=24` | Request créée | Vérifie acceptation valeur positive |
| 8 | `test_request_max_duration_zero_invalid` | max_duration_hours=0 invalide | `max_duration_hours=0` | `ValidationError` | Vérifie rejet valeur nulle |
| 9 | `test_request_sort_by_default` | sort_by défaut | Request sans sort_by | `sort_by == SortBy.BEST` | Vérifie valeur défaut (algo Google) |

### SearchService _filter_flights (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 10 | `test_filter_max_stops_excludes` | Filtre escales exclut vols | Flights [0, 1, 2, 3 stops], max_stops=1 | 2 vols (0, 1 stops) | Vérifie exclusion stops > max |
| 11 | `test_filter_max_stops_zero_direct_only` | Filtre direct uniquement | Flights [0, 1, 2 stops], max_stops=0 | 1 vol (0 stops) | Vérifie filtre vols directs |
| 12 | `test_filter_max_duration_excludes` | Filtre durée exclut vols | Flights [10h, 15h, 25h], max_duration=20 | 2 vols (10h, 15h) | Vérifie exclusion durée > max |
| 13 | `test_filter_combined_and_logic` | Filtres combinés (AND) | Flights variés, max_stops=1, max_duration=15 | Vols satisfont TOUS filtres | Vérifie logique AND |
| 14 | `test_filter_none_no_filtering` | Aucun filtre actif | Flights [3 vols], tous filtres None | 3 vols (tous) | Vérifie pas de filtrage si None |
| 15 | `test_filter_all_excluded_empty` | Tous vols exclus | Flights [2, 3 stops], max_stops=0 | Liste vide | Vérifie retour liste vide |

### SearchService _select_best_flight (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 16 | `test_select_by_best` | Sélection Google (défaut) | Flights [A, B, C], sort_by=BEST | Vol A (premier) | Vérifie sélection premier élément (algo Google) |
| 17 | `test_select_by_price` | Sélection par prix | Flights [1500, 1000, 1200€], sort_by=PRICE | Vol 1000€ | Vérifie sélection prix min |
| 18 | `test_select_by_duration` | Sélection par durée | Flights [15h, 10h, 20h], sort_by=DURATION | Vol 10h | Vérifie sélection durée min |
| 19 | `test_select_by_stops` | Sélection par escales | Flights [2, 0, 1 stops], sort_by=STOPS | Vol 0 stops | Vérifie sélection escales min |
| 20 | `test_select_empty_returns_none` | Liste vide | Flights [], sort_by=BEST | None | Vérifie retour None si vide |
| 21 | `test_select_single_flight` | Un seul vol | Flights [1 vol], sort_by=BEST | Ce vol | Vérifie retour du seul vol |

### SearchService Integration (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 22 | `test_parse_results_with_filter` | Parsing avec filtre actif | HTML 10 vols, max_stops=1 | CombinationResult avec 1 vol (meilleur filtré) | Vérifie intégration filtre |
| 23 | `test_parse_results_no_match_skips` | Aucun vol ne match filtre | HTML 5 vols tous 3+ stops, max_stops=0 | Combinaison skippée, log WARNING | Vérifie skip si aucun match |
| 24 | `test_parse_results_sort_by_duration` | Sélection par durée | HTML 10 vols, sort_by=DURATION | CombinationResult avec vol le plus court | Vérifie sélection durée |
| 25 | `test_parse_results_backward_compatible` | Sans filtres (rétrocompat) | HTML 10 vols, aucun filtre | CombinationResult avec premier vol Google | Vérifie comportement défaut (BEST) |

**Total tests unitaires** : 4 + 6 + 6 + 6 + 4 = **26 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_filter_max_stops` | Mock HTML avec vols 0-3 escales | POST /search-flights avec max_stops=1 | Status 200, tous vols sélectionnés ont ≤1 escale |
| 2 | `test_integration_filter_direct_only` | Mock HTML avec vols variés | POST /search-flights avec max_stops=0 | Status 200, tous vols sont directs |
| 3 | `test_integration_sort_by_duration` | Mock HTML avec vols durées variées | POST /search-flights avec sort_by=duration | Status 200, chaque combinaison a le vol le plus court |
| 4 | `test_integration_no_filters_backward` | Mock HTML standard | POST /search-flights sans filtres | Status 200, comportement identique Story 6 |
| 5 | `test_integration_all_filtered_empty` | Mock HTML tous vols 3+ escales | POST /search-flights avec max_stops=0 | Status 200, results=[] car aucune combinaison valide |

**Total tests intégration** : **5 tests**

---

**TOTAL TESTS** : 26 unitaires + 5 intégration = **31 tests**

---

## Exemples JSON

**Exemple 1 : Request avec filtres**

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
      "to_city": "Paris",
      "date_range": {"start": "2025-06-15", "end": "2025-06-20"}
    }
  ],
  "max_stops": 1,
  "max_duration_hours": 18,
  "sort_by": "duration"
}
```

**Exemple 2 : Request vols directs uniquement**

```json
{
  "segments": [
    {
      "from_city": "Paris",
      "to_city": "New York",
      "date_range": {"start": "2025-07-01", "end": "2025-07-05"}
    },
    {
      "from_city": "New York",
      "to_city": "Paris",
      "date_range": {"start": "2025-07-10", "end": "2025-07-15"}
    }
  ],
  "max_stops": 0
}
```

**Exemple 3 : Request sans filtres (rétrocompatible)**

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
      "to_city": "Paris",
      "date_range": {"start": "2025-06-15", "end": "2025-06-20"}
    }
  ]
}
```

**Exemple 4 : Response (top 10 inchangé, trié par prix)**

```json
{
  "results": [
    {
      "price": 1200.0,
      "airline": "Air France",
      "departure_date": "2025-06-03",
      "segments": [
        {"from": "Paris", "to": "Tokyo", "date": "2025-06-03"},
        {"from": "Tokyo", "to": "Paris", "date": "2025-06-17"}
      ]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 15230,
    "segments_count": 2
  }
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Filtre max_stops fonctionne** : Tous vols sélectionnés ont `stops ≤ max_stops`
2. **Filtre max_stops=0 retourne directs** : Avec max_stops=0, seuls vols sans escale sélectionnés
3. **Filtre max_duration_hours fonctionne** : Tous vols sélectionnés ont durée ≤ max heures
4. **Filtres cumulatifs AND** : Si plusieurs filtres actifs, vols satisfont TOUS les critères
5. **Sélection Google (défaut)** : Sans sort_by, premier vol de la liste filtrée (algo Google)
6. **Sélection par prix** : Avec sort_by=price, vol le moins cher sélectionné
7. **Sélection par durée** : Avec sort_by=duration, vol le plus court sélectionné
8. **Sélection par escales** : Avec sort_by=stops, vol avec moins d'escales sélectionné
9. **Skip si aucun match** : Si aucun vol ne passe les filtres, combinaison skippée (log WARNING)
10. **Rétrocompatibilité** : Request sans filtres fonctionne identiquement à Story 6
11. **Top 10 inchangé** : Le ranking final reste trié par prix croissant (validate_results_sorted intact)

## Critères techniques

12. **Enum SortBy hérite str** : `class SortBy(str, Enum)` pour sérialisation JSON
13. **Filtres optionnels None** : Champs filtres avec `| None` et défaut `None`
14. **Validations Pydantic** : field_validator pour max_stops ≥ 0, max_duration > 0
15. **Type hints complets** : Tous nouveaux champs/méthodes annotés avec types modernes
16. **Méthodes privées** : `_filter_flights` et `_select_best_flight` préfixées underscore

## Critères qualité

17. **31 tests passent** : 26 unitaires + 5 intégration tous verts
18. **Coverage ≥80%** : Sur SearchRequest et SearchService modifiés
19. **Ruff + Mypy passent** : Aucune erreur lint/type
20. **Docstrings présentes** : Enum, nouveaux champs et méthodes documentés (1 ligne)

---

**Note** : Story simple (3 story points) → 20 critères couvrant filtrage (4), sélection (5), comportement (2), technique (5), qualité (4).
