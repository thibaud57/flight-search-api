---
title: "Tenacity - Retry Logic & Resilience"
description: "Référence complète Tenacity pour retry logic : décorateur @retry, wait strategies (fixed, exponential, jitter), stop conditions, async/await support, combinaison strategies. Consulter pour configuration resilience patterns, exponential backoff with jitter, error handling async."
date: "2025-17-11"
keywords: ["tenacity", "retry", "resilience", "async", "exponential-backoff", "jitter", "decorator", "wait-strategies"]
scope: ["code"]
technologies: ["tenacity"]
---

# Décorateur @retry - Utilisation Basique

## Description

Le décorateur `@retry` est le point d'entrée principal de Tenacity. Il enveloppe une fonction avec une logique de retry automatique, permettant de gérer les échecs temporaires sans code boilerplate.

## Exemple

```python
from tenacity import retry, stop_after_attempt

# Basique - retente indéfiniment sur exception
@retry
def unreliable_function():
    raise Exception("Échec temporaire")

# Avancé - avec limite d'attempts et wait strategy
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def robust_api_call():
    # Retente jusqu'à 5 fois avec backoff exponentiel
    return requests.get('https://api.example.com/data')
```

## Points clés

- **Décorateur simple** : Ajouter `@retry` suffit pour retry indéfini
- **Stop conditions** : `stop_after_attempt(N)` limite tentatives
- **Wait strategies** : `wait_exponential()` pour backoff progressif
- **Combinable** : Stop + wait + retry conditions combinables
- **Automatique** : Capture toutes exceptions par défaut

# Wait Strategies - Exponential Backoff et Jitter

## Description

Les stratégies d'attente contrôlent les délais entre les tentatives de retry. L'exponential backoff augmente progressivement les délais pour éviter de surcharger un service défaillant. Le jitter (aléatoire) prévient le problème du "thundering herd".

## Exemple

```python
from tenacity import (
    retry, wait_fixed, wait_exponential,
    wait_random_exponential, wait_random, wait_chain
)

# Fixed wait - délai constant
@retry(wait=wait_fixed(2))
def simple_retry():
    pass

# Exponential backoff - 2^x * multiplier secondes
@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def exponential_retry():
    # Attend 4s minimum, jusqu'à 10s max
    pass

# Exponential avec jitter aléatoire
@retry(wait=wait_random_exponential(multiplier=1, max=60))
def jitter_retry():
    # Attendu aléatoire jusqu'à 2^x * 1 secondes, max 60s
    pass

# Combinaison : 3s fixe + 0-2s aléatoire
@retry(wait=wait_fixed(3) + wait_random(0, 2))
def combined_wait():
    pass

# Chaîné - stratégies différentes selon tentatives
@retry(wait=wait_chain(
    wait_fixed(1),
    wait_fixed(5),
    wait_fixed(10)
))
def chained_wait():
    # 1s pour 1ère tentative, 5s pour 2e, 10s pour 3e+
    pass
```

## Points clés

- **wait_fixed** : Délai constant entre tentatives
- **wait_exponential** : Backoff exponentiel (2^x * multiplier secondes)
- **wait_random_exponential** : Exponentiel + jitter pour éviter thundering herd
- **Combinaison `+`** : Additionner stratégies (`wait_fixed(3) + wait_random(0, 2)`)
- **wait_chain** : Stratégies différentes selon numéro tentative
- **min/max** : Bornes pour éviter délais trop courts ou trop longs

# Async Support - Retry avec Async/Await

## Description

Tenacity supporte nativement les coroutines asyncio avec sleeps asynchrones. Le décorateur `@retry` fonctionne directement sur les fonctions `async def`, rendant le retry transparent pour le code asynchrone.

## Exemple

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Async basique avec décorateur
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.example.com/data') as resp:
            return await resp.json()

# Utilisation
async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

```python
# AsyncRetrying pour boucles sans décorateur
from tenacity import AsyncRetrying, stop_after_attempt

async def process_with_retry():
    async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):
        with attempt:
            # Votre code asynchrone ici
            await some_async_operation()

asyncio.run(process_with_retry())
```

## Points clés

- **Support natif async** : Décorateur `@retry` fonctionne directement sur `async def`
- **Sleeps asynchrones** : Utilise `asyncio.sleep()` automatiquement (pas de blocage)
- **AsyncRetrying** : Classe pour boucles manuelles sans décorateur
- **Transparence** : Aucune différence syntaxe entre sync et async retry
- **Combinaison** : Toutes stratégies (stop, wait, retry_if) fonctionnent en async

# Ressources

## Documentation Officielle

- **Tenacity Documentation** : https://tenacity.readthedocs.io/en/latest/
- **API Reference** : https://tenacity.readthedocs.io/en/latest/api.html
- **Wait Strategies** : https://tenacity.readthedocs.io/en/latest/index.html#wait-strategies
- **Async Retry** : https://tenacity.readthedocs.io/en/latest/index.html#retrying-async
