---
title: "Story 12: Per-Segment Filters (Kayak only)"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-4/story-11"]
date: "2025-11-26"
keywords: ["filters", "per-segment", "max-duration", "max-stops", "min-layover", "duration-parsing", "filter-service", "segment-model", "pydantic-validation", "user-preferences", "kayak-request"]
scope: ["specs"]
technologies: ["Pydantic v2", "Python", "regex"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Filtres personnalisés par segment** : Utilisateurs recherchant vols multi-city (ex: Paris→Tokyo→Kyoto→Paris) veulent appliquer filtres différents par segment selon contraintes voyage (ex: segment 1 max 12h car travail lendemain, segment 2 accepte escales pour économiser, segment 3 min 1h30 layover pour confort)
- **Contrôle granulaire itinéraire** : Planification voyage complexe nécessite flexibilité filtres : segment business direct sans escale, segment loisir accepte vols longs économiques, segment retour évite layovers courts stressants (<1h30)
- **Format durée intuitif** : Utilisateurs grand public attendent format durée humain-lisible "12h", "1h30" (pas 720 minutes format technique), similaire affichage Kayak UI
- **Filtres optionnels** : Utilisateurs débutants ne veulent pas complexité, filtres doivent être optionnels avec comportement par défaut permissif (sans filtres = tous vols retournés)

## Contraintes métier

- **Route Kayak uniquement** : Les filtres per-segment ne sont implémentés que sur `/search-kayak` (pas `/search-google-flights`) car l'extraction des données nécessaires (durée exacte, stops, layover) n'est fiable que via API interne Kayak
- **Validation format durée stricte** : Regex `^\d{1,2}h(\d{2})?$` doit accepter uniquement formats valides ("12h", "1h30") et rejeter formats ambigus ("1h3", "72", "12h60") pour éviter erreurs parsing silencieuses
- **Limites escales réalistes** : Kayak affiche maximum 3 escales par segment, filtrer au-delà (ex: `max_stops=5`) inutile et confus pour utilisateurs
- **Pas de validation cross-segment** : Filtres appliqués indépendamment par segment (pas de règles globales "total escales <5" ou "durée totale itinéraire <30h"), simplicité MVP prioritaire
- **Deux SearchRequest distincts** : `SearchRequest` existant pour Google Flights (inchangé), `SearchRequestKayak` nouveau pour route Kayak avec support filtres per-segment

## Valeur business

- **Réduction bruit résultats** : Filtres permettent exclure vols non-pertinents (ex: 20h transit, 3 escales épuisantes) avant ranking, améliore qualité Top 10 retournés (satisfaction utilisateur +30-40%)
- **Foundation préférences utilisateur** : Architecture per-segment filters réutilisable pour futurs critères (preferred airlines, departure time windows, cabin class) sans refonte structurelle
- **Parity agrégateurs premium** : Kayak/Skyscanner offrent filtres granulaires, notre API doit matcher fonctionnalités pour compétitivité B2B (partenariats agences voyage)
- **Métriques comportement utilisateur** : Filters appliqués observables via logs (quels filtres populaires, valeurs fréquentes) pour optimiser UX futures versions
- **Pas de breaking change** : Route Google existante inchangée, aucune migration client nécessaire pour utilisateurs Google Flights existants

## Métriques succès

- **Taux adoption filtres** : 40-60% requêtes SearchRequestKayak incluent au moins 1 filtre segment (baseline adoption attendue post-lancement)
- **Taux filtrage efficace** : Filtres réduisent résultats moyens ~20-40% (ex: 500 vols avant filtrage → 300-400 après, élimination vols non-pertinents)
- **Zéro erreur format durée** : Validation regex rejette 100% formats invalides ("1h3", "12h60") avec messages clairs (pas de parsing silencieux incorrect)
- **Backward compatibility** : Route `/search-google-flights` avec SearchRequest existant continue à fonctionner sans modification
- **Coverage tests** : ≥80% sur SegmentFilters, KayakSegment model, parse_duration utility, FilterService apply_filters

---

# 📋 Spécifications Techniques

## 1. SegmentFilters (Pydantic Model)

**Rôle** : Définir filtres optionnels applicables à un segment individuel itinéraire multi-city avec validation format durée humain-lisible.

**Interface** :
```python
class SegmentFilters(BaseModel):
    """Filtres optionnels par segment avec validation format durée."""

    max_duration: str | None = None
    max_stops: int | None = None
    min_layover: str | None = None
```

**Champs** :

| Champ | Type | Description | Contraintes | Valeur par défaut |
|-------|------|-------------|-------------|-------------------|
| `max_duration` | `str \| None` | Durée maximale vol segment (format "Xh" ou "XhYY") | Regex `^\d{1,2}h(\d{2})?$`, minutes ≤ 1440 (24h) | `None` (pas de filtre) |
| `max_stops` | `int \| None` | Nombre maximal escales segment | 0 ≤ value ≤ 3 | `None` (pas de filtre) |
| `min_layover` | `str \| None` | Durée minimale escale/layover (format "Xh" ou "XhYY") | Regex `^\d{1,2}h(\d{2})?$`, minutes ≤ 720 (12h layover raisonnable) | `None` (pas de filtre) |

**Validations Pydantic** :

**1. Validation `max_duration` format** :
```python
@field_validator('max_duration', mode='after')
@classmethod
def validate_max_duration_format(cls, v: str | None) -> str | None:
    """Valide format durée 'Xh' ou 'XhYY' avec regex."""
```

- **Regex** : `^\d{1,2}h(\d{2})?$`
- **Comportement** :
  - `None` → Skip validation (filtre non appliqué)
  - `"12h"` → ✅ Valide
  - `"1h30"` → ✅ Valide (minutes 2 chiffres obligatoires si présent)
  - `"12h60"` → ❌ Lève `ValueError` (minutes ≥ 60 invalide)
  - `"1h3"` → ❌ Lève `ValueError` (minutes doit être 2 chiffres : "1h03")
  - `"72"` → ❌ Lève `ValueError` (manque unité "h")
  - `"999h"` → ❌ Lève `ValueError` (heures max 99)
- **Error message** : `"Invalid duration format 'X'. Expected format: 'Xh' or 'XhYY' (e.g., '12h', '1h30')"`

**2. Validation `max_duration` limites** :
```python
@field_validator('max_duration', mode='after')
@classmethod
def validate_max_duration_limit(cls, v: str | None) -> str | None:
    """Valide durée max ≤ 24h (1440 minutes)."""
```

- **Comportement** :
  - Convertir durée string en minutes via `parse_duration(v)`
  - Si minutes > 1440 → Lève `ValueError`
  - `"24h"` → ✅ Valide
  - `"25h"` → ❌ Lève `ValueError`
- **Error message** : `"max_duration exceeds limit: X minutes (max 1440 minutes = 24h)"`

**3. Validation `min_layover` format et limites** :
```python
@field_validator('min_layover', mode='after')
@classmethod
def validate_min_layover(cls, v: str | None) -> str | None:
    """Valide format + limite min_layover ≤ 12h."""
```

- **Comportement** : Identique `max_duration` validation
- **Limite** : ≤ 720 minutes (12h layover maximum raisonnable)
- **Justification** : Layover >12h = overnight, rare et edge case

**4. Validation `max_stops` range** :
```python
@field_validator('max_stops', mode='after')
@classmethod
def validate_max_stops_range(cls, v: int | None) -> int | None:
    """Valide max_stops entre 0 et 3."""
```

- **Comportement** :
  - `None` → Skip validation
  - 0 ≤ v ≤ 3 → ✅ Valide
  - v < 0 → ❌ Lève `ValueError` (escales négatives impossibles)
  - v > 3 → ❌ Lève `ValueError` (Google Flights max 3 escales affichées)
- **Error message** : `"max_stops must be between 0 and 3 (got: X)"`

**Comportement** :

- **Filtres optionnels** : Tous champs `None` par défaut, aucun filtre obligatoire
- **Validation stricte** : ConfigDict `extra="forbid"` rejette champs inconnus avec ValidationError (protection contre typos)
- **Validation indépendante** : Chaque filtre validé séparément, pas de cross-validation (ex: pas de règle "min_layover < max_duration")
- **Immutabilité** : Model Pydantic peut être frozen via `frozen=True` dans ConfigDict (optionnel, simplicité MVP)

**Edge cases** :

- **Tous filtres None** : SegmentFilters vide valide, équivalent "aucun filtre appliqué"
- **Durée "0h"** : Valide format regex mais invalide métier (vol instantané impossible), géré par FilterService (skip vols durée 0)
- **Minutes "00"** : `"12h00"` valide mais redondant vs `"12h"`, accepté pour flexibilité user input

**Erreurs levées** :
- `ValidationError` : Si format durée invalide, valeur hors range, ou type incorrect

**Logging structuré** :
- DEBUG : SegmentFilters créé avec valeurs non-None (ex: `{"max_duration": "12h", "max_stops": 1}`)

---

## 2. KayakSegment (Pydantic Model)

**Rôle** : Représenter un segment itinéraire multi-city pour route Kayak avec plage dates + filtres optionnels appliqués à ce segment.

**Fichier** : `app/models/kayak_segment.py`

**Interface** :
```python
class KayakSegment(BaseModel):
    """Segment itinéraire multi-city Kayak : date range + filtres optionnels."""

    date_range: DateRange
    filters: SegmentFilters | None = None
```

**Champs** :

| Champ | Type | Description | Contraintes | Valeur par défaut |
|-------|------|-------------|-------------|-------------------|
| `date_range` | `DateRange` | Plage dates départ segment (start/end ISO 8601) | DateRange validations existantes (end ≥ start, start ≥ today, max 15 jours) | Obligatoire |
| `filters` | `SegmentFilters \| None` | Filtres optionnels segment | SegmentFilters validations | `None` (pas de filtre) |

**Validations Pydantic** :

Pas de validation custom au-delà des champs (délégation validations à `DateRange` et `SegmentFilters`).

**Comportement** :

- **Validation stricte** : ConfigDict `extra="forbid"` rejette champs inconnus avec ValidationError (protection contre typos)
- **Composition models** : KayakSegment encapsule `DateRange` (réutilise validation existante Story 2-3) + `SegmentFilters` (nouveau)
- **Exclusif route Kayak** : Ce model est utilisé uniquement par `SearchRequestKayak`, pas par `SearchRequest` Google
- **Filtres optionnels par défaut** : Si `filters=None` → comportement équivalent ancien système (tous vols acceptés)

**Edge cases** :

- **KayakSegment sans filtres** : `KayakSegment(date_range=DateRange(...), filters=None)` → Valide, comportement permissif
- **DateRange invalide propagation** : Si `date_range` invalide → ValidationError levée par DateRange (pas géré par KayakSegment)

**Erreurs levées** :
- `ValidationError` : Si `date_range` invalide ou `filters` invalide (propagation validation sous-models)

**Logging structuré** :
- DEBUG : KayakSegment créé avec filtres non-None (contexte métier : segment N a filtres spécifiques)

---

## 3. SearchRequestKayak (Nouveau Model)

**Rôle** : Nouveau model de requête pour route `/search-kayak` avec support filtres per-segment. Le `SearchRequest` existant pour Google Flights reste **INCHANGÉ**.

**Fichier** : `app/models/request.py` (ajout à côté de SearchRequest existant)

**SearchRequest existant (INCHANGÉ - Route Google)** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city Google Flights avec URL template."""

    template_url: str
    segments_date_ranges: list[DateRange]  # ✅ Conservé inchangé
```

**SearchRequestKayak (NOUVEAU - Route Kayak)** :
```python
class SearchRequestKayak(BaseModel):
    """Requête recherche vols Kayak avec URL template + filtres per-segment."""

    template_url: str
    segments: list[KayakSegment]  # ✅ Nouveau champ avec filtres
```

**Comparaison Models** :

| Aspect | SearchRequest (Google) | SearchRequestKayak (Kayak) |
|--------|------------------------|---------------------------|
| Route | `/search-google-flights` | `/search-kayak` |
| Champ segments | `segments_date_ranges: list[DateRange]` | `segments: list[KayakSegment]` |
| Support filtres | ❌ Non | ✅ Oui (via `KayakSegment.filters`) |
| Breaking change | ❌ Aucun | ❌ Nouveau model |
| Tests existants | ✅ Inchangés | ✅ Nouveaux tests |

**Validations Pydantic SearchRequestKayak** :

Validations similaires à SearchRequest existant mais adaptées pour `segments: list[KayakSegment]` :

```python
@field_validator('segments', mode='after')
@classmethod
def validate_segments_count(cls, v: list[KayakSegment]) -> list[KayakSegment]:
    """Valide 2 à 5 segments (même règle que SearchRequest)."""
```

**Validations à implémenter** :

- **validate_segments_count** : 2 ≤ len(segments) ≤ 5
- **validate_date_ranges_max_days** : Itérer sur `segments[i].date_range`
- **validate_segments_chronological_order** : Itérer sur `segments[i].date_range`
- **validate_explosion_combinatoire** : Calculer days depuis `segments[i].date_range`

**Format Request SearchRequestKayak** :

```json
{
  "template_url": "https://www.kayak.fr/flights/...",
  "segments": [
    {
      "date_range": {"start": "2026-01-10", "end": "2026-01-18"},
      "filters": {"max_duration": "12h", "max_stops": 1}
    },
    {
      "date_range": {"start": "2026-02-16", "end": "2026-02-18"}
    }
  ]
}
```

**Avantages deux models distincts** :

- ✅ **Pas de breaking change** : Route Google existante fonctionne sans modification
- ✅ **Tests existants préservés** : ~20 tests SearchRequest continuent à passer
- ✅ **Séparation responsabilités** : Chaque route a son model adapté à ses besoins
- ✅ **Évolution indépendante** : SearchRequestKayak peut évoluer sans impacter Google

**Edge cases** :

- **KayakSegments sans filtres** : `{"segments": [{"date_range": {...}}]}` → ✅ Valide (filters optionnels)
- **Mauvais model sur mauvaise route** : Route `/search-kayak` avec format SearchRequest → ValidationError (champ `segments` manquant)

**Erreurs levées** :
- `ValidationError` : Si `segments` count invalide ou format incorrect

**Logging structuré** :
- INFO : SearchRequestKayak reçu avec X segments, Y segments avec filtres appliqués

---

## 4. parse_duration (Utility Function)

**Rôle** : Convertir string durée format humain-lisible ("12h", "1h30") en minutes (int) pour comparaison numérique dans FilterService.

**Interface** :
```python
def parse_duration(value: str) -> int:
    """
    Convertit durée format 'Xh' ou 'XhYY' en minutes.

    Args:
        value: String durée format "12h" ou "1h30"

    Returns:
        Durée totale en minutes (int)

    Raises:
        ValueError: Si format invalide (regex mismatch)
    """
```

**Comportement** :

**Étape 1 : Validation format regex**
1. Appliquer regex `^\d{1,2}h(\d{2})?$` sur `value`
2. Si aucun match → Lève `ValueError` avec message format attendu
3. Extraire groups : `hours` (group 1), `minutes` (group 2 optionnel)

**Étape 2 : Extraction heures**
4. Parser `hours` en int (toujours présent)
5. Exemple : `"12h"` → hours=12, `"1h30"` → hours=1

**Étape 3 : Extraction minutes (optionnel)**
6. Si group `minutes` présent → Parser en int
7. Si group `minutes` absent → minutes=0
8. Exemple : `"12h"` → minutes=0, `"1h30"` → minutes=30

**Étape 4 : Validation minutes ≥ 60**
9. Si minutes ≥ 60 → Lève `ValueError` (minutes invalides)
10. Exemple : `"12h60"` → ValueError, `"12h59"` → ✅ Valide

**Étape 5 : Conversion total minutes**
11. Calculer `total_minutes = (hours × 60) + minutes`
12. Retourner `total_minutes` (int)

**Exemples Parsing** :

| Input | Regex Match | Hours | Minutes | Total Minutes | Valide |
|-------|-------------|-------|---------|---------------|--------|
| `"12h"` | ✅ | 12 | 0 | 720 | ✅ |
| `"1h30"` | ✅ | 1 | 30 | 90 | ✅ |
| `"24h"` | ✅ | 24 | 0 | 1440 | ✅ |
| `"0h"` | ✅ | 0 | 0 | 0 | ✅ (métier invalide mais parsing OK) |
| `"12h60"` | ✅ | 12 | 60 | ❌ | ❌ ValueError (minutes ≥ 60) |
| `"1h3"` | ❌ | - | - | - | ❌ ValueError (format invalide) |
| `"72"` | ❌ | - | - | - | ❌ ValueError (manque "h") |
| `"999h"` | ✅ | 999 | 0 | 59940 | ✅ (parsing OK, limite métier gérée ailleurs) |

**Edge cases** :

- **"0h"** : Valide parsing (0 minutes), invalide métier (vol instantané impossible), géré par FilterService
- **"99h99"** : Regex accept (2 chiffres max heures + minutes), mais minutes ≥ 60 → ValueError
- **Leading zeros** : `"01h05"` valide regex, parsing accepte (hours=1, minutes=5)
- **Espaces** : `"12 h"`, `" 12h "` invalides regex (pas de trim automatique), caller doit strip avant

**Erreurs levées** :
- `ValueError` : Si format invalide (regex mismatch) ou minutes ≥ 60

**Logging structuré** :
- DEBUG : Durée parsée avec succès (input → output minutes)
- WARNING : ValueError levée avec input invalide (aide debugging user input)

---

## 5. FilterService

**Rôle** : Appliquer filtres SegmentFilters sur liste vols GoogleFlightDTO pour éliminer vols non-conformes critères utilisateur.

**Interface** :
```python
class FilterService:
    """Service application filtres per-segment sur vols."""

    def apply_filters(
        self,
        flights: list[GoogleFlightDTO],
        filters: SegmentFilters | None
    ) -> list[GoogleFlightDTO]:
        """
        Filtre vols selon critères SegmentFilters.

        Args:
            flights: Liste vols à filtrer
            filters: Filtres à appliquer (None = aucun filtrage)

        Returns:
            Liste vols filtrés (sous-ensemble input)
        """
```

**Comportement Filtrage** :

**Étape 1 : Early return si aucun filtre**
1. Si `filters is None` → Retourner `flights` inchangé (aucun filtrage appliqué)
2. Si `filters` tous champs None (`max_duration=None, max_stops=None, min_layover=None`) → Retourner `flights` inchangé

**Étape 2 : Filtrage max_duration**
3. Si `filters.max_duration is not None` :
   - Convertir `filters.max_duration` en minutes via `parse_duration()`
   - Filtrer vols : garder seulement `flight` où `parse_duration(flight.duration) ≤ max_duration_minutes`
   - Exemple : `max_duration="12h"` (720 min) → Exclure vols "13h 30min" (810 min)

**Étape 3 : Filtrage max_stops**
4. Si `filters.max_stops is not None` :
   - Filtrer vols : garder seulement `flight` où `flight.stops ≤ filters.max_stops`
   - Exemple : `max_stops=1` → Exclure vols avec `stops=2` ou `stops=3`

**Étape 4 : Filtrage min_layover**
5. Si `filters.min_layover is not None` :
   - **Note** : GoogleFlightDTO ne contient pas champ `layover_duration` (données Google Flights limitées)
   - **Comportement Story 12 MVP** : Skip filtrage min_layover (log WARNING feature non implémentée)
   - **Future Story** : Requiert parsing détaillé escales depuis network API responses (field GoogleFlightDTO extended)

**Étape 5 : Retour liste filtrée**
6. Retourner liste vols restants après tous filtres appliqués
7. Si aucun vol ne passe filtres → Retourner liste vide `[]` (pas d'exception)

**Exemples Filtrage** :

**Scenario 1 : max_duration appliqué**
- Input : `flights=[flight1(duration="11h"), flight2(duration="14h"), flight3(duration="10h 30min")]`
- Filters : `SegmentFilters(max_duration="12h")`
- Output : `[flight1, flight3]` (flight2 exclu car 14h > 12h)

**Scenario 2 : max_stops appliqué**
- Input : `flights=[flight1(stops=0), flight2(stops=1), flight3(stops=2)]`
- Filters : `SegmentFilters(max_stops=1)`
- Output : `[flight1, flight2]` (flight3 exclu car stops=2 > max_stops=1)

**Scenario 3 : Multiple filtres combinés**
- Input : `flights=[flight1(duration="10h", stops=0), flight2(duration="11h", stops=1), flight3(duration="9h", stops=2)]`
- Filters : `SegmentFilters(max_duration="12h", max_stops=1)`
- Output : `[flight1, flight2]` (flight3 exclu car stops=2 > max_stops=1 malgré durée OK)

**Scenario 4 : Aucun vol ne passe filtres**
- Input : `flights=[flight1(duration="15h", stops=2), flight2(duration="16h", stops=3)]`
- Filters : `SegmentFilters(max_duration="12h", max_stops=1)`
- Output : `[]` (liste vide, aucun vol conforme)

**Edge cases** :

- **GoogleFlightDTO.duration format invalide** : Si `flight.duration` format non parseable (ex: "Unknown") → Skip vol (exclude silencieusement, log WARNING)
- **Filtres None partiel** : `SegmentFilters(max_duration="12h", max_stops=None)` → Applique seulement filtre duration, ignore stops
- **Durée exacte limite** : `max_duration="12h"` (720 min), `flight.duration="12h 00min"` (720 min) → ✅ Inclus (≤ pas <)
- **min_layover non implémenté** : Log WARNING feature not implemented, skip filtre (pas d'exception bloquante)

**Erreurs levées** :
- Aucune exception levée (filtrage silencieux, retourne liste vide si aucun match)

**Logging structuré** :
- INFO : Filtrage appliqué avec résultat (X vols input → Y vols output, Z vols filtrés)
- DEBUG : Détail filtres appliqués (max_duration=X, max_stops=Y, vols exclus : [flight_ids])
- WARNING : min_layover filter skipped (feature not implemented yet)
- WARNING : Vol avec duration format invalide exclu du filtrage

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### SegmentFilters Validation (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_segment_filters_all_none` | Filtres vides (tous None) valides | `SegmentFilters()` (defaults None) | Model créé sans exception, tous champs `None` | Vérifie comportement par défaut permissif |
| 2 | `test_segment_filters_max_duration_valid` | Format durée "12h" valide | `SegmentFilters(max_duration="12h")` | Model créé, `max_duration == "12h"` | Vérifie validation format "Xh" |
| 3 | `test_segment_filters_max_duration_with_minutes` | Format durée "1h30" valide | `SegmentFilters(max_duration="1h30")` | Model créé, `max_duration == "1h30"` | Vérifie validation format "XhYY" |
| 4 | `test_segment_filters_max_duration_invalid_format` | Format durée invalide "1h3" | `SegmentFilters(max_duration="1h3")` | Lève `ValidationError` message "Invalid duration format" | Vérifie regex rejette minutes 1 chiffre |
| 5 | `test_segment_filters_max_duration_exceeds_limit` | Durée >24h invalide | `SegmentFilters(max_duration="25h")` | Lève `ValidationError` message "exceeds limit" | Vérifie limite 1440 minutes |
| 6 | `test_segment_filters_max_stops_valid` | max_stops entre 0-3 valide | `SegmentFilters(max_stops=1)` | Model créé, `max_stops == 1` | Vérifie validation range escales |
| 7 | `test_segment_filters_max_stops_out_of_range` | max_stops >3 invalide | `SegmentFilters(max_stops=5)` | Lève `ValidationError` message "must be between 0 and 3" | Vérifie limite max 3 escales |
| 8 | `test_segment_filters_min_layover_exceeds_limit` | min_layover >12h invalide | `SegmentFilters(min_layover="13h")` | Lève `ValidationError` message "exceeds limit" | Vérifie limite 720 minutes layover |

### KayakSegment Model (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 9 | `test_kayak_segment_with_filters` | KayakSegment avec date_range + filtres valide | `KayakSegment(date_range=DateRange(...), filters=SegmentFilters(...))` | Model créé avec `date_range` et `filters` non-None | Vérifie composition models |
| 10 | `test_kayak_segment_without_filters` | KayakSegment avec date_range seulement (filters None) | `KayakSegment(date_range=DateRange(...), filters=None)` | Model créé avec `filters == None` | Vérifie filtres optionnels |
| 11 | `test_kayak_segment_invalid_date_range` | DateRange invalide propagation | `KayakSegment(date_range=DateRange(start="2026-02-01", end="2026-01-01"))` | Lève `ValidationError` depuis DateRange (end < start) | Vérifie validation DateRange propagée |

### parse_duration Utility (5 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 12 | `test_parse_duration_hours_only` | Parse format "12h" | `parse_duration("12h")` | `720` (minutes) | Vérifie conversion heures → minutes |
| 13 | `test_parse_duration_hours_minutes` | Parse format "1h30" | `parse_duration("1h30")` | `90` (minutes) | Vérifie conversion heures + minutes → total minutes |
| 14 | `test_parse_duration_zero` | Parse "0h" edge case | `parse_duration("0h")` | `0` (minutes) | Vérifie parsing OK (validation métier ailleurs) |
| 15 | `test_parse_duration_invalid_format` | Format invalide "72" sans unité | `parse_duration("72")` | Lève `ValueError` message "Expected format" | Vérifie regex rejette format invalide |
| 16 | `test_parse_duration_minutes_out_of_range` | Minutes ≥60 invalide "12h60" | `parse_duration("12h60")` | Lève `ValueError` message "minutes" | Vérifie validation minutes <60 |

### FilterService apply_filters (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 17 | `test_apply_filters_none` | Aucun filtre appliqué (filters=None) | `flights=[flight1, flight2], filters=None` | `[flight1, flight2]` inchangé | Vérifie early return si filters None |
| 18 | `test_apply_filters_max_duration` | Filtre max_duration exclut vols longs | `flights=[flight1(duration="11h"), flight2(duration="14h")], filters=SegmentFilters(max_duration="12h")` | `[flight1]` (flight2 exclu) | Vérifie filtrage durée correctement appliqué |
| 19 | `test_apply_filters_max_stops` | Filtre max_stops exclut vols avec escales | `flights=[flight1(stops=0), flight2(stops=2)], filters=SegmentFilters(max_stops=1)` | `[flight1]` (flight2 exclu) | Vérifie filtrage escales correctement appliqué |
| 20 | `test_apply_filters_combined` | Multiple filtres combinés (AND logic) | `flights=[flight1(duration="10h", stops=0), flight2(duration="11h", stops=2)], filters=SegmentFilters(max_duration="12h", max_stops=1)` | `[flight1]` (flight2 exclu car stops>1) | Vérifie logic combinaison filtres |
| 21 | `test_apply_filters_no_match` | Aucun vol ne passe filtres | `flights=[flight1(duration="15h", stops=2)], filters=SegmentFilters(max_duration="12h", max_stops=1)` | `[]` liste vide | Vérifie comportement aucun match (pas d'exception) |
| 22 | `test_apply_filters_invalid_duration_format` | Vol avec duration invalide exclu silencieusement | `flights=[flight1(duration="Unknown"), flight2(duration="10h")], filters=SegmentFilters(max_duration="12h")` | `[flight2]` (flight1 exclu car format invalide) | Vérifie handling duration non parseable |

**Total tests unitaires** : 8 (SegmentFilters) + 3 (KayakSegment) + 5 (parse_duration) + 6 (FilterService) = **22 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_kayak_with_segment_filters` | Mock SearchService avec 3 KayakSegments dont 2 avec filtres, 10 vols par combinaison | POST `/api/v1/search-kayak` avec body `SearchRequestKayak` format `segments` | Status 200, `SearchResponse.results` contient vols filtrés correctement (segment 1 max 12h appliqué, segment 2 sans filtres, segment 3 max_stops=1 appliqué) |
| 2 | `test_integration_kayak_validation_invalid_filters` | App FastAPI TestClient | POST `/api/v1/search-kayak` avec `segments[0].filters.max_duration="invalid"` | Status 422, JSON error contient message "Invalid duration format" |
| 3 | `test_integration_google_route_unchanged` | App FastAPI TestClient | POST `/api/v1/search-google-flights` avec format `SearchRequest` existant (`segments_date_ranges`) | Status 200, route Google continue à fonctionner sans modification |
| 4 | `test_integration_kayak_filters_reduce_results` | Mock SearchService sans filtres baseline (100 vols total), puis avec filtres stricts | Comparer résultats sans filtres vs avec `max_duration="10h", max_stops=0` sur tous segments | Résultats filtrés ~30-40% moins nombreux (filtrage efficace), Top 10 ranking fonctionne sur résultats filtrés |
| 5 | `test_integration_kayak_segments_without_filters` | App FastAPI TestClient | POST `/api/v1/search-kayak` avec `segments[i].filters=null` pour tous KayakSegments | Status 200, comportement équivalent ancien système (tous vols retournés sans filtrage) |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 22 unitaires + 5 intégration = **27 tests**

---

## Exemples JSON

**Exemple 1 : SearchRequestKayak avec Per-Segment Filters (Route `/search-kayak`)**

```json
{
  "template_url": "https://www.kayak.fr/flights/PAR-TYO/2026-01-10/TYO-KYO/2026-02-16/KYO-PAR/2026-03-30",
  "segments": [
    {
      "date_range": {
        "start": "2026-01-10",
        "end": "2026-01-18"
      },
      "filters": {
        "max_duration": "12h",
        "max_stops": 1
      }
    },
    {
      "date_range": {
        "start": "2026-02-16",
        "end": "2026-02-18"
      }
    },
    {
      "date_range": {
        "start": "2026-03-30",
        "end": "2026-04-01"
      },
      "filters": {
        "min_layover": "1h30"
      }
    }
  ]
}
```

**Contexte** : Requête Kayak multi-city 3 segments (Paris→Tokyo→Kyoto→Paris) avec filtres différents par segment :
- Segment 1 : Max 12h vol direct ou 1 escale (business trip, rapidité prioritaire)
- Segment 2 : Aucun filtre (loisir, flexibilité totale)
- Segment 3 : Min 1h30 layover si escale (confort, éviter stress connexions courtes)

---

**Exemple 2 : SearchRequest Google (Route `/search-google-flights` - INCHANGÉ)**

```json
{
  "template_url": "https://www.google.com/travel/flights?tfs=CBwQAh...",
  "segments_date_ranges": [
    {
      "start": "2026-01-10",
      "end": "2026-01-18"
    },
    {
      "start": "2026-02-16",
      "end": "2026-02-18"
    }
  ]
}
```

**Contexte** : Route Google Flights utilise toujours l'ancien format `SearchRequest` avec `segments_date_ranges`. Aucun changement requis pour clients existants.

---

**Exemple 3 : SearchRequestKayak Sans Filtres**

```json
{
  "template_url": "https://www.kayak.fr/flights/...",
  "segments": [
    {
      "date_range": {
        "start": "2026-01-10",
        "end": "2026-01-18"
      }
    },
    {
      "date_range": {
        "start": "2026-02-16",
        "end": "2026-02-18"
      }
    }
  ]
}
```

**Contexte** : Requête Kayak sans aucun filtre appliqué (filters=null implicite), tous vols retournés.

---

**Exemple 4 : ValidationError Format Durée Invalide (Route Kayak)**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "segments", 0, "filters", "max_duration"],
      "msg": "Value error, Invalid duration format '1h3'. Expected format: 'Xh' or 'XhYY' (e.g., '12h', '1h30')",
      "input": "1h3",
      "ctx": {
        "error": "Invalid duration format"
      }
    }
  ]
}
```

**Contexte** : Client envoie format durée invalide "1h3" sur route Kayak (minutes doit être 2 chiffres "1h03"), ValidationError Pydantic avec message clair explicitant format attendu.

---

**Exemple 5 : Logging Filtrage Appliqué**

```json
{
  "timestamp": "2025-11-25T10:30:00Z",
  "level": "INFO",
  "service": "FilterService",
  "message": "Filters applied to segment",
  "segment_index": 0,
  "filters": {
    "max_duration": "12h",
    "max_stops": 1
  },
  "flights_input": 15,
  "flights_output": 8,
  "flights_filtered": 7,
  "filter_efficiency": "46.7%"
}
```

**Contexte** : Logging structuré après application filtres sur segment 1, 15 vols input → 8 vols output (7 vols exclus car durée >12h ou stops >1), efficacité filtrage 46.7%.

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **SegmentFilters validation format durée** : Regex `^\d{1,2}h(\d{2})?$` accepte "12h", "1h30", rejette "1h3", "72", "12h60" avec messages clairs (vérifié tests validation)

2. **SegmentFilters validation limites** : `max_duration` ≤ 24h (1440 min), `min_layover` ≤ 12h (720 min), `max_stops` entre 0-3 (vérifié ValidationError si hors range)

3. **SegmentFilters optionnels** : Tous champs `None` par défaut, SegmentFilters vide valide `SegmentFilters()` créé sans exception (vérifié comportement permissif)

4. **KayakSegment composition** : KayakSegment encapsule `date_range: DateRange` (obligatoire) + `filters: SegmentFilters | None` (optionnel) avec validations propagées (vérifié DateRange invalid → ValidationError)

5. **Deux SearchRequest distincts** : `SearchRequest` existant pour Google (inchangé avec `segments_date_ranges`), `SearchRequestKayak` nouveau pour Kayak (avec `segments: list[KayakSegment]`)

6. **SearchRequest Google inchangé** : Route `/search-google-flights` continue à utiliser `SearchRequest` avec `segments_date_ranges: list[DateRange]`, aucune modification nécessaire (vérifié tests existants passent)

7. **SearchRequestKayak validations** : Validations similaires à SearchRequest (2-5 segments, max 15 jours, chronologie, explosion combinatoire) fonctionnent sur `segments[i].date_range`

8. **parse_duration conversion** : Convertit "12h" → 720 minutes, "1h30" → 90 minutes, lève ValueError si format invalide ou minutes ≥60 (vérifié tests unitaires)

9. **FilterService filtrage max_duration** : Exclut vols avec `parse_duration(flight.duration) > max_duration_minutes` (vérifié flight "14h" exclu si max "12h")

10. **FilterService filtrage max_stops** : Exclut vols avec `flight.stops > max_stops` (vérifié flight stops=2 exclu si max_stops=1)

11. **FilterService filtrage combiné** : Multiple filtres appliqués en AND logic, vol doit passer TOUS les filtres pour être inclus (vérifié tests combined filters)

12. **FilterService aucun match** : Si aucun vol ne passe filtres → retourne liste vide `[]` sans exception (vérifié comportement gracieux)

13. **FilterService filters None** : Si `filters=None` ou tous champs None → retourne `flights` inchangé (vérifié early return, aucun filtrage appliqué)

## Critères techniques

14. **Type hints PEP 695** : SegmentFilters, KayakSegment, SearchRequestKayak, parse_duration, FilterService annotés avec type hints modernes (`str | None`, `list[KayakSegment]`, `list[GoogleFlightDTO]`)

15. **Pydantic v2 validations** : `field_validator` mode='after' sur champs SegmentFilters, validators réutilisent fonction `parse_duration` pour cohérence (vérifié validation pipeline)

16. **ConfigDict extra="forbid"** : SegmentFilters, KayakSegment, SearchRequestKayak rejettent champs inconnus avec ValidationError explicite

17. **Regex compilation optimisée** : Regex `^\d{1,2}h(\d{2})?$` compilé une fois au niveau module pour performance (avoid re-compilation par validation)

18. **parse_duration pure function** : Pas de side-effects, retourne int ou lève ValueError, pas de logging interne (testabilité isolation)

19. **FilterService stateless** : Méthode `apply_filters` pure sans état interne, pas de mutation input `flights` liste (retourne nouvelle liste filtrée)

20. **Logging structuré JSON complet** : Logs filtrage incluent : segment_index, filters appliqués, flights_input/output counts, filter_efficiency % (format pythonjsonlogger)

21. **ValidationError messages clairs** : Messages UX-friendly avec exemples formats attendus ("Expected format: 'Xh' or 'XhYY' (e.g., '12h', '1h30')"), pas juste "invalid"

22. **min_layover feature flag** : min_layover skip avec log WARNING "not implemented yet" (future story), pas d'exception bloquante (dégradation gracieuse MVP)

## Critères qualité

23. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code SegmentFilters, KayakSegment, parse_duration, FilterService apply_filters (pytest-cov)

24. **27 tests passent** : 22 tests unitaires (8 SegmentFilters + 3 KayakSegment + 5 parse_duration + 6 FilterService) + 5 tests intégration tous verts (pytest -v)

25. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

26. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

27. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks SearchService configurés

28. **Docstrings 1 ligne** : SegmentFilters, KayakSegment, SearchRequestKayak, parse_duration, FilterService avec docstring descriptive, focus POURQUOI pas QUOI

29. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON (pas d'implémentation complète)

30. **Commits conventional** : Story 12 committée avec message `feat(kayak): add per-segment filters (max_duration, max_stops, min_layover)` conforme Conventional Commits

---

**Note importante** : Story complexité moyenne (5 story points) → 30 critères couvrent exhaustivement architecture per-segment filters (13 fonctionnels avec deux models distincts + min_layover feature flag), parsing durée résilient + validation Pydantic v2 (9 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (regex format, limites 24h/12h/3 stops, deux models SearchRequest), **M**esurable (27 tests passent, coverage ≥80%, filtrage réduit ~20-40% vols), **A**tteignable (Pydantic v2 validation mature, regex standard Python), **R**elevant (filtres granulaires = valeur UX premium, foundation préférences utilisateur), **T**emporel (MVP Phase 5, après Epics 1-3 déjà implémentés).

**Avantages deux models distincts** :
- ✅ **Pas de breaking change** : Tests existants (~20) continuent à passer sans modification
- ✅ **Évolution indépendante** : SearchRequestKayak peut évoluer sans impacter Google
- ✅ **Séparation responsabilités** : Chaque route a son model adapté
- ✅ **Architecture scalable** : Futurs filtres (preferred airlines, time windows) facilement ajoutables sur Kayak
