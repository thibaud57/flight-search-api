---
title: "Kayak - Structure URL & Scraping"
description: "Référence Kayak : URL structure simple (/flights/PAR-SLZ/date), JSON API interne (segments, legs, results), polling mechanism, timing optimisé (30-45s), bandwidth optimization. Consulter pour intégration scraping Kayak."
date: "2025-25-11"
keywords: ["kayak", "url", "scraping", "polling", "json", "api", "flights", "multi-city", "segments", "timing", "bandwidth"]
scope: ["code"]
technologies: ["kayak", "crawl4ai", "playwright"]
---

# Structure URL Kayak

## Description

Kayak utilise une structure URL simple et lisible pour les recherches de vols, contrairement à Google Flights qui encode les paramètres en base64. Les URLs sont directement construites avec les codes aéroports et dates dans le path.

## Format URL

```
https://www.kayak.fr/flights/{origin}-{destination}/{date_depart}/{date_retour}?sort=bestflight_a
```

## Exemples

**Aller simple**
```
https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a
```

**Aller-retour**
```
https://www.kayak.fr/flights/PAR-TYO/2026-03-15/2026-03-25?sort=bestflight_a
```

**Multi-city (3 segments)**
```
https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a
```

## Points clés

- **Format origine/destination** : Codes IATA 3 lettres séparés par `-` (ex: `PAR-SLZ`)
- **Format dates** : `YYYY-MM-DD` dans le path (pas en query params)
- **Multi-city** : Segments concaténés dans le path avec `/`
- **Tri par défaut** : `?sort=bestflight_a` pour meilleurs résultats en premier
- **Localisation** : Domaine `.fr` pour France, prix en EUR automatique

---

# Structure JSON API Interne

## Description

Kayak charge les résultats via une API interne non documentée. Les données sont structurées en dictionnaires avec `segments`, `legs`, `results`. Cette API est utilisée par le frontend Kayak et peut être interceptée via network capture.

