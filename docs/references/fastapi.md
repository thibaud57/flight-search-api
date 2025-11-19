---
title: "FastAPI - Framework Web Asynchrone"
description: "Référence FastAPI : Dependency Injection (Depends, sous-dépendances, caching), Async Routes (async def vs def, appels externes), TestClient (tests intégration, GET/POST, validation erreurs). Consulter pour patterns API, tests, best practices async."
date: "2025-17-11"
keywords: ["fastapi", "dependency-injection", "depends", "async-routes", "async", "testclient", "testing", "pytest", "api", "rest-api", "routes", "endpoints", "httpx"]
scope: ["code", "test"]
technologies: ["fastapi", "httpx", "pytest"]
---

# Dependency Injection (Injection de Dépendances)

## Description

La Dependency Injection en FastAPI permet au framework de fournir automatiquement les dépendances déclarées dans vos fonctions. Il suffit de déclarer ce dont vous avez besoin via `Depends()`, et FastAPI se charge de l'injection, réduisant la duplication de code et centralisant la logique partagée.

## Exemple minimal

```python
from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()

# Dépendance simple
def get_query(q: str | None = None):
    return q

# Utilisation dans une route
@app.get("/items/")
async def read_items(q: Annotated[str | None, Depends(get_query)] = None):
    return {"q": q}
```

**Patterns avancés** :

Dépendances réutilisables avec classes :
```python
class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
    return {"q": commons.q, "skip": commons.skip, "limit": commons.limit}
```

Sous-dépendances (dépendances imbriquées) :
```python
def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None,
):
    if not q:
        return last_query
    return q

@app.get("/items/")
async def read_items(query: Annotated[str, Depends(query_or_cookie_extractor)]):
    return {"query": query}
```

## Points clés

- **Mixage async/sync** : Les dépendances peuvent être `async def` ou `def`, mixées librement
- **Caching automatique** : Dépendances identiques réutilisées dans une même requête
- **Contrôle cache** : `use_cache=False` pour forcer réévaluation
- **OpenAPI** : Intégrées automatiquement dans le schéma
- **Type aliases** : `QueryDep = Annotated[str, Depends(get_query)]` pour réutilisation
- **Classes** : Utilisables directement comme dépendances (inférence automatique)

# Async Routes (Routes Asynchrones)

## Description

FastAPI supporte nativement les routes asynchrones via `async def`. Le choix entre `async def` et `def` dépend de vos besoins : utilisez `async def` si vous devez attendre des appels externes (APIs, BDD async), et `def` pour les traitements purement synchrones ou avec des librairies sans support async.

## Exemple minimal

```python
from fastapi import FastAPI

app = FastAPI()

# Route asynchrone
@app.get("/async-items/")
async def read_async_items():
    # Vous pouvez utiliser await ici
    return {"message": "Async route"}

# Route synchrone
@app.get("/sync-items/")
def read_sync_items():
    return {"message": "Sync route"}
```

**Patterns avancés** :

Async pour les appels externes :
```python
import httpx

@app.get("/external/")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

Sync pour les traitements sans I/O :
```python
@app.get("/compute/")
def compute_result():
    result = sum(range(1000000))
    return {"result": result}
```

## Points clés

- **Await uniquement en async** : `await` n'existe que dans `async def`
- **Threadpool pour sync** : FastAPI exécute `def` dans un threadpool externe automatiquement
- **Performances équivalentes** : Les deux approches offrent de bonnes performances
- **Mixage autorisé** : Mélanger `async def` et `def` dans la même application est sans problème
- **I/O externe** : Utiliser `async def` pour APIs, BDD, fichiers (meilleure concurrence)
- **CPU-bound** : Utiliser `def` pour calculs lourds (évite overhead async)

# TestClient (Tests d'Intégration)

## Description

FastAPI fournit `TestClient`, basé sur Starlette et HTTPX, pour tester vos endpoints facilement. Il simule des requêtes HTTP sans serveur réel, permettant des tests d'intégration rapides et fiables avec une syntaxe familière.

## Exemple minimal

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

# Créer le client de test
client = TestClient(app)

# Test simple
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

**Patterns avancés** :

GET avec paramètres :
```python
def test_query_params():
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    assert response.json()["skip"] == 0
```

POST avec JSON :
```python
def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Widget", "price": 9.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Widget"
```

Validation d'erreurs :
```python
def test_invalid_request():
    response = client.post("/items/", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error
    errors = response.json()["detail"]
    assert len(errors) > 0
```

## Points clés

- **Fonctions sync** : Utiliser `def` pour les fonctions de test (pas `async def`)
- **Méthodes HTTP** : Requêtes avec `client.get()`, `client.post()`, `client.put()`, `client.delete()`
- **Response JSON** : Accès JSON via `response.json()`
- **Status codes** : Vérifier `response.status_code` pour les assertions
- **Pytest** : Exécution avec `pytest` automatiquement (détection `test_*.py`)
- **Headers** : `client.get("/", headers={"Authorization": "Bearer token"})`
- **Installation** : Nécessite `httpx` (`pip install httpx pytest`)

# Ressources

## Documentation Officielle

- **FastAPI Documentation** : https://fastapi.tiangolo.com
- **Dependency Injection** : https://fastapi.tiangolo.com/tutorial/dependencies/
- **Async Routes** : https://fastapi.tiangolo.com/async/
- **Testing** : https://fastapi.tiangolo.com/tutorial/testing/
