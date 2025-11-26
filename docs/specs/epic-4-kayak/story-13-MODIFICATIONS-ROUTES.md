# Story 13 - Modifications Architecture Routes

**Date** : 2025-11-26
**Décision** : Passer d'une route unifiée avec paramètre `provider` vers **2 routes séparées** pour Google Flights et Kayak

---

## 📋 Décision Architecture

### ❌ Approche actuelle (Story 13 initiale)
- **1 route unifiée** : `POST /api/v1/search-flights`
- **Paramètre** : `provider: "google_flights" | "kayak"` dans SearchRequest
- **Logique** : Factory pattern sélectionne provider selon paramètre

### ✅ Nouvelle approche (demandée par user)
- **2 routes séparées** :
  - `POST /api/v1/search-google-flights` (route Google Flights renommée)
  - `POST /api/v1/search-kayak` (nouvelle route Kayak)
- **Pas de paramètre `provider`** : Route détermine le provider
- **Logique** : Chaque route appelle directement son provider via SearchService

---

## 🔄 Changements Nécessaires

### 1. Models (app/models/request.py)

**AVANT** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city avec provider sélectionnable."""

    template_url: str
    segments_date_ranges: list[DateRange]
    provider: Literal["google_flights", "kayak"] = "google_flights"  # ❌ À supprimer

    @field_validator("provider", mode="after")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Valide provider disponible."""  # ❌ À supprimer
```

**APRÈS** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city (format unifié Google/Kayak)."""

    template_url: str
    segments_date_ranges: list[DateRange]
    # Pas de champ provider - déterminé par la route appelée
```

---

### 2. Routes API (app/api/routes.py)

**AVANT** :
```python
@router.post("/search-flights", response_model=SearchResponse)
async def search_flights(request: SearchRequest) -> SearchResponse:
    """Recherche vols multi-city avec provider sélectionnable."""
    # Factory pattern sélection provider
    provider = provider_factory.get_provider(request.provider)  # ❌
```

**APRÈS** :
```python
@router.post("/search-google-flights", response_model=SearchResponse)
async def search_google_flights(request: SearchRequest) -> SearchResponse:
    """Recherche vols multi-city via Google Flights."""
    # Appel direct GoogleFlightsProvider
    return await google_search_service.search_flights(request)


@router.post("/search-kayak", response_model=SearchResponse)
async def search_kayak(request: SearchRequest) -> SearchResponse:
    """Recherche vols multi-city via Kayak."""
    # Appel direct KayakSearchService (ou KayakProvider)
    return await kayak_search_service.search_flights(request)
```

**Note route Google** : L'ancienne route `/search-flights` devient `/search-google-flights` pour clarté et cohérence.

---

### 3. SearchService (app/services/search_service.py)

**Option A : 1 SearchService avec injection provider**

```python
class SearchService:
    """Service orchestration recherche vols."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        provider: FlightProvider,  # ✅ Provider injecté (pas factory)
    ) -> None:
        self.combination_generator = combination_generator
        self.provider = provider

    async def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Recherche avec provider injecté."""
        # Génère combinaisons
        combinations = self.combination_generator.generate(...)

        # Délègue au provider injecté
        results = await self.provider.search(request)

        # Ranking Top 10
        return SearchResponse(...)
```

**Injection dans routes** :
```python
# Instanciation services
google_provider = GoogleFlightsProvider(...)
kayak_provider = KayakProvider(...)

google_search_service = SearchService(combination_generator, google_provider)
kayak_search_service = SearchService(combination_generator, kayak_provider)
```

**Option B : 2 SearchService spécialisés**

```python
class GoogleSearchService:
    """Service recherche Google Flights."""
    def __init__(self, combination_generator, google_provider):
        ...

class KayakSearchService:
    """Service recherche Kayak."""
    def __init__(self, combination_generator, kayak_provider):
        ...
```

**Recommandation** : **Option A** (1 SearchService réutilisable avec injection provider) - Plus flexible et moins de duplication.

---

### 4. ProviderFactory (app/services/providers/factory.py)

**Statut** : **CONSERVÉ** mais **usage modifié**

**AVANT** : Utilisé directement dans routes pour sélection runtime
**APRÈS** : Utilisé uniquement pour **instanciation initiale** des services (startup)

