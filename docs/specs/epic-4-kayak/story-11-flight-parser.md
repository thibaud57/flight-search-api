---
title: "Story 11: KayakFlightParser"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-4/story-10"]
date: "2025-25-11"
keywords: ["kayak", "parser", "json", "segments", "legs", "results", "denormalization", "GoogleFlightDTO"]
scope: ["specs"]
technologies: ["Python", "Pydantic v2", "JSON"]
---

# 🎯 Contexte Business

## Besoin utilisateur
- Parser les données JSON capturées depuis l'API interne Kayak (via network capture)
- Extraire les informations des vols depuis une structure dénormalisée complexe (results → legs → segments)
- Convertir les données Kayak vers le format unifié GoogleFlightDTO pour compatibilité avec le reste de l'API

## Contraintes métier
- **Structure JSON non documentée** : API interne Kayak peut évoluer sans préavis
- **Dénormalisation complexe** : Les données sont réparties en 3 dictionnaires (results, legs, segments) avec références par ID
- **Robustesse requise** : Parser doit gérer les champs manquants ou null gracieusement
- **Performance** : Dénormalisation de N résultats doit être rapide (< 100ms pour 50 résultats)

## Valeur business
- ✅ Extraction fiable des données Kayak pour recherches multi-city complexes
- ✅ Unification format Google Flights + Kayak = API unique pour client
- ✅ Résilience face aux évolutions structure JSON Kayak (defaults intelligents)
- ✅ Foundation pour intégration future d'autres sources (Skyscanner, Kiwi)

## Métriques succès
- **Taux de parsing réussi** : ≥ 95% des réponses Kayak valides parsées correctement
- **Temps de parsing** : < 100ms pour 50 résultats (dénormalisation complète)
- **Coverage tests** : ≥ 90% sur module parser
- **Robustesse** : Gestion de 100% des champs optionnels sans crash

---

# 📋 Spécifications Techniques

## 1. KayakFlightParser

**Rôle** : Parser le JSON brut depuis l'API interne Kayak et convertir vers GoogleFlightDTO

**Fichier** : `app/services/kayak/flight_parser.py`

**Interface** :
```python
class KayakFlightParser:
    """Parser pour extraire vols depuis JSON API interne Kayak."""

    def parse(self, json_data: dict) -> list[GoogleFlightDTO]:
        """Parse JSON Kayak et retourne liste vols au format GoogleFlightDTO."""
```

**Champs/Paramètres** :

| Paramètre | Type | Description | Contraintes |
|-----------|------|-------------|-------------|
| `json_data` | `dict` | JSON brut depuis API Kayak | Contient keys `results`, `legs`, `segments` |
| **Return** | `list[GoogleFlightDTO]` | Liste vols parsés triés par prix | Trié ascendant, 0-N résultats |

**Comportement** :
- Valide présence des keys obligatoires (`results`, `legs`, `segments`)
- Dénormalise chaque result : resolve legs par ID, puis segments par ID
- Convertit chaque segment dénormalisé vers GoogleFlightDTO
- Gère champs optionnels avec defaults (ex: `stops`, `layover`, aéroports)
- Trie résultats finaux par prix ascendant
- Lève `ValueError` si JSON malformé (keys manquantes)
- Retourne liste vide si `results = []` ou `status != "complete"`

**Validations** :
- Vérifier `json_data.get("results")` est liste (pas None)
- Vérifier `json_data.get("legs")` est dict
- Vérifier `json_data.get("segments")` est dict
- Ignorer results avec `legs` ou `segments` manquants (log warning)

---

## 2. Structure JSON Kayak

**Input attendu** (depuis network capture) :

```json
{
  "status": "complete",
  "results": [
    {
      "resultId": "abc123",
      "price": 1250.00,
      "legs": ["leg_id_1", "leg_id_2"]
    }
  ],
  "legs": {
    "leg_id_1": {
      "duration": 765,
      "stops": 0,
      "segments": ["segment_id_1"],
      "layover": {"duration": 120}
    }
  },
  "segments": {
    "segment_id_1": {
      "airline": "AF",
      "flightNumber": "123",
      "origin": "CDG",
      "destination": "NRT",
      "departure": "2026-01-14T10:30:00",
      "arrival": "2026-01-15T06:45:00",
      "duration": 765
    }
  }
}
```

**Mapping vers GoogleFlightDTO** :

| Champ GoogleFlightDTO | Source Kayak | Notes |
|-----------------------|--------------|-------|
| `price` | `results[].price` | Float obligatoire |
| `airline` | `segments{}.airline` | String code IATA (ex: "AF") |
| `departure_time` | `segments{}.departure` | ISO 8601 string |
| `arrival_time` | `segments{}.arrival` | ISO 8601 string |
| `duration` | `legs{}.duration` minutes → format "Xh Ymin" | Conversion minutes → string |
| `stops` | `legs{}.stops` | Int optionnel (défaut: 0 si absent) |
| `departure_airport` | `segments{}.origin` | String code IATA (optionnel) |
| `arrival_airport` | `segments{}.destination` | String code IATA (optionnel) |