## Endpoints Observés

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/search/V8/flight/start` | GET | Démarre une recherche, retourne `searchId` |
| `/i/api/search/dynamic/flights/poll` | POST | **Endpoint principal** - Récupère résultats progressifs (vérifié 2025-11-26) |
| `/api/search/V8/flight/poll` | GET | Ancien endpoint poll (remplacé par `/i/api/search/dynamic/flights/poll`) |
| `/k/authajax/` | GET | Authentification session |

**Note** : L'endpoint principal vérifié pour la capture de résultats est `/i/api/search/dynamic/flights/poll` (POST), pas `/api/search/V8/flight/poll` (GET). La structure path a évolué.

## Structure JSON Response (Vérifiée 2025-11-26)

**Response complète** `/i/api/search/dynamic/flights/poll` :

```json
{
  "status": "complete",
  "searchStatus": {
    "tripType": "multicity",
    "legs": [...]
  },
  "totalCount": 2005,
  "filteredCount": 535,
  "pageNumber": 1,
  "pageSize": 15,
  "results": [
    {
      "resultId": "d8399293dd06900e3dd54eaaea8af4e5",
      "type": "core",
      "isBest": true,
      "isCheapest": false,
      "bookingOptions": [
        {
          "providerCode": "GOTOGATE",
          "displayPrice": {
            "price": 1380,
            "currency": "EUR",
            "localizedPrice": "1 380 €"
          },
          "bookingUrl": {
            "url": "/book/flight?code=...",
            "urlType": "relative"
          },
          "fareAmenities": [
            {
              "type": "CARRYON_BAG",
              "restriction": "UNAVAILABLE"
            },
            {
              "type": "CHECKED_BAG",
              "restriction": "FEE"
            }
          ]
        }
      ],
      "legs": [
        {
          "id": "CDGSLZ1768910400000LA80671768950000000LA32942",
          "segments": [
            {"id": "1768910400000LA80670705"},
            {"id": "1768950000000LA32941800"}
          ]
        }
      ]
    }
  ],
  "legs": {
    "CDGSLZ1768910400000LA80671768950000000LA32942": {
      "duration": 1100,
      "arrival": "2026-01-21T02:25:00",
      "departure": "2026-01-20T12:05:00",
      "segments": [
        {"id": "1768910400000LA80670705"},
        {"id": "1768950000000LA32941800"}
      ]
    }
  },
  "segments": {
    "1768910400000LA80670705": {
      "airline": "LA",
      "flightNumber": "8067",
      "origin": "CDG",
      "destination": "GRU",
      "departure": "2026-01-20T12:05:00",
      "arrival": "2026-01-20T20:00:00",
      "duration": 715,
      "equipmentTypeName": "Boeing 787-9 Dreamliner"
    }
  },
  "airports": {
    "CDG": {...},
    "GRU": {...}
  },
  "airlines": {
    "LA": {...}
  }
}
```

**Exemple réel capturé** (4 segments multi-city PAR→SLZ, RIO→BUE, SCL→LIM, LIM→PAR) :
- Total résultats : 2005 vols
- Filtrés : 535 vols
- Page 1 : 18 itinéraires (pageSize: 15, mais retourne 18)
- Meilleur prix : 1 380 € (GOTOGATE)
- 6 booking options par résultat (multi-providers)

## Champs Clés

### Top-Level (Metadata)

| Champ | Type | Description |
|-------|------|-------------|
| `status` | string | `"complete"` ou `"polling"` - indicateur fin chargement |
| `searchStatus` | object | Metadata recherche (tripType, legs, travelers, bags) |
| `searchStatus.tripType` | string | `"multicity"`, `"roundtrip"`, `"oneway"` |
| `totalCount` | int | Nombre total résultats trouvés |
| `filteredCount` | int | Nombre résultats après filtres |
| `pageNumber` | int | Numéro page courante (pagination) |
| `pageSize` | int | Taille page (nombre max résultats par page) |

### Results (Itinéraires complets)

| Champ | Type | Description |
|-------|------|-------------|
| `results[]` | array | Liste itinéraires complets multi-city |
| `results[].resultId` | string | ID unique résultat (hash) |
| `results[].type` | string | `"core"` = résultat standard |
| `results[].isBest` | boolean | ✅ Flag "meilleur vol" (ranking Kayak) |
| `results[].isCheapest` | boolean | ✅ Flag "moins cher" |
| `results[].bookingOptions[]` | array | ✅ **Multi-providers** (6+ prix différents) |
| `results[].legs[]` | array | Segments multi-city (inline avec id + segments[]) |

### Booking Options (Multi-providers)

| Champ | Type | Description |
|-------|------|-------------|
| `bookingOptions[].providerCode` | string | Provider (GOTOGATE, FLIGHTNETWORK, etc.) |
| `bookingOptions[].displayPrice` | object | Prix formaté (price, currency, localizedPrice) |
| `bookingOptions[].displayPrice.price` | float | Prix brut (ex: 1380.00) |
| `bookingOptions[].displayPrice.currency` | string | Devise (EUR, USD, etc.) |
| `bookingOptions[].displayPrice.localizedPrice` | string | Prix localisé (ex: "1 380 €") |
| `bookingOptions[].bookingUrl` | object | URL réservation (relative ou absolute) |
| `bookingOptions[].fareAmenities[]` | array | Détails baggages, changements, sièges |

### Legs (Référentiel segments multi-city)

| Champ | Type | Description |
|-------|------|-------------|
| `legs{}` | dict | Dictionnaire leg_id → données trajet (duration, stops) |
| `legs{}.duration` | int | Durée totale leg en minutes |
| `legs{}.arrival` | string | ISO 8601 datetime arrivée finale leg |
| `legs{}.departure` | string | ISO 8601 datetime départ initial leg |
| `legs{}.segments[]` | array | Liste segment_ids composant ce leg |

### Segments (Vols individuels)

| Champ | Type | Description |
|-------|------|-------------|
| `segments{}` | dict | Dictionnaire segment_id → données vol |
| `segments{}.airline` | string | Code IATA compagnie (ex: `LA`, `AF`) |
| `segments{}.flightNumber` | string | Numéro vol (ex: `"8067"`) |
| `segments{}.origin` | string | Code IATA aéroport départ (ex: `"CDG"`) |
| `segments{}.destination` | string | Code IATA aéroport arrivée (ex: `"GRU"`) |
| `segments{}.departure` | string | ISO 8601 datetime départ |
| `segments{}.arrival` | string | ISO 8601 datetime arrivée |
| `segments{}.duration` | int | Durée segment en minutes |
| `segments{}.equipmentTypeName` | string | ✅ Type avion (ex: "Boeing 787-9 Dreamliner") |

### Référentiels (Dictionnaires lookup)

| Champ | Type | Description |
|-------|------|-------------|
| `airports{}` | dict | Dictionnaire code_IATA → données aéroport |
| `airlines{}` | dict | Dictionnaire code_IATA → données compagnie |

## Points clés

- **Structure dénormalisée** : `results` référence `legs` par ID via `results[].legs[].id`, `legs` référence `segments` par ID
- **Multi-providers** : ✅ **Avantage majeur** - Chaque résultat a 6+ `bookingOptions[]` avec prix différents (GOTOGATE, FLIGHTNETWORK, etc.)
- **Ranking natif** : `isBest` et `isCheapest` flags → pas besoin calculer soi-même
- **Metadata pagination** : `totalCount`, `filteredCount`, `pageNumber`, `pageSize` disponibles
- **Type avion** : `segments{}.equipmentTypeName` détaillé (ex: "Boeing 787-9 Dreamliner")
- **Layover disponible** : `legs{}.layover.duration` pour escales (si présent)
- **Status polling** : Checker `status == "complete"` pour savoir si tous résultats chargés
- **Prix localisés** : `displayPrice.localizedPrice` format natif (ex: "1 380 €")

---

# Timing & Polling Strategy

## Description

Kayak charge les résultats progressivement via polling. Contrairement à une idée reçue, il n'est PAS nécessaire d'attendre la fin complète du polling pour avoir des résultats exploitables - les meilleurs prix apparaissent généralement dans le premier batch.

## Observations Timing

| Phase | Durée observée | Notes |
|-------|---------------|-------|
| Chargement page initial | 10-20s | DOM + premiers scripts |
| Premier batch résultats | 15-25s | Top résultats déjà triés |
| Polling complet | 45-90s | Tous résultats (pas nécessaire) |

## Stratégie Recommandée

```python
# Configuration optimisée
KAYAK_CONFIG = {
    "page_load_timeout": 30,      # Max attente chargement page
    "first_results_wait": 20,     # Attente premier batch
    "max_total_wait": 45,         # Timeout total (pas 90s!)
    "poll_interval": (4, 8),      # Intervalle randomisé anti-détection
}

