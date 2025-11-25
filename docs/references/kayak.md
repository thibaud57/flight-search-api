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
| `/api/search/V8/flight/poll` | GET | Récupère résultats progressifs |
| `/k/authajax/` | GET | Authentification session |

## Structure JSON Response

```json
{
  "status": "complete",
  "searchStatus": {
    "tripType": "multicity",
    "legs": [...]
  },
  "results": [
    {
      "resultId": "abc123",
      "price": 1250.00,
      "legs": ["leg_id_1", "leg_id_2", "leg_id_3"]
    }
  ],
  "legs": {
    "leg_id_1": {
      "duration": 765,
      "stops": 0,
      "segments": ["segment_id_1", "segment_id_2"]
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

## Champs Clés

| Champ | Type | Description |
|-------|------|-------------|
| `status` | string | `"complete"` ou `"polling"` - indicateur fin chargement |
| `results[]` | array | Liste combinaisons avec prix et références legs |
| `results[].price` | float | Prix total itinéraire en devise locale |
| `legs{}` | dict | Dictionnaire leg_id → données trajet (duration, stops) |
| `legs{}.duration` | int | Durée totale en minutes |
| `legs{}.segments` | array | Liste segment_ids composant ce leg |
| `segments{}` | dict | Dictionnaire segment_id → données vol |
| `segments{}.airline` | string | Code IATA compagnie (ex: `AF`) |
| `segments{}.duration` | int | Durée segment en minutes |
| `segments{}.departure` | string | ISO 8601 datetime départ |
| `segments{}.arrival` | string | ISO 8601 datetime arrivée |

## Points clés

- **Structure dénormalisée** : `results` référence `legs` par ID, `legs` référence `segments` par ID
- **Layover disponible** : `legs{}.layover.duration` pour escales (si présent)
- **Prix unique** : Prix total dans `results[].price`, pas de prix par segment
- **Status polling** : Checker `status == "complete"` pour savoir si tous résultats chargés

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

# Différences vs Google Flights

## Comparaison

| Aspect | Google Flights | Kayak |
|--------|---------------|-------|
| **URL** | Params encodés base64 `tfs=` | Path simple `/PAR-TYO/date` |
| **Données** | API interne JSON | API interne JSON |
| **Chargement** | 10-15s (networkidle) | 20-30s (premiers résultats) |
| **Polling** | Non requis | Optionnel (premiers résultats OK) |
| **Structure JSON** | `data.flights[].segments[]` | `results[]` → `legs{}` → `segments{}` |
| **Prix** | `price.total` dans flight | `price` dans result |
| **Escales** | `stops` count | `layover.duration` détaillé |

## Avantages Kayak

- **Layover détaillé** : Durée escale précise (pas juste count)
- **URL lisible** : Debug plus facile
- **Tri natif** : `?sort=bestflight_a` pré-trie résultats

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