---

## 3. Conversion Format Duration

**Rôle** : Convertir durée en minutes (Kayak) vers format string lisible (GoogleFlightDTO)

**Fonction utilitaire** :
```python
def format_duration(minutes: int) -> str:
    """Convertit durée en minutes vers format 'Xh Ymin'."""
```

**Exemples** :

| Input (minutes) | Output (string) |
|-----------------|-----------------|
| 765 | "12h 45min" |
| 120 | "2h 0min" |
| 90 | "1h 30min" |
| 45 | "0h 45min" |

---

## 4. Gestion Erreurs

**Exceptions levées** :

| Situation | Exception | Message |
|-----------|-----------|---------|
| `results` key manquante | `ValueError` | "Missing 'results' key in Kayak JSON" |
| `legs` key manquante | `ValueError` | "Missing 'legs' key in Kayak JSON" |
| `segments` key manquante | `ValueError` | "Missing 'segments' key in Kayak JSON" |
| Leg ID non trouvé | Log warning, skip result | "Leg ID 'xxx' not found in legs dict" |
| Segment ID non trouvé | Log warning, skip result | "Segment ID 'xxx' not found in segments dict" |

**Resilience** :
- Utiliser `.get(key, default)` pour tous les champs optionnels
- Ne pas crasher si `layover` absent (layover optionnel)
- Ne pas crasher si `stops` absent (défaut: 0)
- Logger warnings pour IDs manquants mais continuer parsing

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### KayakFlightParser.parse (~10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_parse_valid_json_complete` | Parse JSON valide complet avec status "complete" | JSON avec 2 results, tous champs présents | Liste de 2 GoogleFlightDTO triés par prix | Vérifie dénormalisation correcte + tri |
| 2 | `test_parse_empty_results` | Parse JSON avec results vide | `{"results": [], "legs": {}, "segments": {}}` | Liste vide `[]` | Vérifie gestion cas sans résultats |
| 3 | `test_parse_missing_results_key` | JSON sans key "results" | `{"legs": {}, "segments": {}}` | Lève `ValueError("Missing 'results' key")` | Vérifie validation structure JSON |
| 4 | `test_parse_missing_legs_key` | JSON sans key "legs" | `{"results": [...], "segments": {}}` | Lève `ValueError("Missing 'legs' key")` | Vérifie validation structure JSON |
| 5 | `test_parse_missing_segments_key` | JSON sans key "segments" | `{"results": [...], "legs": {}}` | Lève `ValueError("Missing 'segments' key")` | Vérifie validation structure JSON |
| 6 | `test_parse_leg_id_not_found` | Result référence leg ID inexistant | Result avec `legs: ["unknown_id"]` | Skip ce result, log warning | Vérifie resilience face IDs invalides |
| 7 | `test_parse_segment_id_not_found` | Leg référence segment ID inexistant | Leg avec `segments: ["unknown_id"]` | Skip ce result, log warning | Vérifie resilience face IDs invalides |
| 8 | `test_parse_optional_fields_absent` | Segments sans stops/layover | Segment sans champs `stops`, `layover` | GoogleFlightDTO avec `stops=0`, pas de crash | Vérifie defaults intelligents |
| 9 | `test_parse_sorting_by_price` | Résultats avec prix désordonnés | 3 results avec prix [1500, 1000, 1200] | Liste triée [1000, 1200, 1500] | Vérifie tri ascendant par prix |
| 10 | `test_parse_multiple_segments_per_leg` | Leg avec 2+ segments (escales) | Leg avec `segments: ["seg1", "seg2"]` | 1 GoogleFlightDTO par segment | Vérifie gestion vols multi-segments |

### Conversion format_duration (~3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 11 | `test_format_duration_hours_and_minutes` | Conversion durée mixte | 765 minutes | `"12h 45min"` | Vérifie calcul heures + minutes |
| 12 | `test_format_duration_hours_only` | Conversion durée ronde | 120 minutes | `"2h 0min"` | Vérifie gestion minutes = 0 |
| 13 | `test_format_duration_minutes_only` | Conversion durée < 1h | 45 minutes | `"0h 45min"` | Vérifie gestion heures = 0 |