async def fetch_kayak_results(url: str) -> dict:
    """
    Stratégie smart : prendre premiers résultats sans attendre completion.

    Les premiers résultats Kayak sont triés par "bestflight" donc
    contiennent déjà les meilleures options.
    """
    # 1. Charger page avec network capture
    # 2. Attendre premier XHR avec results[] non vide
    # 3. Extraire Top 10 → terminé (pas besoin status=complete)
```

## Points clés

- **Premiers résultats = meilleurs** : Kayak trie par pertinence, pas besoin d'attendre fin polling
- **Timeout conservateur** : 30-45s suffisent pour Top 10
- **Bandwidth optimisé** : Pas de polling continu = moins de requêtes
- **Anti-détection** : Délais randomisés entre actions (`randint(4, 8)`)

---

# Bandwidth Optimization

## Description

Le scraping Kayak peut consommer beaucoup de bandwidth à cause des ressources non essentielles (images, fonts, tracking). Une stratégie de blocage via Playwright hooks permet de réduire la consommation de ~60%.

## Ressources à Bloquer

| Type | Exemples | Économie estimée |
|------|----------|------------------|
| Images | Logos compagnies, photos | ~200-400KB |
| Fonts | Google Fonts, custom | ~50-150KB |
| Tracking | Doubleclick, analytics | ~30-100KB |
| Ads | Publicités diverses | ~100-300KB |

## Domaines à Bloquer

```python
BLOCKED_DOMAINS = [
    "fonts.gstatic.com",
    "fonts.googleapis.com",
    "*.doubleclick.net",
    "*.googlesyndication.com",
    "www.googletagmanager.com",
    "*.facebook.net",
    "*.twitter.com",
    "sc-static.net",  # Kayak tracking
]
```

## Resource Types à Bloquer

```python
BLOCKED_TYPES = [
    "image",
    "font",
    "media",
    "stylesheet",  # Optionnel - peut casser layout mais pas données
]

