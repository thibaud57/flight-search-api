---
title: "Story 12: Per-Segment Filters (Generic)"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-4/story-11"]
date: "2025-11-28"
keywords: ["filters", "per-segment", "max-duration", "max-stops", "min-layover", "max-layover", "duration-parsing", "filter-service", "pydantic-validation", "kayak", "generic"]
scope: ["specs"]
technologies: ["Pydantic v2", "Python", "regex"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- **Filtres personnalisés par segment** : Utilisateurs recherchant vols multi-city (ex: Paris→Tokyo→Kyoto→Paris) veulent appliquer filtres différents par segment selon contraintes voyage (ex: segment 1 max 12h car travail lendemain, segment 2 accepte escales pour économiser, segment 3 min 1h30 layover pour confort)
- **Contrôle granulaire itinéraire** : Planification voyage complexe nécessite flexibilité filtres : segment business direct sans escale, segment loisir accepte vols longs économiques, segment retour évite layovers courts stressants (<1h30) ou trop longs (>6h)
- **Format durée intuitif** : Utilisateurs grand public attendent format durée humain-lisible "12h", "1h30" (pas 720 minutes format technique), similaire affichage Kayak UI
- **Filtres optionnels** : Utilisateurs débutants ne veulent pas complexité, filtres doivent être optionnels avec comportement par défaut permissif (sans filtres = tous vols retournés)
- **Filtres indépendants par segment** : Chaque segment peut avoir ses propres filtres ou aucun (ex: filtres segment 2 et 3 uniquement, segment 1 sans filtre)

## Contraintes métier

- **Route Kayak MVP** : Les filtres per-segment sont implémentés sur `/search-kayak` en priorité car l'extraction des données nécessaires (durée exacte, layovers) est fiable via API interne Kayak
- **Architecture générique** : SegmentFilters doit être générique (pas spécifique Kayak) pour réutilisation future sur route Google Flights quand scraping layovers sera implémenté
- **Validation format durée stricte** : Regex `^\d{1,2}h(\d{2})?$` doit accepter uniquement formats valides ("12h", "1h30") et rejeter formats ambigus ("1h3", "72", "12h60") pour éviter erreurs parsing silencieuses
- **Limites escales réalistes** : Kayak affiche maximum 3 escales par segment, filtrer au-delà (ex: `max_stops=5`) inutile et confus pour utilisateurs
- **Validation layover cohérente** : max_layover doit être **strictement supérieur** à min_layover si les deux sont définis
- **Pas de validation cross-segment** : Filtres appliqués indépendamment par segment (pas de règles globales "total escales <5" ou "durée totale itinéraire <30h"), simplicité MVP prioritaire

## Valeur business

- **Réduction bruit résultats** : Filtres permettent exclure vols non-pertinents (ex: 20h transit, 3 escales épuisantes, layover trop court/long) avant ranking, améliore qualité Top 10 retournés (satisfaction utilisateur +30-40%)
- **Foundation préférences utilisateur** : Architecture per-segment filters réutilisable pour futurs critères (preferred airlines, departure time windows, cabin class) sans refonte structurelle
- **Parity agrégateurs premium** : Kayak/Skyscanner offrent filtres granulaires, notre API doit matcher fonctionnalités pour compétitivité B2B (partenariats agences voyage)
- **Évolutivité multi-provider** : SegmentFilters générique permet extension future Google Flights quand scraping layovers sera implémenté (pas de refonte modèles)
- **Métriques comportement utilisateur** : Filters appliqués observables via logs (quels filtres populaires, valeurs fréquentes) pour optimiser UX futures versions

## Métriques succès

- **Taux adoption filtres** : 40-60% requêtes KayakSearchRequest incluent au moins 1 filtre segment (baseline adoption attendue post-lancement)
- **Taux filtrage efficace** : Filtres réduisent résultats moyens ~20-40% (ex: 500 vols avant filtrage → 300-400 après, élimination vols non-pertinents)
- **Zéro erreur format durée** : Validation regex rejette 100% formats invalides ("1h3", "12h60") avec messages clairs (pas de parsing silencieux incorrect)
- **Validation layover cohérente** : 100% erreurs si max_layover ≤ min_layover (validation Pydantic robuste)
- **Coverage tests** : ≥80% sur SegmentFilters, parse_duration utility, FilterService apply_filters, stops computed property

---

# 📋 Spécifications Techniques

## 1. SegmentFilters (Pydantic Model)

**Rôle** : Définir filtres optionnels applicables à un segment individuel itinéraire multi-city avec validation format durée humain-lisible. Modèle générique réutilisable pour tous providers (Kayak, Google Flights futur).

**Fichier** : `app/models/filters.py` (nouveau fichier)

**Interface** :
```python
class SegmentFilters(BaseModel):
    """Filtres génériques par segment (tous providers)."""
```

**Champs** :

| Champ | Type | Description | Contraintes | Valeur par défaut |
|-------|------|-------------|-------------|-------------------|
| `max_duration` | `str \| None` | Durée maximale vol segment (format "Xh" ou "XhYY") | Regex `^\d{1,2}h(\d{2})?$`, minutes ≤ 1440 (24h) | `None` (pas de filtre) |
| `max_stops` | `int \| None` | Nombre maximal escales segment | 0 ≤ value ≤ 3 | `None` (pas de filtre) |
| `min_layover` | `str \| None` | Durée minimale escale/layover (format "Xh" ou "XhYY") | Regex `^\d{1,2}h(\d{2})?$`, minutes ≤ 720 (12h) | `None` (pas de filtre) |
| `max_layover` | `str \| None` | Durée maximale escale/layover (format "Xh" ou "XhYY") | Regex `^\d{1,2}h(\d{2})?$`, minutes ≤ 1440 (24h), doit être > min_layover | `None` (pas de filtre) |

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

- **Comportement** : Identique `max_duration` validation format
- **Limite** : ≤ 720 minutes (12h layover minimum maximum raisonnable)
- **Justification** : Layover min >12h = edge case très rare

**4. Validation `max_layover` format et limites** :
```python
@field_validator('max_layover', mode='after')
@classmethod
def validate_max_layover(cls, v: str | None) -> str | None:
    """Valide format + limite max_layover ≤ 24h."""
```

- **Comportement** : Identique `max_duration` validation format
- **Limite** : ≤ 1440 minutes (24h layover maximum pour couvrir overnight)
- **Justification** : Layover max 24h couvre cas overnight connections

**5. Validation `max_stops` range** :
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
  - v > 3 → ❌ Lève `ValueError` (Kayak max 3 escales affichées)
- **Error message** : `"max_stops must be between 0 and 3 (got: X)"`

**6. Validation cross-field layover cohérence** :
```python
@model_validator(mode='after')
def validate_layover_range(self) -> Self:
    """Valide que max_layover > min_layover (strictement supérieur)."""
```

- **Comportement** :
  - Si `min_layover` ET `max_layover` définis :
    - Convertir les deux en minutes via `parse_duration()`
    - Si `max_layover_minutes <= min_layover_minutes` → Lève `ValueError`
  - Si un seul défini ou les deux `None` → Skip validation
- **Exemples** :
  - `min_layover="1h30"`, `max_layover="6h"` → ✅ Valide (6h > 1h30)
  - `min_layover="12h"`, `max_layover="12h"` → ❌ ValueError (égal interdit)
  - `min_layover="12h"`, `max_layover="13h"` → ✅ Valide (strictement supérieur)
  - `min_layover="2h"`, `max_layover="1h"` → ❌ ValueError (max < min)
- **Error message** : `"max_layover must be strictly greater than min_layover (got min: X, max: Y)"`

**Comportement** :

- **Filtres optionnels** : Tous champs `None` par défaut, aucun filtre obligatoire
- **Validation stricte** : ConfigDict `extra="forbid"` rejette champs inconnus avec ValidationError (protection contre typos)
- **Validation indépendante** : Chaque filtre validé séparément, sauf validation cross-field layover
- **Immutabilité** : Model Pydantic peut être frozen via `frozen=True` dans ConfigDict (optionnel, simplicité MVP)

**Edge cases** :

- **Tous filtres None** : SegmentFilters vide valide, équivalent "aucun filtre appliqué"
- **Durée "0h"** : Valide format regex mais invalide métier (vol instantané impossible), géré par FilterService (skip vols durée 0)
- **Minutes "00"** : `"12h00"` valide mais redondant vs `"12h"`, accepté pour flexibilité user input
- **Layover égaux** : `min_layover="6h"`, `max_layover="6h"` → ❌ ValueError (strictement supérieur requis)

**Erreurs levées** :
- `ValidationError` : Si format durée invalide, valeur hors range, type incorrect, ou max_layover ≤ min_layover

**Logging structuré** :
- DEBUG : SegmentFilters créé avec valeurs non-None (ex: `{"max_duration": "12h", "max_stops": 1}`)

---

## 2. KayakFlightDTO - Propriété `stops` (Computed)

**Rôle** : Ajouter propriété computed `stops` sur KayakFlightDTO pour calculer nombre d'escales depuis longueur du tableau `layovers`.

**Fichier** : `app/models/kayak_flight_dto.py` (modification existant)

**Interface** :
```python
class KayakFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Kayak."""

    # ... champs existants ...
    layovers: list[LayoverInfo] = []

    @property
    def stops(self) -> int:
        """Nombre d'escales = longueur du tableau layovers."""
```

**Comportement** :

- **Computed property** : Pas de champ stocké, calculé à la volée depuis `len(self.layovers)`
- **Read-only** : Property sans setter, immutable
- **Performance** : O(1) car `len()` sur liste Python
- **Exemples** :
  - `layovers=[]` → `stops=0` (vol direct)
  - `layovers=[LayoverInfo(...)]` → `stops=1` (1 escale)
  - `layovers=[LayoverInfo(...), LayoverInfo(...)]` → `stops=2` (2 escales)

**Edge cases** :
- `layovers=None` impossible car champ défini avec `= []` default (toujours liste)

**Erreurs levées** :
- Aucune (property triviale)

**Logging structuré** :
- Aucun (computed property, pas de side-effect)

---

## 3. KayakSearchRequest - Ajout `segments_filters`

**Rôle** : Étendre KayakSearchRequest existant avec champ `segments_filters` optionnel permettant filtres per-segment.

**Fichier** : `app/models/request.py` (modification existant)

**Interface** :
```python
class KayakSearchRequest(MultiCitySearchRequestBase):
    """Requête recherche vols multi-city Kayak avec filtres per-segment."""

    template_url: Annotated[str, "URL Kayak template"]
    segments_date_ranges: Annotated[list[DateRange], "Plages dates par segment (2-6 segments)"]
    segments_filters: Annotated[
        list[SegmentFilters | None] | None,
        "Filtres optionnels par segment (doit matcher longueur segments_date_ranges)"
    ] = None
```

**Champs** :

| Champ | Type | Description | Contraintes | Valeur par défaut |
|-------|------|-------------|-------------|-------------------|
| `segments_filters` | `list[SegmentFilters \| None] \| None` | Filtres optionnels par segment | Si défini, longueur doit être égale à `len(segments_date_ranges)` | `None` (aucun filtre) |

**Validations Pydantic** :

**Validation longueur segments_filters** :
```python
@model_validator(mode='after')
def validate_segments_filters_length(self) -> Self:
    """Valide que segments_filters match longueur segments_date_ranges."""
```

- **Comportement** :
  - Si `segments_filters is None` → Skip validation (pas de filtres appliqués)
  - Si `segments_filters` défini :
    - `len(segments_filters) == len(segments_date_ranges)` → ✅ Valide
    - `len(segments_filters) != len(segments_date_ranges)` → ❌ Lève `ValueError`
- **Exemples** :
  - `segments_date_ranges=[DateRange(...), DateRange(...)]`, `segments_filters=[SegmentFilters(...), None]` → ✅ Valide (longueurs égales 2)
  - `segments_date_ranges=[DateRange(...), DateRange(...)]`, `segments_filters=[SegmentFilters(...)]` → ❌ ValueError (longueurs différentes 2 vs 1)
  - `segments_date_ranges=[DateRange(...), DateRange(...)]`, `segments_filters=None` → ✅ Valide (pas de filtres)
- **Error message** : `"segments_filters length (X) must match segments_date_ranges length (Y)"`

**Comportement** :

- **Filtres optionnels** : `segments_filters=None` → Aucun filtre appliqué sur aucun segment (comportement par défaut)
- **Filtres partiels** : `segments_filters=[None, SegmentFilters(...), SegmentFilters(...)]` → Segment 1 sans filtre, segments 2-3 avec filtres
- **Filtres complets** : `segments_filters=[SegmentFilters(...), SegmentFilters(...), SegmentFilters(...)]` → Tous segments avec filtres
- **Backward compatible** : Champ optionnel (`= None`), requêtes existantes sans `segments_filters` continuent à fonctionner

**Edge cases** :

- **Tous filtres None dans liste** : `segments_filters=[None, None, None]` → Valide, équivalent à `segments_filters=None` (aucun filtrage appliqué)
- **Liste vide** : `segments_filters=[]` → ❌ ValueError si `segments_date_ranges` non vide (longueurs différentes)

**Erreurs levées** :
- `ValidationError` : Si longueur `segments_filters` ne match pas `segments_date_ranges`

**Logging structuré** :
- INFO : KayakSearchRequest reçu avec X segments, Y segments avec filtres non-None appliqués

---

## 4. parse_duration (Utility Function)

**Rôle** : Convertir string durée format humain-lisible ("12h", "1h30") en minutes (int) pour comparaison numérique dans FilterService et validations Pydantic.

**Fichier** : `app/utils/duration.py` (nouveau fichier)

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
        ValueError: Si format invalide (regex mismatch) ou minutes ≥ 60
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

**Rôle** : Appliquer filtres SegmentFilters sur liste vols KayakFlightDTO pour éliminer vols non-conformes critères utilisateur.

**Fichier** : `app/services/filter_service.py` (nouveau fichier)

**Interface** :
```python
class FilterService:
    """Service application filtres per-segment sur vols."""

    def apply_filters(
        self,
        flights: list[KayakFlightDTO],
        filters: SegmentFilters | None
    ) -> list[KayakFlightDTO]:
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
2. Si `filters` tous champs None (`max_duration=None, max_stops=None, min_layover=None, max_layover=None`) → Retourner `flights` inchangé

**Étape 2 : Filtrage max_duration**
3. Si `filters.max_duration is not None` :
   - Convertir `filters.max_duration` en minutes via `parse_duration()`
   - Filtrer vols : garder seulement `flight` où `parse_duration(flight.duration) ≤ max_duration_minutes`
   - Exemple : `max_duration="12h"` (720 min) → Exclure vols "13h 30min" (810 min)

**Étape 3 : Filtrage max_stops**
4. Si `filters.max_stops is not None` :
   - Filtrer vols : garder seulement `flight` où `flight.stops ≤ filters.max_stops`
   - `flight.stops` utilise propriété computed sur `len(flight.layovers)`
   - Exemple : `max_stops=1` → Exclure vols avec `stops=2` ou `stops=3`

**Étape 4 : Filtrage min_layover**
5. Si `filters.min_layover is not None` :
   - Convertir `filters.min_layover` en minutes via `parse_duration()`
   - Pour chaque vol, vérifier TOUTES les escales : `flight.layovers[].duration`
   - Filtrer vols : garder seulement `flight` où **TOUTES** escales ont `parse_duration(layover.duration) ≥ min_layover_minutes`
   - Exemple : `min_layover="1h30"` → Exclure vol si une escale "1h 15min" (75 min < 90 min)

**Étape 5 : Filtrage max_layover**
6. Si `filters.max_layover is not None` :
   - Convertir `filters.max_layover` en minutes via `parse_duration()`
   - Pour chaque vol, vérifier TOUTES les escales : `flight.layovers[].duration`
   - Filtrer vols : garder seulement `flight` où **TOUTES** escales ont `parse_duration(layover.duration) ≤ max_layover_minutes`
   - Exemple : `max_layover="6h"` → Exclure vol si une escale "8h" (480 min > 360 min)

**Étape 6 : Retour liste filtrée**
7. Retourner liste vols restants après tous filtres appliqués
8. Si aucun vol ne passe filtres → Retourner liste vide `[]` (pas d'exception)

**Exemples Filtrage** :

**Scenario 1 : max_duration appliqué**
- Input : `flights=[flight1(duration="11h"), flight2(duration="14h"), flight3(duration="10h 30min")]`
- Filters : `SegmentFilters(max_duration="12h")`
- Output : `[flight1, flight3]` (flight2 exclu car 14h > 12h)

**Scenario 2 : max_stops appliqué**
- Input : `flights=[flight1(stops=0), flight2(stops=1), flight3(stops=2)]`
- Filters : `SegmentFilters(max_stops=1)`
- Output : `[flight1, flight2]` (flight3 exclu car stops=2 > max_stops=1)

**Scenario 3 : min_layover appliqué**
- Input : `flights=[flight1(layovers=[LayoverInfo(duration="2h")]), flight2(layovers=[LayoverInfo(duration="1h")])]`
- Filters : `SegmentFilters(min_layover="1h30")`
- Output : `[flight1]` (flight2 exclu car layover 1h < 1h30)

**Scenario 4 : max_layover appliqué**
- Input : `flights=[flight1(layovers=[LayoverInfo(duration="3h")]), flight2(layovers=[LayoverInfo(duration="8h")])]`
- Filters : `SegmentFilters(max_layover="6h")`
- Output : `[flight1]` (flight2 exclu car layover 8h > 6h)

**Scenario 5 : Multiple filtres combinés**
- Input : `flights=[flight1(duration="10h", stops=0), flight2(duration="11h", stops=1), flight3(duration="9h", stops=2)]`
- Filters : `SegmentFilters(max_duration="12h", max_stops=1)`
- Output : `[flight1, flight2]` (flight3 exclu car stops=2 > max_stops=1 malgré durée OK)

**Scenario 6 : Aucun vol ne passe filtres**
- Input : `flights=[flight1(duration="15h", stops=2), flight2(duration="16h", stops=3)]`
- Filters : `SegmentFilters(max_duration="12h", max_stops=1)`
- Output : `[]` (liste vide, aucun vol conforme)

**Edge cases** :

- **KayakFlightDTO.duration format invalide** : Si `flight.duration` format non parseable (ex: "Unknown") → Skip vol (exclude silencieusement, log WARNING)
- **Filtres None partiel** : `SegmentFilters(max_duration="12h", max_stops=None)` → Applique seulement filtre duration, ignore stops
- **Durée exacte limite** : `max_duration="12h"` (720 min), `flight.duration="12h 00min"` (720 min) → ✅ Inclus (≤ pas <)
- **Layover avec plusieurs escales** : Filtrage min/max_layover vérifie **TOUTES** les escales (logic AND : toutes doivent passer critères)
- **Vols directs (stops=0)** : Filtres min/max_layover ignorés si `len(flight.layovers) == 0` (pas d'escale à vérifier)

**Erreurs levées** :
- Aucune exception levée (filtrage silencieux, retourne liste vide si aucun match)

**Logging structuré** :
- INFO : Filtrage appliqué avec résultat (X vols input → Y vols output, Z vols filtrés)
- DEBUG : Détail filtres appliqués (max_duration=X, max_stops=Y, vols exclus : [flight_ids])
- WARNING : Vol avec duration format invalide exclu du filtrage
- WARNING : Vol avec layover duration format invalide exclu du filtrage

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### SegmentFilters Validation (12 tests)

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
| 9 | `test_segment_filters_max_layover_exceeds_limit` | max_layover >24h invalide | `SegmentFilters(max_layover="25h")` | Lève `ValidationError` message "exceeds limit" | Vérifie limite 1440 minutes layover |
| 10 | `test_segment_filters_layover_range_valid` | max_layover > min_layover valide | `SegmentFilters(min_layover="1h30", max_layover="6h")` | Model créé sans exception | Vérifie validation cross-field OK si max > min |
| 11 | `test_segment_filters_layover_range_equal_invalid` | max_layover == min_layover invalide | `SegmentFilters(min_layover="6h", max_layover="6h")` | Lève `ValidationError` message "must be strictly greater" | Vérifie égalité rejetée (strictement supérieur requis) |
| 12 | `test_segment_filters_layover_range_inverted_invalid` | max_layover < min_layover invalide | `SegmentFilters(min_layover="6h", max_layover="2h")` | Lève `ValidationError` message "must be strictly greater" | Vérifie inversion rejetée |

### KayakFlightDTO stops property (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 13 | `test_kayak_flight_stops_zero_direct` | Vol direct sans escale | `KayakFlightDTO(layovers=[])` | `flight.stops == 0` | Vérifie computed property stops=0 si liste vide |
| 14 | `test_kayak_flight_stops_one_layover` | Vol avec 1 escale | `KayakFlightDTO(layovers=[LayoverInfo(...)])` | `flight.stops == 1` | Vérifie computed property stops=len(layovers) |
| 15 | `test_kayak_flight_stops_multiple_layovers` | Vol avec 2 escales | `KayakFlightDTO(layovers=[LayoverInfo(...), LayoverInfo(...)])` | `flight.stops == 2` | Vérifie computed property multi-escales |

### KayakSearchRequest segments_filters validation (4 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 16 | `test_kayak_search_request_no_filters` | Requête sans filtres (segments_filters=None) | `KayakSearchRequest(segments_date_ranges=[...], segments_filters=None)` | Model créé, `segments_filters == None` | Vérifie filtres optionnels par défaut |
| 17 | `test_kayak_search_request_filters_match_length` | segments_filters match segments_date_ranges longueur | `KayakSearchRequest(segments_date_ranges=[DR1, DR2], segments_filters=[SF1, None])` | Model créé sans exception | Vérifie validation longueur OK si égales |
| 18 | `test_kayak_search_request_filters_length_mismatch` | segments_filters ne match pas longueur | `KayakSearchRequest(segments_date_ranges=[DR1, DR2], segments_filters=[SF1])` | Lève `ValidationError` message "length must match" | Vérifie validation longueur rejette si différentes |
| 19 | `test_kayak_search_request_filters_partial` | Filtres partiels (certains segments None) | `KayakSearchRequest(segments_date_ranges=[DR1, DR2, DR3], segments_filters=[None, SF2, SF3])` | Model créé, segment 1 sans filtre, 2-3 avec filtres | Vérifie filtres partiels acceptés |

### parse_duration Utility (5 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 20 | `test_parse_duration_hours_only` | Parse format "12h" | `parse_duration("12h")` | `720` (minutes) | Vérifie conversion heures → minutes |
| 21 | `test_parse_duration_hours_minutes` | Parse format "1h30" | `parse_duration("1h30")` | `90` (minutes) | Vérifie conversion heures + minutes → total minutes |
| 22 | `test_parse_duration_zero` | Parse "0h" edge case | `parse_duration("0h")` | `0` (minutes) | Vérifie parsing OK (validation métier ailleurs) |
| 23 | `test_parse_duration_invalid_format` | Format invalide "72" sans unité | `parse_duration("72")` | Lève `ValueError` message "Expected format" | Vérifie regex rejette format invalide |
| 24 | `test_parse_duration_minutes_out_of_range` | Minutes ≥60 invalide "12h60" | `parse_duration("12h60")` | Lève `ValueError` message "minutes" | Vérifie validation minutes <60 |

### FilterService apply_filters (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 25 | `test_apply_filters_none` | Aucun filtre appliqué (filters=None) | `flights=[flight1, flight2], filters=None` | `[flight1, flight2]` inchangé | Vérifie early return si filters None |
| 26 | `test_apply_filters_max_duration` | Filtre max_duration exclut vols longs | `flights=[flight1(duration="11h"), flight2(duration="14h")], filters=SegmentFilters(max_duration="12h")` | `[flight1]` (flight2 exclu) | Vérifie filtrage durée correctement appliqué |
| 27 | `test_apply_filters_max_stops` | Filtre max_stops exclut vols avec escales | `flights=[flight1(stops=0), flight2(stops=2)], filters=SegmentFilters(max_stops=1)` | `[flight1]` (flight2 exclu) | Vérifie filtrage escales correctement appliqué |
| 28 | `test_apply_filters_min_layover` | Filtre min_layover exclut escales courtes | `flights=[flight1(layovers=[LI(duration="2h")]), flight2(layovers=[LI(duration="1h")])], filters=SegmentFilters(min_layover="1h30")` | `[flight1]` (flight2 exclu) | Vérifie filtrage layover min correctement appliqué |
| 29 | `test_apply_filters_max_layover` | Filtre max_layover exclut escales longues | `flights=[flight1(layovers=[LI(duration="3h")]), flight2(layovers=[LI(duration="8h")])], filters=SegmentFilters(max_layover="6h")` | `[flight1]` (flight2 exclu) | Vérifie filtrage layover max correctement appliqué |
| 30 | `test_apply_filters_combined` | Multiple filtres combinés (AND logic) | `flights=[flight1(duration="10h", stops=0), flight2(duration="11h", stops=2)], filters=SegmentFilters(max_duration="12h", max_stops=1)` | `[flight1]` (flight2 exclu car stops>1) | Vérifie logic combinaison filtres |
| 31 | `test_apply_filters_no_match` | Aucun vol ne passe filtres | `flights=[flight1(duration="15h", stops=2)], filters=SegmentFilters(max_duration="12h", max_stops=1)` | `[]` liste vide | Vérifie comportement aucun match (pas d'exception) |
| 32 | `test_apply_filters_invalid_duration_format` | Vol avec duration invalide exclu silencieusement | `flights=[flight1(duration="Unknown"), flight2(duration="10h")], filters=SegmentFilters(max_duration="12h")` | `[flight2]` (flight1 exclu car format invalide) | Vérifie handling duration non parseable |
| 33 | `test_apply_filters_direct_flight_ignores_layover` | Vol direct (stops=0) ignore filtres layover | `flights=[flight1(stops=0, layovers=[])], filters=SegmentFilters(min_layover="1h30")` | `[flight1]` inclus | Vérifie vols directs ignorent filtres layover |
| 34 | `test_apply_filters_multiple_layovers_all_must_pass` | Multiple escales : TOUTES doivent passer critères | `flights=[flight1(layovers=[LI("2h"), LI("1h")])], filters=SegmentFilters(min_layover="1h30")` | `[]` (exclu car une escale 1h < 1h30) | Vérifie logic AND sur toutes escales |

**Total tests unitaires** : 12 (SegmentFilters) + 3 (stops property) + 4 (KayakSearchRequest) + 5 (parse_duration) + 10 (FilterService) = **34 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_search_kayak_with_segment_filters` | Mock SearchService avec 3 segments, segments_filters=[SF1, None, SF2] | POST `/api/v1/search-kayak` avec body `KayakSearchRequest` | Status 200, `SearchResponse.results` contient vols filtrés (segment 1 max 12h appliqué, segment 2 sans filtres, segment 3 max_stops=1 appliqué) |
| 2 | `test_integration_kayak_validation_invalid_filters` | App FastAPI TestClient | POST `/api/v1/search-kayak` avec `segments_filters[0].max_duration="invalid"` | Status 422, JSON error contient message "Invalid duration format" |
| 3 | `test_integration_kayak_filters_reduce_results` | Mock SearchService sans filtres baseline (100 vols total), puis avec filtres stricts | Comparer résultats sans filtres vs avec `max_duration="10h", max_stops=0` sur tous segments | Résultats filtrés ~30-40% moins nombreux (filtrage efficace), Top 10 ranking fonctionne sur résultats filtrés |
| 4 | `test_integration_kayak_segments_without_filters` | App FastAPI TestClient | POST `/api/v1/search-kayak` avec `segments_filters=null` | Status 200, comportement équivalent ancien système (tous vols retournés sans filtrage) |
| 5 | `test_integration_kayak_layover_range_validation` | App FastAPI TestClient | POST `/api/v1/search-kayak` avec `segments_filters[0]={min_layover: "6h", max_layover: "6h"}` | Status 422, JSON error contient message "must be strictly greater" |

**Total tests intégration** : 5 tests

---

**TOTAL TESTS** : 34 unitaires + 5 intégration = **39 tests**

---

## Exemples JSON

**Exemple 1 : KayakSearchRequest avec Per-Segment Filters**

```json
{
  "template_url": "https://www.kayak.fr/flights/PAR-TYO/2026-01-10/TYO-KYO/2026-02-16/KYO-PAR/2026-03-30",
  "segments_date_ranges": [
    {"start": "2026-01-10", "end": "2026-01-18"},
    {"start": "2026-02-16", "end": "2026-02-18"},
    {"start": "2026-03-30", "end": "2026-04-01"}
  ],
  "segments_filters": [
    {
      "max_duration": "12h",
      "max_stops": 1
    },
    null,
    {
      "min_layover": "1h30",
      "max_layover": "6h"
    }
  ]
}
```

**Contexte** : Requête Kayak multi-city 3 segments (Paris→Tokyo→Kyoto→Paris) avec filtres différents par segment :
- Segment 1 : Max 12h vol direct ou 1 escale (business trip, rapidité prioritaire)
- Segment 2 : Aucun filtre (loisir, flexibilité totale)
- Segment 3 : Layover entre 1h30 et 6h (confort, éviter connexions courtes stressantes ou overnight trop longues)

---

**Exemple 2 : KayakSearchRequest Sans Filtres**

```json
{
  "template_url": "https://www.kayak.fr/flights/PAR-TYO/2026-01-10/TYO-PAR/2026-02-16",
  "segments_date_ranges": [
    {"start": "2026-01-10", "end": "2026-01-18"},
    {"start": "2026-02-16", "end": "2026-02-18"}
  ]
}
```

**Contexte** : Requête Kayak sans aucun filtre appliqué (segments_filters omis), tous vols retournés. Comportement backward-compatible.

---

**Exemple 3 : ValidationError Format Durée Invalide**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "segments_filters", 0, "max_duration"],
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