**Total tests unitaires** : 13 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_parse_real_kayak_response` | JSON réel capturé depuis API Kayak (fixture) | Appel `parse(json_data)` | Liste GoogleFlightDTO valide, tous champs mappés correctement |
| 2 | `test_integration_parse_malformed_json_gracefully` | JSON malformé (keys manquantes) | Appel `parse(json_data)` | Lève `ValueError` avec message explicite, pas de crash |

**Total tests intégration** : 2 tests

---

## Exemples JSON

**Exemple 1 : JSON Kayak valide complet**
```json
{
  "status": "complete",
  "results": [
    {
      "resultId": "result_1",
      "price": 1250.50,
      "legs": ["leg_1"]
    },
    {
      "resultId": "result_2",
      "price": 980.00,
      "legs": ["leg_2"]
    }
  ],
  "legs": {
    "leg_1": {
      "duration": 765,
      "stops": 1,
      "segments": ["segment_1", "segment_2"],
      "layover": {"duration": 120}
    },
    "leg_2": {
      "duration": 600,
      "stops": 0,
      "segments": ["segment_3"]
    }
  },
  "segments": {
    "segment_1": {
      "airline": "AF",
      "flightNumber": "123",
      "origin": "CDG",
      "destination": "JFK",
      "departure": "2026-01-14T10:30:00",
      "arrival": "2026-01-14T13:45:00",
      "duration": 465
    },
    "segment_2": {
      "airline": "AA",
      "flightNumber": "456",
      "origin": "JFK",
      "destination": "LAX",
      "departure": "2026-01-14T16:00:00",
      "arrival": "2026-01-14T19:15:00",
      "duration": 300
    },
    "segment_3": {
      "airline": "UA",
      "flightNumber": "789",
      "origin": "ORD",
      "destination": "SFO",
      "departure": "2026-01-15T08:00:00",
      "arrival": "2026-01-15T12:00:00",
      "duration": 600
    }
  }
}
```

**Exemple 2 : GoogleFlightDTO parsé depuis result_2**
```json
{
  "price": 980.00,
  "airline": "UA",
  "departure_time": "2026-01-15T08:00:00",
  "arrival_time": "2026-01-15T12:00:00",
  "duration": "10h 0min",
  "stops": 0,
  "departure_airport": "ORD",
  "arrival_airport": "SFO"
}
```

**Exemple 3 : JSON Kayak avec champs optionnels absents**
```json
{
  "status": "complete",
  "results": [
    {
      "resultId": "result_minimal",
      "price": 1500.00,
      "legs": ["leg_minimal"]
    }
  ],
  "legs": {
    "leg_minimal": {
      "duration": 480,
      "segments": ["segment_minimal"]
    }
  },
  "segments": {
    "segment_minimal": {
      "airline": "BA",
      "departure": "2026-02-01T14:00:00",
      "arrival": "2026-02-01T22:00:00",
      "duration": 480
    }
  }
}
```

**Exemple 4 : JSON malformé (key manquante)**
```json
{
  "status": "complete",
  "results": [
    {"resultId": "r1", "price": 1000, "legs": ["l1"]}
  ],
  "segments": {
    "s1": {"airline": "AF", "duration": 300}
  }
}
```
→ Lève `ValueError("Missing 'legs' key in Kayak JSON")`

---

# ✅ Critères d'acceptation

## Critères fonctionnels
1. **Parse JSON valide complet** : Parser extrait correctement tous les champs depuis structure dénormalisée (results → legs → segments)
2. **Conversion GoogleFlightDTO** : Mapping correct de tous les champs Kayak vers GoogleFlightDTO (price, airline, times, duration, stops, airports)
3. **Tri par prix** : Résultats finaux triés par prix ascendant (moins cher en premier)
4. **Gestion champs optionnels** : Champs absents (`stops`, `layover`, airports) gérés avec defaults intelligents sans crash
5. **Gestion liste vide** : JSON avec `results: []` retourne liste vide `[]` sans erreur
6. **Gestion IDs invalides** : Leg/Segment IDs non trouvés → skip result + log warning, pas de crash

## Critères techniques
7. **Validation structure JSON** : Lève `ValueError` si keys obligatoires (`results`, `legs`, `segments`) absentes
8. **Type safety strict** : Annotations types PEP 695 sur toutes les signatures
9. **Resilience parsing** : Utilisation systématique `.get(key, default)` pour champs optionnels
10. **Format duration** : Conversion minutes → string "Xh Ymin" (ex: 765 → "12h 45min")
11. **Logs structurés** : Warnings avec contexte (IDs manquants) via `logger.warning(..., extra={...})`
12. **Pas de dépendances externes** : Parser utilise uniquement stdlib Python + Pydantic (pas de libs JSON spécifiques)

## Critères qualité
13. **Coverage ≥ 90%** : Module `flight_parser.py` couvert à 90%+ par tests unitaires
14. **13 tests unitaires** : Tous scénarios (nominal, edge cases, erreurs) testés
15. **2 tests intégration** : Parse JSON réel + JSON malformé
16. **Ruff + Mypy + Type hints** : Code conforme standards projet (0 erreurs lint/typecheck)
17. **Docstrings 1 ligne** : Toutes fonctions documentées (format PEP 257)
18. **Pas de commentaires inline** : Code self-explanatory (sauf justification explicite)

## Critères production
19. **Performance < 100ms** : Dénormalisation de 50 résultats en < 100ms (benchmark intégration)
20. **Logs production** : Log warning pour IDs manquants (permet debugging structure JSON évolutive)
21. **Future-proof** : Structure permet ajout facile de nouveaux champs Kayak (extensibilité)