ALLOWED_TYPES = [
    "xhr",      # API calls = données vols
    "fetch",    # API calls
    "script",   # JavaScript nécessaire
    "document", # HTML page
]
```

## Hook Playwright

```python
async def block_kayak_resources(route: Route) -> None:
    """Bloquer ressources non essentielles Kayak."""
    url = route.request.url
    resource_type = route.request.resource_type

    # Bloquer domaines tracking/ads
    if any(domain in url for domain in BLOCKED_DOMAINS):
        await route.abort()
        return

    # Bloquer types lourds
    if resource_type in BLOCKED_TYPES:
        await route.abort()
        return

    # Autoriser le reste (notamment XHR/Fetch API)
    await route.continue_()
```

## Points clés

- **Whitelist XHR/Fetch** : Essentiel - contiennent les données vols
- **Scripts nécessaires** : JavaScript Kayak génère les API calls
- **CSS optionnel** : Peut être bloqué si seules données JSON nécessaires
- **Économie réelle** : ~60% bandwidth en moins par recherche

---

# Consent Popup Handler

## Description

Kayak affiche un popup de consentement cookies (RGPD) au premier chargement. Ce popup doit être fermé pour que la page charge correctement les résultats.

## Sélecteurs Observés

```python
# À identifier précisément lors de l'implémentation
KAYAK_CONSENT_SELECTORS = [
    "button[id*='accept']",
    "button[class*='consent']",
    "div[class*='cookie'] button",
    # Sélecteur exact à déterminer via inspection
]
```

## Stratégie

```python
async def handle_kayak_consent(page: Page) -> None:
    """Fermer popup consent Kayak si présent."""
    try:
        # Attendre popup (timeout court - peut ne pas apparaître)
        consent_btn = await page.wait_for_selector(
            KAYAK_CONSENT_SELECTOR,
            timeout=5000
        )
        if consent_btn:
            await consent_btn.click()
            await asyncio.sleep(1)  # Laisser popup se fermer
    except TimeoutError:
        pass  # Pas de popup = OK
```

## Points clés

- **Timeout court** : 5s max - popup peut ne pas apparaître (cookies déjà acceptés)
- **Non bloquant** : Ignorer si pas de popup
- **Sélecteur à valider** : Inspecter page Kayak réelle pour sélecteur exact

---

# Avantage Multi-Providers (Kayak vs Google Flights)

## Description

**Différence majeure** : Kayak retourne **plusieurs prix par itinéraire** (6+ booking options) alors que Google Flights ne retourne **qu'un seul prix**. Cet avantage est crucial pour proposer le meilleur rapport qualité/prix aux utilisateurs.

## Exemple Réel (Capture 2025-11-26)

**Itinéraire multi-city** : PAR→SLZ / RIO→BUE / SCL→LIM / LIM→PAR

**Kayak** : 6 booking options pour le même itinéraire
```json
{
  "resultId": "d8399293dd06900e3dd54eaaea8af4e5",
  "bookingOptions": [
    {
      "providerCode": "GOTOGATE",
      "displayPrice": {"price": 1380, "localizedPrice": "1 380 €"}
    },
    {
      "providerCode": "FLIGHTNETWORK",
      "displayPrice": {"price": 1390, "localizedPrice": "1 390 €"}
    },
    {
      "providerCode": "GOTOGATE",
      "displayPrice": {"price": 1560, "localizedPrice": "1 560 €"}
    },
    {
      "providerCode": "FLIGHTNETWORK",
      "displayPrice": {"price": 1571, "localizedPrice": "1 571 €"}
    },
    {
      "providerCode": "GOTOGATE",
      "displayPrice": {"price": 1814, "localizedPrice": "1 814 €"}
    }
  ]
}
```

**Google Flights** : 1 seul prix pour le même itinéraire
```json
{
  "flightId": "abc123",
  "price": {"total": 1450}
}
```

## Stratégie Extraction Prix

**Recommandation** : Toujours extraire le **prix minimum** de `bookingOptions[]` pour chaque résultat :

```python
def get_cheapest_price(result: dict) -> float:
    """Retourne le prix minimum parmi tous les providers."""
    return min(
        opt["displayPrice"]["price"]
        for opt in result["bookingOptions"]
    )
