---
title: "Google Flights - URL Structure & Paramètres"
description: "Référence Google Flights : URL structure (flight_type, airports, dates), paramètres (departure_id, arrival_id, outbound_date, return_date), localisation (hl, curr France/EUR), multi-city (multi_city_json avec segments), URL encoding, codes IATA. Consulter pour construction URLs crawling Google Flights."
date: "2025-17-11"
keywords: ["google-flights", "url", "url-structure", "parameters", "paramètres", "multi-city", "dates", "iata", "airports", "flight-type", "locale", "currency", "query", "encoding"]
scope: ["code"]
technologies: ["google-flights"]
---

# Structure URL de Base

## Description

Google Flights utilise une URL structurée avec des paramètres query pour définir les recherches de vols. La structure de base permet de spécifier les aéroports, dates, type de vol et paramètres de localisation (langue, devise). Les URLs sont construites dynamiquement pour refléter les critères de recherche saisis.

## Exemple

```
https://www.google.com/travel/flights?departure_id=CDG&arrival_id=JFK&outbound_date=2025-11-21&return_date=2025-11-28&hl=fr&curr=EUR&flight_type=2
```

## Points clés

- **Format URL** : `https://www.google.com/travel/flights?[parameters]`
- **Paramètres query** : Séparés par `&`, encodés en URL
- **Paramètres principaux** :
  - `departure_id` : Code aéroport départ (3 lettres IATA)
  - `arrival_id` : Code aéroport arrivée (3 lettres IATA)
  - `outbound_date` : Date départ (format YYYY-MM-DD)
  - `return_date` : Date retour (format YYYY-MM-DD, optionnel)
  - `hl` : Langue interface (ex: `fr` pour français)
  - `curr` : Devise (ex: `EUR` pour euros)
  - `flight_type` : Type de vol (1=aller-simple, 2=aller-retour, 3=multi-city)

# Format des Dates

## Description

Google Flights impose un format strict pour les dates dans les URLs : YYYY-MM-DD (année sur 4 chiffres, mois sur 2 chiffres, jour sur 2 chiffres). Ce format ISO 8601 simplifié est utilisé pour tous les paramètres de dates, quel que soit le type de vol (aller-simple, aller-retour, multi-city).

## Exemple

```
outbound_date=2025-11-21&return_date=2025-11-28
```

Exemples concrets :
- Départ : `2025-11-21`
- Retour : `2025-11-28`
- Multi-city segment : `"date":"2025-12-05"`

## Points clés

- **Format unique** : `YYYY-MM-DD` (ISO 8601 simplifié)
- **Aucune variante acceptée** : Pas de format DD/MM/YYYY, MM-DD-YYYY, etc.
- **Zéros obligatoires** : Mois et jours doivent être sur 2 chiffres (`2025-01-05`, pas `2025-1-5`)
- **Universalité** : Format identique quelle que soit la localisation (`hl` parameter)

# Paramètres Multi-City

## Description

Les vols multi-city (plusieurs étapes successives) utilisent le paramètre `multi_city_json` contenant un tableau JSON de segments. Chaque segment définit un trajet individuel avec aéroport de départ, arrivée, date, et options horaires optionnelles. Le JSON doit être URL-encodé avant inclusion dans l'URL.

## Exemple

```json
[
  {
    "departure_id": "CDG",
    "arrival_id": "NRT",
    "date": "2025-11-21"
  },
  {
    "departure_id": "NRT",
    "arrival_id": "LAX,SEA",
    "date": "2025-11-28"
  },
  {
    "departure_id": "LAX",
    "arrival_id": "AUS",
    "date": "2025-12-05",
    "times": "8,18,9,23"
  }
]
```

## Points clés

- **Paramètre** : `multi_city_json` avec tableau JSON de segments
- **Structure segment** :
  - `departure_id` : Aéroport de départ (code IATA 3 lettres)
  - `arrival_id` : Aéroport d'arrivée (code IATA, ou codes multiples séparés par virgule)
  - `date` : Date au format YYYY-MM-DD
  - `times` (optionnel) : Plage horaire (format 24h : `start,end` ou `dep_start,dep_end,arr_start,arr_end`)
- **URL encoding obligatoire** : JSON doit être encodé (`%20`, `%22`, etc.)
- **Limite segments** : ~10+ segments supportés officieusement
- **Multiples destinations** : `arrival_id` accepte plusieurs codes séparés par virgule (`"LAX,SEA"`)

# Localisation & Devise (France/EUR)

