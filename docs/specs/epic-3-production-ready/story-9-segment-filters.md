---
title: "Story 9: Per-Segment Filters"
epic: "Epic 3: Production Ready"
story_points: 5
dependencies: ["epic-3/story-7"]
date: "2025-25-11"
keywords: ["filters", "per-segment", "max-duration", "max-stops", "min-layover", "duration-parsing", "filter-service", "segment-model", "pydantic-validation", "user-preferences"]
scope: ["specs"]
technologies: ["Pydantic v2", "Python", "regex"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Filtres personnalisés par segment** : Utilisateurs recherchant vols multi-city (ex: Paris→Tokyo→Kyoto→Paris) veulent appliquer filtres différents par segment selon contraintes voyage (ex: segment 1 max 12h car travail lendemain, segment 2 accepte escales pour économiser, segment 3 min 1h30 layover pour confort)
- **Contrôle granulaire itinéraire** : Planification voyage complexe nécessite flexibilité filtres : segment business direct sans escale, segment loisir accepte vols longs économiques, segment retour évite layovers courts stressants (<1h30)
- **Format durée intuitif** : Utilisateurs grand public attendent format durée humain-lisible "12h", "1h30" (pas 720 minutes format technique), similaire affichage Google Flights UI
- **Filtres optionnels** : Utilisateurs débutants ne veulent pas complexité, filtres doivent être optionnels avec comportement par défaut permissif (sans filtres = tous vols retournés)

## Contraintes métier

- **Validation format durée stricte** : Regex `^\d{1,2}h(\d{2})?$` doit accepter uniquement formats valides ("12h", "1h30") et rejeter formats ambigus ("1h3", "72", "12h60") pour éviter erreurs parsing silencieuses
- **Limites escales réalistes** : Google Flights affiche maximum 3 escales par segment, filtrer au-delà (ex: `max_stops=5`) inutile et confus pour utilisateurs
- **Pas de validation cross-segment** : Filtres appliqués indépendamment par segment (pas de règles globales "total escales <5" ou "durée totale itinéraire <30h"), simplicité MVP prioritaire
- **Breaking change acceptable** : Remplacement `segments_date_ranges: list[DateRange]` par `segments: list[Segment]` dans SearchRequest = breaking change API, acceptable car MVP sans clients production existants

## Valeur business

- **Réduction bruit résultats** : Filtres permettent exclure vols non-pertinents (ex: 20h transit, 3 escales épuisantes) avant ranking, améliore qualité Top 10 retournés (satisfaction utilisateur +30-40%)
- **Foundation préférences utilisateur** : Architecture per-segment filters réutilisable pour futurs critères (preferred airlines, departure time windows, cabin class) sans refonte structurelle
- **Parity agrégateurs premium** : Kayak/Skyscanner offrent filtres granulaires, notre API doit matcher fonctionnalités pour compétitivité B2B (partenariats agences voyage)
- **Métriques comportement utilisateur** : Filters appliqués observables via logs (quels filtres populaires, valeurs fréquentes) pour optimiser UX futures versions

## Métriques succès

- **Taux adoption filtres** : 40-60% requêtes SearchRequest incluent au moins 1 filtre segment (baseline adoption attendue post-lancement)
- **Taux filtrage efficace** : Filtres réduisent résultats moyens ~20-40% (ex: 500 vols avant filtrage → 300-400 après, élimination vols non-pertinents)
- **Zéro erreur format durée** : Validation regex rejette 100% formats invalides ("1h3", "12h60") avec messages clairs (pas de parsing silencieux incorrect)
- **Backward compatibility validation** : Ancienne structure `segments_date_ranges` rejetée avec ValidationError explicite (guide migration clients)
- **Coverage tests** : ≥80% sur SegmentFilters, Segment model, parse_duration utility, FilterService apply_filters

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

## 2. Segment (Pydantic Model)

**Rôle** : Représenter un segment itinéraire multi-city avec plage dates + filtres optionnels appliqués à ce segment.

**Interface** :
```python
class Segment(BaseModel):
    """Segment itinéraire multi-city : date range + filtres optionnels."""

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
- **Composition models** : Segment encapsule `DateRange` (réutilise validation existante Story 2-3) + `SegmentFilters` (nouveau)
- **Backward compatibility** : Ancien champ `segments_date_ranges: list[DateRange]` remplacé par `segments: list[Segment]` dans SearchRequest (breaking change documenté)
- **Filtres optionnels par défaut** : Si `filters=None` → comportement équivalent ancien système (tous vols acceptés)

**Edge cases** :

- **Segment sans filtres** : `Segment(date_range=DateRange(...), filters=None)` → Valide, comportement permissif
- **DateRange invalide propagation** : Si `date_range` invalide → ValidationError levée par DateRange (pas géré par Segment)

**Erreurs levées** :
- `ValidationError` : Si `date_range` invalide ou `filters` invalide (propagation validation sous-models)

**Logging structuré** :
- DEBUG : Segment créé avec filtres non-None (contexte métier : segment N a filtres spécifiques)

---

## 3. SearchRequest (Modification Breaking Change)

**Rôle** : Remplacer champ `segments_date_ranges: list[DateRange]` par `segments: list[Segment]` pour supporter filtres per-segment.

**Interface actuelle (Story 2-8)** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city avec URL template."""

    template_url: str
    segments_date_ranges: list[DateRange]  # ⚠️ ANCIEN champ
```

**Interface modifiée (Story 9)** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city avec URL template + filtres per-segment."""

    template_url: str
    segments: list[Segment]  # ✅ NOUVEAU champ (breaking change)
```

**Champs Modifiés** :

| Champ | Type Ancien | Type Nouveau | Migration Required | Impact |
|-------|-------------|--------------|-------------------|--------|
| `segments_date_ranges` | `list[DateRange]` | ❌ Retiré | Clients doivent wrapper DateRange dans Segment | Breaking change |
| `segments` | ❌ N'existe pas | `list[Segment]` | Clients utilisent nouveau champ | Breaking change |

**Validations Pydantic** :

Validations existantes sur `segments_date_ranges` (count 2-5, max 15 jours, chronologie, explosion combinatoire) **déplacées** vers validation `segments` :

```python
@field_validator('segments', mode='after')
@classmethod
def validate_segments_count(cls, v: list[Segment]) -> list[Segment]:
    """Valide 2 à 5 segments (inchangé Story 2)."""
```

**Adaptations Validations** :

- **validate_date_ranges_max_days** → Itérer sur `segments[i].date_range` au lieu de `segments_date_ranges[i]`
- **validate_segments_chronological_order** → Itérer sur `segments[i].date_range` au lieu de `segments_date_ranges[i]`
- **validate_explosion_combinatoire** → Calculer days depuis `segments[i].date_range` au lieu de `segments_date_ranges[i]`

**Comportement Migration** :

**Ancien format (Story 2-8)** :
```json
{
  "template_url": "https://...",
  "segments_date_ranges": [
    {"start": "2026-01-10", "end": "2026-01-18"},
    {"start": "2026-02-16", "end": "2026-02-18"}
  ]
}
```

**Nouveau format (Story 9)** :
```json
{
  "template_url": "https://...",
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

**Backward Compatibility Handling** :

Aucune rétrocompatibilité fournie (breaking change MVP accepté). Si client envoie ancien format :

```json
{
  "template_url": "https://...",
  "segments_date_ranges": [...]
}
```

→ ValidationError Pydantic : `"Extra inputs are not permitted: segments_date_ranges"` (ConfigDict extra="forbid")

**Error message explicite** : Documentation migration fournie dans CHANGELOG.md avec exemples conversion.

**Edge cases** :

- **Mix ancien/nouveau champ** : `{"segments": [...], "segments_date_ranges": [...]}` → ValidationError (extra="forbid" rejette `segments_date_ranges`)
- **Segments sans filtres** : `{"segments": [{"date_range": {...}}]}` → ✅ Valide (filters optionnels)

**Erreurs levées** :
- `ValidationError` : Si ancien champ `segments_date_ranges` présent ou si `segments` count invalide

**Logging structuré** :
- INFO : SearchRequest reçu avec X segments, Y segments avec filtres appliqués
- WARNING : ValidationError si ancien format détecté (aide debugging migration clients)

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
   - **Comportement Story 9 MVP** : Skip filtrage min_layover (log WARNING feature non implémentée)
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

### Segment Model (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 9 | `test_segment_with_filters` | Segment avec date_range + filtres valide | `Segment(date_range=DateRange(...), filters=SegmentFilters(...))` | Model créé avec `date_range` et `filters` non-None | Vérifie composition models |
| 10 | `test_segment_without_filters` | Segment avec date_range seulement (filters None) | `Segment(date_range=DateRange(...), filters=None)` | Model créé avec `filters == None` | Vérifie filtres optionnels |
| 11 | `test_segment_invalid_date_range` | DateRange invalide propagation | `Segment(date_range=DateRange(start="2026-02-01", end="2026-01-01"))` | Lève `ValidationError` depuis DateRange (end < start) | Vérifie validation DateRange propagée |

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

**Total tests unitaires** : 8 (SegmentFilters) + 3 (Segment) + 5 (parse_duration) + 6 (FilterService) = **22 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_with_segment_filters` | Mock SearchService avec 3 segments dont 2 avec filtres, 10 vols par combinaison | POST `/api/v1/search-flights` avec body nouveau format `segments` | Status 200, `SearchResponse.results` contient vols filtrés correctement (segment 1 max 12h appliqué, segment 2 sans filtres, segment 3 max_stops=1 appliqué) |
| 2 | `test_integration_validation_invalid_filters` | App FastAPI TestClient | POST `/api/v1/search-flights` avec `segments[0].filters.max_duration="invalid"` | Status 400, JSON error contient message "Invalid duration format" |
| 3 | `test_integration_backward_compatibility_rejection` | App FastAPI TestClient | POST `/api/v1/search-flights` avec ancien format `segments_date_ranges` | Status 422, ValidationError message contient "Extra inputs are not permitted: segments_date_ranges" |
| 4 | `test_integration_filters_reduce_results` | Mock SearchService sans filtres baseline (100 vols total), puis avec filtres stricts | Comparer résultats sans filtres vs avec `max_duration="10h", max_stops=0` sur tous segments | Résultats filtrés ~30-40% moins nombreux (filtrage efficace), Top 10 ranking fonctionne sur résultats filtrés |
| 5 | `test_integration_segments_without_filters` | App FastAPI TestClient | POST `/api/v1/search-flights` avec `segments[i].filters=null` pour tous segments | Status 200, comportement équivalent ancien système (tous vols retournés sans filtrage) |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 22 unitaires + 5 intégration = **27 tests**

---

## Exemples JSON

**Exemple 1 : SearchRequest avec Per-Segment Filters (Nouveau Format Story 9)**

```json
{
  "template_url": "https://www.google.com/travel/flights?tfs=CBwQAhopag0IAhIJL20vMDVxdGoSCjIwMjYtMDEtMTByDQgCEgkvbS8wM3RqYngaKWoNCAISCS9tLzAzdGpieBIKMjAyNi0wMi0xNnINCAISCS9tLzA1cXRqGilqDQgCEgkvbS8wNXF0ahIKMjAyNi0wMy0zMHINCAISCS9tLzAzdGpieHABggELCP___________wFAAUgBmAEB",
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

**Contexte** : Requête multi-city 3 segments (Paris→Tokyo→Kyoto→Paris) avec filtres différents par segment :
- Segment 1 : Max 12h vol direct ou 1 escale (business trip, rapidité prioritaire)
- Segment 2 : Aucun filtre (loisir, flexibilité totale)
- Segment 3 : Min 1h30 layover si escale (confort, éviter stress connexions courtes)

---

**Exemple 2 : SearchRequest Sans Filtres (Backward Compatible Behavior)**

```json
{
  "template_url": "https://www.google.com/travel/flights?tfs=...",
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

**Contexte** : Requête sans aucun filtre appliqué (filters=null implicite), comportement équivalent ancien système Story 2-8, tous vols retournés.

---

**Exemple 3 : ValidationError Format Durée Invalide**

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

**Contexte** : Client envoie format durée invalide "1h3" (minutes doit être 2 chiffres "1h03"), ValidationError Pydantic avec message clair explicitant format attendu.

---

**Exemple 4 : ValidationError Backward Compatibility Rejection**

```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "segments_date_ranges"],
      "msg": "Extra inputs are not permitted",
      "input": [
        {"start": "2026-01-10", "end": "2026-01-18"}
      ]
    }
  ]
}
```

**Contexte** : Client envoie ancien format avec `segments_date_ranges`, ValidationError Pydantic rejette champ (ConfigDict extra="forbid"), guide migration via documentation CHANGELOG.md.

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

4. **Segment composition** : Segment encapsule `date_range: DateRange` (obligatoire) + `filters: SegmentFilters | None` (optionnel) avec validations propagées (vérifié DateRange invalid → ValidationError)

5. **SearchRequest breaking change** : Champ `segments_date_ranges` retiré, nouveau champ `segments: list[Segment]` requis, ancien format rejeté avec ValidationError extra="forbid" (vérifié tests intégration)

6. **SearchRequest validations migrées** : Validations existantes (2-5 segments, max 15 jours, chronologie, explosion combinatoire) fonctionnent sur `segments[i].date_range` (vérifié comportement inchangé Story 2-8)

7. **parse_duration conversion** : Convertit "12h" → 720 minutes, "1h30" → 90 minutes, lève ValueError si format invalide ou minutes ≥60 (vérifié tests unitaires)

8. **FilterService filtrage max_duration** : Exclut vols avec `parse_duration(flight.duration) > max_duration_minutes` (vérifié flight "14h" exclu si max "12h")

9. **FilterService filtrage max_stops** : Exclut vols avec `flight.stops > max_stops` (vérifié flight stops=2 exclu si max_stops=1)

10. **FilterService filtrage combiné** : Multiple filtres appliqués en AND logic, vol doit passer TOUS les filtres pour être inclus (vérifié tests combined filters)

11. **FilterService aucun match** : Si aucun vol ne passe filtres → retourne liste vide `[]` sans exception (vérifié comportement gracieux)

12. **FilterService filters None** : Si `filters=None` ou tous champs None → retourne `flights` inchangé (vérifié early return, aucun filtrage appliqué)

## Critères techniques

13. **Type hints PEP 695** : SegmentFilters, Segment, SearchRequest, parse_duration, FilterService annotés avec type hints modernes (`str | None`, `list[Segment]`, `list[GoogleFlightDTO]`)

14. **Pydantic v2 validations** : `field_validator` mode='after' sur champs SegmentFilters, validators réutilisent fonction `parse_duration` pour cohérence (vérifié validation pipeline)

15. **ConfigDict extra="forbid"** : SegmentFilters, Segment, SearchRequest rejettent champs inconnus avec ValidationError explicite (vérifié backward compatibility rejection)

16. **Regex compilation optimisée** : Regex `^\d{1,2}h(\d{2})?$` compilé une fois au niveau module pour performance (avoid re-compilation par validation)

17. **parse_duration pure function** : Pas de side-effects, retourne int ou lève ValueError, pas de logging interne (testabilité isolation)

18. **FilterService stateless** : Méthode `apply_filters` pure sans état interne, pas de mutation input `flights` liste (retourne nouvelle liste filtrée)

19. **Logging structuré JSON complet** : Logs filtrage incluent : segment_index, filters appliqués, flights_input/output counts, filter_efficiency % (format pythonjsonlogger)

20. **ValidationError messages clairs** : Messages UX-friendly avec exemples formats attendus ("Expected format: 'Xh' or 'XhYY' (e.g., '12h', '1h30')"), pas juste "invalid"

21. **min_layover feature flag** : min_layover skip avec log WARNING "not implemented yet" (future story), pas d'exception bloquante (dégradation gracieuse MVP)

## Critères qualité

22. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code SegmentFilters, Segment, parse_duration, FilterService apply_filters (pytest-cov)

23. **27 tests passent** : 22 tests unitaires (8 SegmentFilters + 3 Segment + 5 parse_duration + 6 FilterService) + 5 tests intégration tous verts (pytest -v)

24. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

25. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

26. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat), mocks SearchService configurés

27. **Docstrings 1 ligne** : SegmentFilters, Segment, parse_duration, FilterService avec docstring descriptive, focus POURQUOI pas QUOI

28. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON (pas d'implémentation complète)

29. **Documentation migration** : CHANGELOG.md contient section migration Story 8→9 avec exemples conversion ancien format → nouveau format, breaking change explicité

30. **Commits conventional** : Story 9 committée avec message `feat(filters): add per-segment filters (max_duration, max_stops, min_layover)` conforme Conventional Commits

---

**Note importante** : Story complexité moyenne (5 story points) → 30 critères couvrent exhaustivement architecture per-segment filters (12 fonctionnels incluant breaking change + min_layover feature flag), parsing durée résilient + validation Pydantic v2 (9 techniques), qualité tests TDD (9 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (regex format, limites 24h/12h/3 stops, breaking change rejection), **M**esurable (27 tests passent, coverage ≥80%, filtrage réduit ~20-40% vols), **A**tteignable (Pydantic v2 validation mature, regex standard Python), **R**elevant (filtres granulaires = valeur UX premium, foundation préférences utilisateur), **T**emporel (MVP Phase 5, après SearchRequest/GoogleFlightDTO Story 2-8 déjà implémentés).

**Breaking Change Impact** : ⚠️ **Remplacement `segments_date_ranges` → `segments`** nécessite coordination clients API pour migration :
1. Wrapper chaque `DateRange` dans objet `Segment` avec `date_range` key
2. Ajouter optionnel `filters` par segment si besoin
3. Tester avec nouveau format avant déploiement production

**Avantages** : Architecture scalable pour futurs filtres (preferred airlines, time windows, cabin class), UX premium compétitive vs agrégateurs (Kayak/Skyscanner parity), métriques comportement utilisateur observables (logs filtres appliqués).
