---
title: "Decodo Proxies - Residential Proxy Management"
description: "Référence complète Decodo Proxies pour gestion résidentiels : rotation (rotating vs sticky sessions), ciblage France (country/city), authentification (username/password, API key, IP whitelisting), optimisation bande passante (pricing volumes). Consulter pour configuration proxies, authentification, stratégies de coûts."
date: "2025-17-11"
keywords: ["decodo", "proxies", "residential", "rotation", "ip", "authentication", "france", "bandwidth", "sticky-sessions", "ip-whitelisting", "country-targeting", "pricing", "api-key"]
scope: ["deploy", "code"]
technologies: ["decodo"]
---

# Residential Rotation

## Description

La rotation résidentielle de Decodo permet d'obtenir des adresses IP différentes soit à chaque requête, soit pendant une durée définie. Les proxies utilisent des appareils résidentiels authentiques (115M+ IPs) dans 195+ pays pour un masquage d'identité fiable.

## Modes disponibles

- **Rotating proxies** : changement d'IP à chaque requête
- **Sticky sessions** : conservation de la même IP pendant 1 à 1440 minutes (jusqu'à 24 heures)

## Configuration exemple

### Mode Rotating (sans session ID)

```bash
curl -U username:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

### Mode Sticky Session (10 minutes par défaut)

```bash
curl -U user-username-country-us-session-abc123:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

### Mode Sticky Session Personnalisé (30 minutes)

```bash
curl -U user-username-country-us-sessionduration-30-session-abc123:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

## Points clés

- **Rotating proxies** : IP change à chaque requête (anonymat maximal)
- **Sticky sessions** : IP conservée 1-1440 min (sessions persistantes)
- **Session ID** : Identifiant unique pour sticky sessions (ex: abc123)
- **Duration personnalisée** : Parameter sessionduration-N pour durée spécifique (minutes)

# France Targeting (Ciblage géographique)

## Description

Decodo permet de cibler précisément les IPs résidentielles de France via des paramètres de localisation. Le pays est spécifié avec le code Alpha-2 ISO (FR pour France), et peut être combiné avec d'autres critères comme la ville ou les codes postaux.

## Configuration exemple

### Endpoint France (tous les modes)

```
fr.decodo.com:40001-49999  # Sticky session (port spécifique)
fr.decodo.com:40000        # Rotating session (port terminé en 0)
```

### Avec authentification Username/Password

```bash
curl -U user-username-country-fr:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

### Avec ciblage France + Paris

```bash
curl -U user-username-country-fr-city-paris:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

## Points clés

- **Code pays** : Toujours en minuscules (fr, pas FR)
- **Endpoints France** : fr.decodo.com:40000 (rotating) ou :40001-49999 (sticky)
- **Ciblage ville** : country-fr-city-paris pour ciblage géographique précis
- **Exclusivité** : Ciblage ville et ASN mutuellement exclusifs
- **IPv4 uniquement** : Whitelisted IP n'accepte que IPv4 (pas IPv6)

# Authentication (Authentification)

## Description

Decodo propose deux méthodes d'authentification : Username/Password (standard) et IP Whitelisting (authentification par adresse IP).

## Format Authentication Username/Password

### Format standard

```
username:password
```

### Format avec paramètres (recommandé)

```
user-{username}-country-{country_code}-city-{city_name}-session-{session_id}:password
```

### Exemple France avec session sticky

```
user-myuser-country-fr-session-mysession123:mypassword
```

### Format avec API Key (Note du plan)

```
customer-{api_key}-country-{country_code}:password
```

### Exemple pour France

```
customer-abc123def456-country-fr:password
```

## Points clés

- **Deux méthodes** : Username/Password (standard) ou IP Whitelisting
- **Format standard** : user-{username}-country-{country}-session-{session_id}:password
- **Format API Key** : customer-{api_key}-country-{country}:password
- **Paramètres combinables** : country, city, session, sessionduration dans username
- **Ordre paramètres** : Respecter ordre exact pour fonctionnement correct

# Bandwidth Optimization (Optimisation de bande passante)

## Description

Decodo propose une tarification basée sur la bande passante avec réductions selon le volume. Les coûts diminuent proportionnellement avec l'augmentation de la consommation mensuelle.

## Exemple

| Volume | Prix/GB | Coût mensuel |
|--------|---------|--------------|
| 2 GB | $3.00 | $6 |
| 8 GB | $2.75 | $22 |
| 25 GB (Populaire) | $2.60 | $65 |
| 50 GB | $2.45 | $123 |
| 100 GB | $2.25 | $225 |
| 250 GB | $2.00 | $500 |
| 500 GB | $1.75 | $875 |
| 1000 GB | $1.50 | $1500 |
| Pay As You Go | $3.50 | - |

## Points clés

- **Tarification volume** : Réductions jusqu'à 57% (1000GB vs 2GB)
- **Plan populaire** : 25GB à $2.60/GB ($65/mois)
- **Stratégie grands besoins** : Privilégier plans volume élevé pour économies maximales
- **Marge dépassements** : Prévoir 30-40% buffer pour pics de consommation
- **Dépassements** : Facturés au tarif Pay As You Go ($3.50/GB)

# Ressources

## Documentation Officielle

- **Decodo Help Center** : https://help.decodo.com
- **Residential Proxy Quick Start** : https://help.decodo.com/docs/residential-proxy-quick-start
- **Proxy Endpoints and Ports** : https://help.decodo.com/docs/residential-proxy-endpoints-and-ports
- **Authentication Methods** : https://help.decodo.com/docs/residential-proxy-authentication-methods
- **Residential Proxies Pricing** : https://decodo.com/proxies/residential-proxies/pricing