```python
class ProviderFactory:
    """Factory pour instanciation providers (utilisé au startup uniquement)."""

    def __init__(
        self,
        google_provider: GoogleFlightsProvider,
        kayak_provider: KayakProvider,
    ) -> None:
        self._providers = {
            "google_flights": google_provider,
            "kayak": kayak_provider,
        }

    def get_provider(self, name: str) -> FlightProvider:
        """Retourne provider selon nom (utilisé au startup pour injection)."""
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
        return self._providers[name]
```

**Usage dans main.py (startup)** :
```python
# Instanciation providers
factory = ProviderFactory(google_provider, kayak_provider)

# Injection dans services
google_search_service = SearchService(
    combination_generator,
    factory.get_provider("google_flights")
)
kayak_search_service = SearchService(
    combination_generator,
    factory.get_provider("kayak")
)
```

---

## 📝 Tests à Modifier

### Tests Unitaires (12 tests)

**Modules concernés** :
- `tests/unit/test_models.py` : Supprimer tests validation `provider` field
- `tests/unit/test_search_service.py` : Adapter tests injection provider (pas factory)
- `tests/unit/test_provider_factory.py` : **CONSERVER** (toujours utilisé au startup)

**Tests à supprimer** :
- ❌ `test_search_request_with_provider_google`
- ❌ `test_search_request_with_provider_kayak`
- ❌ `test_search_request_without_provider_defaults_google`
- ❌ `test_search_request_invalid_provider`

**Tests à ajouter** :
- ✅ `test_search_service_with_google_provider_injected`
- ✅ `test_search_service_with_kayak_provider_injected`

---

### Tests Intégration (3 tests actuels → 4 tests nouveaux)

**Fichier** : `tests/integration/test_api_routes.py`

**AVANT** :
```python
def test_search_with_google_provider(client):
    response = client.post("/api/v1/search-flights", json={
        "template_url": "...",
        "segments_date_ranges": [...],
        "provider": "google_flights"  # ❌
    })
    assert response.status_code == 200

def test_search_with_kayak_provider(client):
    response = client.post("/api/v1/search-flights", json={
        "template_url": "...",
        "segments_date_ranges": [...],
        "provider": "kayak"  # ❌
    })
    assert response.status_code == 200

def test_search_without_provider_defaults_google(client):
    response = client.post("/api/v1/search-flights", json={
        "template_url": "...",
        "segments_date_ranges": [...]
        # Pas de provider → default Google
    })
    assert response.status_code == 200
```

**APRÈS** :
```python
def test_search_google_flights_route(client):
    """Test route dédiée Google Flights."""
    response = client.post("/api/v1/search-google-flights", json={
        "template_url": "https://www.google.com/travel/flights?tfs=...",
        "segments_date_ranges": [...]
    })
    assert response.status_code == 200
    assert "results" in response.json()

def test_search_kayak_route(client):
    """Test route dédiée Kayak."""
    response = client.post("/api/v1/search-kayak", json={
        "template_url": "https://www.kayak.fr/flights/...",
        "segments_date_ranges": [...]
    })
    assert response.status_code == 200
    assert "results" in response.json()

def test_google_route_with_kayak_url_works(client):
    """Vérifie que route Google accepte tout template_url (pas de validation provider)."""
    response = client.post("/api/v1/search-google-flights", json={
        "template_url": "https://www.kayak.fr/flights/...",  # URL Kayak mais route Google
        "segments_date_ranges": [...]
    })
    # Devrait passer validation (template_url est juste string)
    assert response.status_code == 200

def test_kayak_route_with_google_url_works(client):
    """Vérifie que route Kayak accepte tout template_url."""
    response = client.post("/api/v1/search-kayak", json={
        "template_url": "https://www.google.com/travel/flights?tfs=...",
        "segments_date_ranges": [...]
    })
    assert response.status_code == 200
```

**Note importante** : Les routes ne valident PAS le format de `template_url` par rapport au provider. La route détermine le provider, et le provider utilise son URL builder adapté. Donc Google peut recevoir URL Kayak (et vice-versa) sans erreur validation, mais le scraping échouera logiquement.

---

## 🎯 Critères Acceptation Modifiés