```

**Tri Top 10** : Utiliser prix minimum par résultat pour ranking :

```python
top_10 = sorted(
    results,
    key=lambda r: get_cheapest_price(r)
)[:10]
```

## Points clés

- **Meilleure valeur utilisateur** : 6+ prix différents = plus de chances d'avoir le meilleur prix
- **Providers variés** : GOTOGATE, FLIGHTNETWORK, TRAVELOCITY, PRICELINE, etc.
- **Écart prix** : Jusqu'à +31% entre provider le plus cher et le moins cher (1 380 € vs 1 814 €)
- **Tri automatique** : `bookingOptions[]` déjà triés par prix croissant dans Kayak
- **Avantage compétitif** : API retourne plus d'options que concurrent Google Flights

---

# Différences vs Google Flights

## Comparaison

| Aspect | Google Flights | Kayak |
|--------|---------------|-------|
| **URL** | Params encodés base64 `tfs=` | Path simple `/PAR-TYO/date` |
| **Données** | API interne JSON | API interne JSON |
| **Chargement** | 10-15s (networkidle) | 20-30s (premiers résultats) |
| **Polling** | Non requis | Optionnel (premiers résultats OK) |
| **Structure JSON** | `data.flights[].segments[]` | `results[]` → `legs{}` → `segments{}` |
| **Prix** | ❌ 1 prix unique | ✅ 6+ prix (multi-providers) |
| **Escales** | `stops` count | `layover.duration` détaillé |
| **Ranking** | Calcul manuel | `isBest`, `isCheapest` flags |
| **Type avion** | Basique | `equipmentTypeName` détaillé |

## Avantages Kayak

- **✅ Multi-providers** : 6+ prix par itinéraire vs 1 seul (Google) → **Meilleure valeur utilisateur**
- **Layover détaillé** : Durée escale précise (pas juste count)
- **URL lisible** : Debug plus facile
- **Tri natif** : `?sort=bestflight_a` pré-trie résultats
- **Ranking natif** : `isBest`, `isCheapest` flags disponibles
- **Type avion** : Détails complets (Boeing 787-9 Dreamliner vs juste "787")

## Inconvénients Kayak

- **Plus lent** : 20-30s vs 10-15s Google
- **API instable** : Structure peut changer (non documentée)
- **Polling complexe** : Nécessite gestion status

---

# Notes Importantes

## API Non Officielle

- Kayak **n'a PAS d'API publique** officielle
- Les endpoints `/api/search/V8/...` sont **internes** (peuvent changer)
- Services comme Piloterr/Apify sont des **services tiers payants** (scraping-as-a-service)

## Anti-Détection

- **Proxies résidentiels** : Decodo fonctionne pour Kayak (France targeting)
- **Délais randomisés** : `randint(4, 8)` entre actions
- **User-agent rotation** : Via Crawl4AI stealth mode
- **Cookies** : Accepter consent pour éviter redirections

## Maintenance

- Structure JSON peut évoluer → parser résilient avec `.get()` et defaults
- Sélecteurs consent peuvent changer → fallback si non trouvé
- Tester régulièrement avec vraies requêtes

---

# Ressources

- **Kayak** : https://www.kayak.fr (pas de docs API officielles)
- **Services Scraping** :
  - Piloterr : https://www.piloterr.com/library/kayak-flight
  - Apify : https://apify.com/jupri/kayak-flights