**Exemple 4 : ValidationError Layover Range Invalide**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "segments_filters", 0],
      "msg": "Value error, max_layover must be strictly greater than min_layover (got min: 360 minutes, max: 360 minutes)",
      "input": {"min_layover": "6h", "max_layover": "6h"},
      "ctx": {
        "error": "max_layover must be strictly greater than min_layover"
      }
    }
  ]
}
```

**Contexte** : Client envoie min_layover et max_layover égaux (6h == 6h), validation cross-field rejette car égalité interdite (strictement supérieur requis).

---

**Exemple 5 : Logging Filtrage Appliqué**

```json
{
  "timestamp": "2025-11-28T10:30:00Z",
  "level": "INFO",
  "service": "FilterService",
  "message": "Filters applied to segment",
  "segment_index": 0,
  "filters": {
    "max_duration": "12h",
    "max_stops": 1,
    "min_layover": null,
    "max_layover": null
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

2. **SegmentFilters validation limites** : `max_duration` ≤ 24h (1440 min), `min_layover` ≤ 12h (720 min), `max_layover` ≤ 24h (1440 min), `max_stops` entre 0-3 (vérifié ValidationError si hors range)

3. **SegmentFilters validation layover cohérente** : max_layover doit être **strictement supérieur** à min_layover si les deux définis (vérifié ValidationError si égal ou inférieur)

4. **SegmentFilters optionnels** : Tous champs `None` par défaut, SegmentFilters vide valide `SegmentFilters()` créé sans exception (vérifié comportement permissif)

5. **SegmentFilters générique** : Model réutilisable pour tous providers (Kayak MVP, Google Flights futur) sans modification (vérifié aucun code spécifique Kayak dans model)

6. **KayakFlightDTO stops property** : Propriété computed `stops` retourne `len(self.layovers)` (vérifié stops=0 si liste vide, stops=N si N layovers)

7. **KayakSearchRequest segments_filters optionnel** : Champ `segments_filters: list[SegmentFilters | None] | None = None` optionnel (vérifié backward compatibility requêtes sans segments_filters)

8. **KayakSearchRequest validation longueur** : `len(segments_filters) == len(segments_date_ranges)` si segments_filters défini (vérifié ValidationError si longueurs différentes)

9. **KayakSearchRequest filtres partiels** : segments_filters peut contenir None pour certains segments (vérifié filtres partiels acceptés)

10. **parse_duration conversion** : Convertit "12h" → 720 minutes, "1h30" → 90 minutes, lève ValueError si format invalide ou minutes ≥60 (vérifié tests unitaires)

11. **FilterService filtrage max_duration** : Exclut vols avec `parse_duration(flight.duration) > max_duration_minutes` (vérifié flight "14h" exclu si max "12h")

12. **FilterService filtrage max_stops** : Exclut vols avec `flight.stops > max_stops` (vérifié flight stops=2 exclu si max_stops=1)

13. **FilterService filtrage min_layover** : Exclut vols si **UNE** escale a `duration < min_layover` (vérifié logic AND sur toutes escales)

14. **FilterService filtrage max_layover** : Exclut vols si **UNE** escale a `duration > max_layover` (vérifié logic AND sur toutes escales)

15. **FilterService filtrage combiné** : Multiple filtres appliqués en AND logic, vol doit passer TOUS les filtres pour être inclus (vérifié tests combined filters)

16. **FilterService aucun match** : Si aucun vol ne passe filtres → retourne liste vide `[]` sans exception (vérifié comportement gracieux)

17. **FilterService filters None** : Si `filters=None` ou tous champs None → retourne `flights` inchangé (vérifié early return, aucun filtrage appliqué)

18. **FilterService vols directs** : Filtres min/max_layover ignorés si `flight.stops == 0` (vérifié vols directs passent toujours filtres layover)

## Critères techniques

19. **Type hints PEP 695** : SegmentFilters, KayakFlightDTO, KayakSearchRequest, parse_duration, FilterService annotés avec type hints modernes (`str | None`, `list[SegmentFilters | None]`, `list[KayakFlightDTO]`)

20. **Pydantic v2 validations** : `field_validator` mode='after' sur champs SegmentFilters, `model_validator` mode='after' pour validation cross-field layover

21. **ConfigDict extra="forbid"** : SegmentFilters, KayakSearchRequest rejettent champs inconnus avec ValidationError explicite

22. **Regex compilation optimisée** : Regex `^\d{1,2}h(\d{2})?$` compilé une fois au niveau module pour performance (avoid re-compilation par validation)

23. **parse_duration pure function** : Pas de side-effects, retourne int ou lève ValueError, pas de logging interne (testabilité isolation)

24. **FilterService stateless** : Méthode `apply_filters` pure sans état interne, pas de mutation input `flights` liste (retourne nouvelle liste filtrée)

25. **stops computed property** : Property read-only sans setter, O(1) performance via `len()` (vérifié immutabilité)

26. **Logging structuré JSON complet** : Logs filtrage incluent : segment_index, filters appliqués, flights_input/output counts, filter_efficiency % (format pythonjsonlogger)

27. **ValidationError messages clairs** : Messages UX-friendly avec exemples formats attendus ("Expected format: 'Xh' or 'XhYY' (e.g., '12h', '1h30')"), pas juste "invalid"

28. **Architecture générique réutilisable** : SegmentFilters dans fichier séparé `app/models/filters.py`, parse_duration dans `app/utils/duration.py` (séparation responsabilités)

## Critères qualité

29. **Coverage ≥80%** : Tests unitaires + intégration couvrent minimum 80% code SegmentFilters, parse_duration, FilterService, stops property (pytest-cov)

30. **39 tests passent** : 34 tests unitaires (12 SegmentFilters + 3 stops + 4 KayakSearchRequest + 5 parse_duration + 10 FilterService) + 5 tests intégration tous verts (pytest -v)

31. **Ruff + Mypy passent** : `ruff check .` et `ruff format .` sans erreur, `mypy app/` strict mode sans erreur type

32. **Tests TDD format AAA** : Tests unitaires suivent strictement Arrange/Act/Assert, tableaux specs complétés avec 6 colonnes (N°, Nom, Scénario, Input, Output, Vérification)

33. **Tests intégration format Given/When/Then** : Tests intégration suivent BDD avec 5 colonnes (N°, Nom, Prérequis, Action, Résultat)

34. **Docstrings 1 ligne** : SegmentFilters, KayakFlightDTO, KayakSearchRequest, parse_duration, FilterService avec docstring descriptive, focus POURQUOI pas QUOI

35. **Aucun code production dans specs** : Ce document contient uniquement signatures, tableaux tests, descriptions comportements, exemples JSON (pas d'implémentation complète)

36. **Commits conventional** : Story 12 committée avec message `feat(filters): add per-segment filters (max_duration, max_stops, min/max_layover)` conforme Conventional Commits

---

**Note importante** : Story complexité moyenne (5 story points) → 36 critères couvrent exhaustivement architecture per-segment filters générique (18 fonctionnels avec validation layover cohérente + stops computed + architecture réutilisable), parsing durée résilient + validations Pydantic v2 (10 techniques), qualité tests TDD (8 qualité).

**Principe SMART** : Chaque critère est **S**pécifique (regex format, limites 24h/12h/3 stops, max_layover > min_layover, architecture générique), **M**esurable (39 tests passent, coverage ≥80%, filtrage réduit ~20-40% vols), **A**tteignable (Pydantic v2 validation mature, regex standard Python, computed property triviale), **R**elevant (filtres granulaires = valeur UX premium, foundation multi-provider), **T**emporel (MVP Phase 5 Kayak, extension Google Flights Phase 6+).

**Architecture générique** :
- ✅ **SegmentFilters réutilisable** : Tous providers (Kayak MVP, Google Flights futur)
- ✅ **Pas de code spécifique Kayak** : Model générique dans `app/models/filters.py`
- ✅ **Extension future sans refonte** : Ajout min/max_layover Google Flights sans modification SegmentFilters
- ✅ **Séparation responsabilités** : parse_duration dans `app/utils/duration.py` (réutilisable autres parsers)