### Critères fonctionnels

**AVANT (ligne 540-543)** :
1. ~~Provider sélectionnable via champ `provider`~~
2. ~~Backward compatible (default Google)~~
3. Format unifié SearchResponse ✅ **CONSERVÉ**
4. ~~Provider invalide rejeté (HTTP 422)~~

**APRÈS** :
1. **2 routes distinctes** : `/search-google-flights` et `/search-kayak` disponibles
2. **Route renommée** : Ancienne `/search-flights` devient `/search-google-flights`
3. **Format unifié** : SearchResponse identique pour les 2 routes
4. **SearchRequest simplifié** : Suppression champ `provider` (déterminé par route)

### Critères techniques

**AVANT (ligne 551-556)** :
11. ~~Literal["google_flights", "kayak"] dans SearchRequest~~
12. ABC compliance FlightProvider ✅ **CONSERVÉ**
13. Factory pattern ✅ **CONSERVÉ** (usage startup uniquement)
14. Injection dépendances ✅ **CONSERVÉ** (provider injecté dans SearchService)
15. PEP 695 types ✅ **CONSERVÉ**
16. ConfigDict extra="forbid" ✅ **CONSERVÉ**

**APRÈS** :
11. **Pas de validation provider** : SearchRequest ne contient plus `provider`
12. **ABC compliance** : FlightProvider conservé (utilisé par providers)
13. **Factory usage** : ProviderFactory utilisé uniquement au startup (injection services)
14. **Route-level provider selection** : Route détermine provider (pas paramètre request)

### Critères tests

**AVANT (ligne 560-561)** :
- 12 tests unitaires (3 ABC + 3 Google + 3 Kayak + 3 Factory)
- 3 tests intégration (Google + Kayak + default)

**APRÈS** :
- **10-12 tests unitaires** : Supprimer tests validation `provider`, conserver ABC/Factory/Providers
- **4 tests intégration** : 2 routes principales + 2 tests cross-URL (optionnels mais recommandés)

---

## 📚 Documentation Impactée

### Fichiers à modifier :

1. **story-13-orchestration.md** (ce document) :
   - Section 5 (SearchRequest) : Supprimer champ `provider`
   - Section 6 (SearchService) : Adapter injection provider (pas factory)
   - Section Tests : Modifier tests intégration (446-448)
   - Exemples JSON (456-533) : Supprimer `"provider": "..."` des requests

2. **docs/ARCHITECTURE.md** (si existant) :
   - Diagramme routes API : Ajouter 2 routes séparées
   - Section multi-provider : Expliquer choix 2 routes vs 1 route+param

3. **README.md** :
   - Exemples cURL : Montrer les 2 routes
   ```bash
   # Google Flights
   curl -X POST http://localhost:8000/api/v1/search-google-flights \
     -H "Content-Type: application/json" \
     -d '{"template_url": "...", "segments_date_ranges": [...]}'

   # Kayak
   curl -X POST http://localhost:8000/api/v1/search-kayak \
     -H "Content-Type: application/json" \
     -d '{"template_url": "...", "segments_date_ranges": [...]}'
   ```

4. **OpenAPI/Swagger** (auto-généré FastAPI) :
   - 2 endpoints distincts dans documentation interactive
   - Descriptions spécifiques par route

---

## ✅ Checklist Implémentation

### Phase 1 : Models & Core
- [ ] Supprimer champ `provider` de `SearchRequest` (app/models/request.py)
- [ ] Supprimer validator `validate_provider` de `SearchRequest`
- [ ] Adapter `SearchService` pour injection provider (app/services/search_service.py)
- [ ] Conserver `ProviderFactory` mais documenter usage startup uniquement

### Phase 2 : Routes API
- [ ] Renommer route `/search-flights` → `/search-google-flights`
- [ ] Créer nouvelle route `/search-kayak`
- [ ] Injecter `google_search_service` dans route Google
- [ ] Injecter `kayak_search_service` dans route Kayak
- [ ] Supprimer logique factory dans routes (provider déjà injecté)

### Phase 3 : Tests Unitaires
- [ ] Supprimer tests validation `provider` dans `test_models.py`
- [ ] Adapter tests `test_search_service.py` (injection provider au lieu factory)
- [ ] Conserver tests `test_provider_factory.py` (toujours utilisé)
- [ ] Vérifier tous tests unitaires passent (≥ 10 tests)

