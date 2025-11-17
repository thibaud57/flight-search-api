---
title: "Decodo Proxies - Residential Proxy Management"
description: "Référence complète Decodo Proxies pour gestion résidentiels : rotation (rotating vs sticky sessions), ciblage France (country/city), authentification (username/password, API key, IP whitelisting), optimisation bande passante (pricing volumes). Consulter pour configuration proxies, authentification, stratégies de coûts."
date: "2025-17-11"
keywords: ["decodo", "proxies", "residential", "rotation", "ip", "authentication", "france", "bandwidth", "sticky-sessions", "ip-whitelisting", "country-targeting", "pricing", "api-key"]
scope: ["deploy", "code"]
technologies: ["decodo"]
---

# 1. Residential Rotation

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

# 2. France Targeting (Ciblage géographique)

## Description

Decodo permet de cibler précisément les IPs résidentielles de France via des paramètres de localisation. Le pays est spécifié avec le code Alpha-2 ISO (FR pour France), et peut être combiné avec d'autres critères comme la ville ou les codes postaux.

## Configuration exemple

### Endpoint France (tous les modes)

```
fr.decodo.com:30001-39999  # Sticky session (port spécifique)
fr.decodo.com:30000        # Rotating session (port terminé en 0)
```

### Avec authentification Username/Password

```bash
curl -U user-username-country-fr:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

### Avec ciblage France + Paris

```bash
curl -U user-username-country-fr-city-paris:password -x gate.decodo.com:7000 https://ip.decodo.com/json
```

## Notes importantes

- Le code pays est toujours en minuscules (fr, pas FR)
- Le ciblage par ville et ASN sont mutuellement exclusifs
- Whitelisted IP n'accepte que IPv4 (pas IPv6)

# 3. Authentication (Authentification)

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

# 4. Bandwidth Optimization (Optimisation de bande passante)

## Description

Decodo propose une tarification basée sur la bande passante avec réductions selon le volume. Les coûts diminuent proportionnellement avec l'augmentation de la consommation mensuelle.

## Pricing Plans

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

## Optimisation de coûts

### Stratégie de volume

- Pour les grands besoins : privilégier les plans à volume élevé
- Économies : jusqu'à 57% de réduction (1000GB vs 2GB)

### Budget des dépassements

- Prévoir 30-40% de marge supplémentaire pour les pics
- Dépassements facturés au tarif Pay As You Go ($3.50/GB)

# Ressources

## Documentation Officielle

- **Decodo Help Center** : https://help.decodo.com
- **Residential Proxy Quick Start** : https://help.decodo.com/docs/residential-proxy-quick-start
- **Proxy Endpoints and Ports** : https://help.decodo.com/docs/residential-proxy-endpoints-and-ports
- **Authentication Methods** : https://help.decodo.com/docs/residential-proxy-authentication-methods
- **Residential Proxies Pricing** : https://decodo.com/proxies/residential-proxies/pricing
