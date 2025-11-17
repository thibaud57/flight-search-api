---
title: "Tenacity - Retry Logic & Resilience"
description: "Référence complète Tenacity pour retry logic : décorateur @retry, wait strategies (fixed, exponential, jitter), stop conditions, async/await support, combinaison strategies. Consulter pour configuration resilience patterns, exponential backoff with jitter, error handling async."
date: "2025-17-11"
keywords: ["tenacity", "retry", "resilience", "async", "exponential-backoff", "jitter", "decorator", "wait-strategies"]
scope: ["code"]
technologies: ["tenacity"]
---

# 1. Décorateur @retry - Utilisation Basique

## Explication

Le décorateur `@retry` est le point d'entrée principal de Tenacity. Il enveloppe une fonction avec une logique de retry automatique.

## Exemple de Code

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

# 2. Wait Strategies - Exponential Backoff et Jitter

## Explication

Les stratégies d'attente contrôlent les délais entre les tentatives de retry. L'exponential backoff augmente progressivement les délais pour éviter de surcharger un service défaillant. Le jitter (aléatoire) prévient le problème du "thundering herd".

## Exemples de Code

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

# 3. Async Support - Retry avec Async/Await

## Explication

Tenacity supporte nativement les coroutines asyncio avec sleeps asynchrones. Le décorateur `@retry` fonctionne directement sur les fonctions `async def`.

## Exemples de Code

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

# 4. Points Clés à Retenir

| Concept | Usage Pattern |
|---------|---------------|
| **Stop Conditions** | `stop_after_attempt(N)`, `stop_after_delay(seconds)` |
| **Retry Conditions** | `retry_if_exception_type(Exception)`, `retry_if_result(predicate)` |
| **Wait Strategies** | Combinables avec `+` ou `\|` : fixed, exponential, jitter, chain |
| **Async** | Décorateur `@retry` ou classe `AsyncRetrying`, sleeps natifs |

# Ressources

## Documentation Officielle

- **Tenacity Documentation** : https://tenacity.readthedocs.io/en/latest/
- **API Reference** : https://tenacity.readthedocs.io/en/latest/api.html
- **Wait Strategies** : https://tenacity.readthedocs.io/en/latest/index.html#wait-strategies
- **Async Retry** : https://tenacity.readthedocs.io/en/latest/index.html#retrying-async