### Phase 4 : Tests Intégration
- [ ] Créer `test_search_google_flights_route`
- [ ] Créer `test_search_kayak_route`
- [ ] (Optionnel) Créer tests cross-URL (route Google avec URL Kayak, etc.)
- [ ] Supprimer anciens tests avec paramètre `provider`
- [ ] Vérifier tous tests intégration passent (4 tests)

### Phase 5 : Documentation
- [ ] Modifier story-13-orchestration.md (sections SearchRequest, SearchService, Tests)
- [ ] Mettre à jour exemples JSON (supprimer `"provider": "..."`)
- [ ] Ajouter exemples cURL 2 routes dans README.md
- [ ] Vérifier OpenAPI/Swagger affiche correctement 2 routes

### Phase 6 : Validation Finale
- [ ] `ruff check . && ruff format .` : 0 erreurs
- [ ] `mypy app/` : 0 erreurs
- [ ] `pytest tests/unit/` : Tous tests passent
- [ ] `pytest tests/integration/` : Tous tests passent
- [ ] Test manuel `curl` sur les 2 routes : Succès
- [ ] Vérifier logs structurés (provider tracé dans extra)

---

## 🚀 Avantages Architecture 2 Routes

### ✅ Avantages

1. **Clarté** : Client sait exactement quel provider il appelle
2. **Validation spécifique** : Possibilité future d'ajouter validation URL par provider
3. **Paramètres provider-specific** : Kayak peut avoir `polling_max_wait`, Google non
4. **OpenAPI doc** : 2 endpoints distincts dans Swagger (meilleure UX)
5. **Évolution indépendante** : Ajouter param Kayak n'impacte pas route Google
6. **Pas de validation runtime provider** : Erreur 404 si route inexistante (plus clair que 422)

### ⚠️ Inconvénients (mineurs)

1. **Duplication routes** : 2 fonctions routes au lieu d'1 (acceptable avec injection)
2. **Pas de default provider** : Client doit choisir explicitement (mais c'est voulu)
3. **Refactoring tests** : 4 tests intégration au lieu de 3 (marginal)

---

## 📌 Notes Implémentation

### Conservation ABC + Factory

**FlightProvider (ABC)** : ✅ **CONSERVÉ**
- Toujours utilisé par GoogleFlightsProvider et KayakProvider
- Abstraction utile pour tests (mocks) et extensibilité future

**ProviderFactory** : ✅ **CONSERVÉ** (usage modifié)
- **Avant** : Utilisé dans routes pour sélection runtime
- **Après** : Utilisé uniquement au startup pour injection dans SearchService
- **Avantage** : Facilite instanciation initiale (1 lieu central)

### Injection Dépendances

**Startup (main.py ou app init)** :
```python
# Instanciation providers
google_provider = GoogleFlightsProvider(crawler_service, flight_parser)
kayak_provider = KayakProvider(url_builder, polling_service, kayak_parser)

# Factory (optionnel mais pratique pour organisation)
factory = ProviderFactory(google_provider, kayak_provider)

# Instanciation services avec injection provider
google_search_service = SearchService(
    combination_generator,
    factory.get_provider("google_flights")
)
kayak_search_service = SearchService(
    combination_generator,
    factory.get_provider("kayak")
)

# Routes utilisent les services injectés
@router.post("/search-google-flights")
async def search_google_flights(request: SearchRequest):
    return await google_search_service.search_flights(request)
```

---

## 🔗 Références

**Fichiers Story 13 concernés** :
- Section 5 (SearchRequest) : Ligne 280-325
- Section 6 (SearchService) : Ligne 328-390
- Tests intégration : Ligne 446-448
- Exemples JSON : Ligne 456-533
- Critères acceptation : Ligne 537-572

**User feedback** :
> "Ok pour les routes et prévoir dans la story ou tu crée la route kayak de renommer google flights et penser à adapter les tests unitaires et surtotu integration"

**Décision confirmée** : 2 routes séparées (`/search-google-flights`, `/search-kayak`) au lieu de 1 route unifiée avec paramètre `provider`.