## Description

Les paramètres de localisation contrôlent la langue de l'interface et la devise d'affichage des prix. Ces paramètres sont purement cosmétiques et n'affectent pas la logique de recherche sous-jacente (dates et codes aéroports restent universels). Pour la France, utiliser `hl=fr` et `curr=EUR`.

## Exemple

```
https://www.google.com/travel/flights?departure_id=CDG&arrival_id=ORY&outbound_date=2025-11-21&hl=fr&curr=EUR
```

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `hl` | `fr` | Interface en français |
| `curr` | `EUR` | Devise en euros |
| `hl` | `fr-FR` | Français France (variante complète) |

## Points clés

- **Langue interface** : `hl=fr` (français) ou `hl=fr-FR` (français France)
- **Devise affichage** : `curr=EUR` (euros) pour la France
- **Effet cosmétique uniquement** : N'affecte pas la recherche (dates, codes IATA restent universels)
- **Devise interne** : Google convertit depuis USD en interne, `curr` affecte uniquement l'affichage final
- **Variantes régionales** : `fr` suffit généralement, `fr-FR` pour précision géographique

# Exemples Concrets Complets

## Description

Exemples d'URLs Google Flights complètes pour les trois types de vols : aller-simple (`flight_type=1`), aller-retour (`flight_type=2`), et multi-city (`flight_type=3`). Ces URLs incluent tous les paramètres nécessaires (aéroports, dates, localisation) et sont prêtes à l'emploi pour le crawling.

## Exemple

**Aller-Simple : Paris (CDG) → Tokyo (NRT)**
```
https://www.google.com/travel/flights?flight_type=1&departure_id=CDG&arrival_id=NRT&outbound_date=2025-11-21&hl=fr&curr=EUR
```

**Aller-Retour : Paris (CDG) → New York (JFK)**
```
https://www.google.com/travel/flights?flight_type=2&departure_id=CDG&arrival_id=JFK&outbound_date=2025-12-01&return_date=2025-12-15&hl=fr&curr=EUR
```

**Multi-City : Paris → Tokyo → Los Angeles**
```
https://www.google.com/travel/flights?flight_type=3&multi_city_json=[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-11-21"},{"departure_id":"NRT","arrival_id":"LAX","date":"2025-11-28"},{"departure_id":"LAX","arrival_id":"CDG","date":"2025-12-10"}]&hl=fr&curr=EUR
```

## Points clés

- **Aller-simple** : Requiert `flight_type=1`, `departure_id`, `arrival_id`, `outbound_date`
- **Aller-retour** : Requiert `flight_type=2` + `return_date` en plus des paramètres aller-simple
- **Multi-city** : Requiert `flight_type=3` + `multi_city_json` (tableau de segments)
- **Localisation France** : Ajouter `hl=fr&curr=EUR` systématiquement
- **URL encoding** : JSON multi-city doit être encodé (espaces, guillemets, crochets)

# Notes Importantes pour Implémentation

## Description

Points critiques pour l'implémentation de construction d'URLs Google Flights : encodage, formats, limitations et comportements spécifiques de Google Flights à respecter pour éviter erreurs de parsing ou rejets de requêtes.

## Exemple

```python
# ✅ Bon : URL encoding du JSON multi-city
import urllib.parse

multi_city_data = [
    {"departure_id":"CDG","arrival_id":"NRT","date":"2025-11-21"},
    {"departure_id":"NRT","arrival_id":"LAX","date":"2025-11-28"}
]
encoded_json = urllib.parse.quote(json.dumps(multi_city_data))
url = f"https://www.google.com/travel/flights?flight_type=3&multi_city_json={encoded_json}&hl=fr&curr=EUR"
```

## Points clés

- **URL Encoding obligatoire** : Paramètres JSON doivent être URL-encodés (espaces = `%20`, guillemets = `%22`, crochets = `%5B`/`%5D`)
- **Format dates strict** : Toujours `YYYY-MM-DD`, aucune variante acceptée
- **Codes IATA étendus** : Google accepte codes métropoles (ex: `NYC` au lieu de `JFK`, `PAR` au lieu de `CDG`)
- **Localisation cosmétique** : `hl` affecte uniquement interface, dates/codes restent universels
- **Devise affichage seul** : `curr` affecte affichage, requêtes internes en USD
- **Limite multi-city** : ~10+ segments supportés officieusement (limite exacte non documentée)

# Ressources

## Documentation Officielle

- **Google Flights** : https://www.google.com/travel/flights
