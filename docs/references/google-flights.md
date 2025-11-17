---
title: "Google Flights - URL Structure & Paramètres"
description: "Référence Google Flights : URL structure (flight_type, airports, dates), paramètres (departure_id, arrival_id, outbound_date, return_date), localisation (hl, curr France/EUR), multi-city (multi_city_json avec segments), URL encoding, codes IATA. Consulter pour construction URLs crawling Google Flights."
date: "2025-17-11"
keywords: ["google-flights", "url", "url-structure", "parameters", "paramètres", "multi-city", "dates", "iata", "airports", "flight-type", "locale", "currency", "query", "encoding"]
scope: ["code"]
technologies: ["google-flights"]
---

# 1. Structure URL de Base

## Format standard

```
https://www.google.com/travel/flights?[parameters]
```

## Paramètres principaux

- `departure_id` : Code aéroport départ (3 lettres)
- `arrival_id` : Code aéroport arrivée (3 lettres)
- `outbound_date` : Date départ (YYYY-MM-DD)
- `return_date` : Date retour (YYYY-MM-DD)
- `hl` : Langue interface (ex: `fr` pour français)
- `curr` : Devise (ex: `EUR` pour euros)
- `flight_type` : Type de vol (1=aller-simple, 2=aller-retour, 3=multi-city)

# 2. Format des Dates

## Format standardisé

`YYYY-MM-DD`

## Exemples

- Départ : `2025-11-21`
- Retour : `2025-11-28`

## Utilisation dans URLs

```
outbound_date=2025-11-21&return_date=2025-11-28
```

# 3. Paramètres Multi-City

## Format JSON Multi-City

Pour les vols avec plusieurs étapes, utiliser le paramètre `multi_city_json` avec un JSON encodé :

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

## Structure des Segments

Chaque segment multi-city requiert :

- `departure_id` : Aéroport de départ (code IATA)
- `arrival_id` : Aéroport d'arrivée (code IATA, ou codes multiples séparés par virgule)
- `date` : Date au format YYYY-MM-DD
- `times` (optionnel) : Plage horaire (format 24h : `start,end` ou `dep_start,dep_end,arr_start,arr_end`)

# 4. Localisation & Devise (France/EUR)

## Paramètres de Localisation

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `hl` | `fr` | Interface en français |
| `curr` | `EUR` | Devise en euros |
| `hl` | `fr-FR` | Français France (variante complète) |

## Exemple URL Localisée France

```
https://www.google.com/travel/flights?
  departure_id=CDG
  &arrival_id=ORY
  &outbound_date=2025-11-21
  &hl=fr
  &curr=EUR
```

# 5. Exemples Concrets Complets

## Aller-Simple : Paris (CDG) → Tokyo (NRT)

```
https://www.google.com/travel/flights?
  flight_type=1
  &departure_id=CDG
  &arrival_id=NRT
  &outbound_date=2025-11-21
  &hl=fr
  &curr=EUR
```

## Aller-Retour : Paris (CDG) → New York (JFK)

```
https://www.google.com/travel/flights?
  flight_type=2
  &departure_id=CDG
  &arrival_id=JFK
  &outbound_date=2025-12-01
  &return_date=2025-12-15
  &hl=fr
  &curr=EUR
```

## Multi-City : Paris → Tokyo → Los Angeles

```
https://www.google.com/travel/flights?
  flight_type=3
  &multi_city_json=[
    {"departure_id":"CDG","arrival_id":"NRT","date":"2025-11-21"},
    {"departure_id":"NRT","arrival_id":"LAX","date":"2025-11-28"},
    {"departure_id":"LAX","arrival_id":"CDG","date":"2025-12-10"}
  ]
  &hl=fr
  &curr=EUR
```

# 6. Notes Importantes pour Implémentation

1. **URL Encoding** : Les paramètres JSON doivent être URL-encodés (espaces = `%20`, guillemets = `%22`)
2. **Format Dates** : Toujours utiliser `YYYY-MM-DD`, pas de variantes
3. **Codes IATA** : Google accepte aussi les identifiants de métropole (ex: `NYC` au lieu de `JFK`)
4. **Localisation** : `hl` affecte uniquement l'interface, les dates et codes restent universels
5. **Devise** : Affecte l'affichage uniquement, requête interne en USD
6. **Multi-City Limites** : ~10+ segments supportés officieusement

# Ressources

## Documentation Officielle

- **Google Flights** : https://www.google.com/travel/flights
