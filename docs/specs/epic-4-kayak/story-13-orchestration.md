---
title: "Story 13: Multi-Provider Orchestration"
epic: "Epic 4: Kayak Integration"
story_points: 8
dependencies: ["epic-4/story-12"]
date: "2025-11-25"
keywords: ["orchestration", "provider", "factory", "abstraction", "google-flights", "kayak", "multi-provider"]
scope: ["specs"]
technologies: ["Python", "ABC", "Factory Pattern", "PEP 695", "Pydantic v2"]
---

# Contexte Business

## Besoin utilisateur
- Permettre au client de choisir le provider de recherche (Google Flights ou Kayak)
- Préparer l'architecture pour ajouter facilement de nouveaux providers futurs (Skyscanner, Expedia, etc.)
- Garantir interface uniforme de sortie (GoogleFlightDTO) quelque soit le provider
- Maintenir backward compatibility avec les clients existants utilisant Google Flights par défaut

## Contraintes métier
- Provider Google Flights doit rester le défaut (backward compatible)
- Tous les providers retournent le même format de sortie (GoogleFlightDTO)
- SearchRequest doit accepter le provider en paramètre optionnel
- Erreur explicite si provider demandé n'existe pas
- Aucun changement breaking pour les API existantes

## Valeur business
- Flexibilité client : choisir provider selon besoin (latence Kayak vs fiabilité Google)
- Résilience : basculer sur provider backup si un est down
- Évolutivité : ajouter nouveaux providers sans refactoring majeur
- Métriques provider-specific : comparer prix moyen, latence, taux succès entre Google et Kayak

## Métriques succès
- POST /search accepte paramètre `provider` avec valeurs `google_flights` | `kayak`
- Provider invalide retourne HTTP 400 avec message explicite
- Réponse format identique (SearchResponse) quelque soit provider
- Temps réponse comparable : Google ~10-15s, Kayak ~20-30s
- Tests passent : 12 unitaires + 3 intégration = 15 tests total

---

# Spécifications Techniques

## 1. FlightProvider (Abstract Base Class)

**Rôle** : Définir interface commune pour tous les providers de recherche vols. Force implémentation méthode `search()` et propriété `name`.

**Interface** :
```python
class FlightProvider(ABC):
    """Interface abstraite pour providers de recherche vols."""

    @abstractmethod
    async def search(self, request: SearchRequest) -> list[GoogleFlightDTO]:
        """
        Recherche vols selon SearchRequest.

        Args:
            request: Requête avec template_url et segments_date_ranges

        Returns:
            Liste GoogleFlightDTO (format unifié) triée par prix croissant

        Raises:
            NotImplementedError: Si provider non implémenté
            CaptchaDetectedError: Si captcha bloque scraping
            NetworkError: Si erreur réseau/timeout
            ParsingError: Si extraction données échoue
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nom unique du provider (identifiant).

        Returns:
            Nom provider (ex: "google_flights", "kayak")
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `search()` | `abstractmethod` | Méthode recherche vols | Doit être implémentée par sous-classes |
| `name` | `property abstractmethod` | Property nom provider | Doit être implémentée par sous-classes |

**Comportement** :
- Classe abstraite (ABC) ne peut pas être instanciée directement
- Force héritage et implémentation des méthodes abstraites
- Méthode `search()` retourne TOUJOURS `list[GoogleFlightDTO]` (format unifié)
- Property `name` retourne identifiant unique (utilisé par factory)

**Validations** :
- Tentative instanciation directe lève `TypeError`
- Classe héritant sans implémenter méthodes abstraites lève `TypeError`

---

## 2. GoogleFlightsProvider

**Rôle** : Implémentation concrète de FlightProvider pour Google Flights. Délègue crawling à CrawlerService et parsing à FlightParser existants.

**Interface** :
```python
class GoogleFlightsProvider(FlightProvider):
    """Provider Google Flights utilisant CrawlerService + FlightParser."""

    def __init__(self, crawler_service: CrawlerService, flight_parser: FlightParser) -> None:
        """
        Initialise provider avec services injectés.

        Args:
            crawler_service: Service crawling Google Flights
            flight_parser: Parser HTML Google Flights → GoogleFlightDTO
        """

    async def search(self, request: SearchRequest) -> list[GoogleFlightDTO]:
        """
        Recherche vols via Google Flights.

        Délègue à :
        - CrawlerService.crawl_google_flights() pour crawling
        - FlightParser.parse() pour extraction données

        Returns:
            Liste GoogleFlightDTO triée par prix croissant
        """

    @property
    def name(self) -> str:
        """Retourne "google_flights"."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `crawler_service` | `CrawlerService` | Service crawling Google Flights | Requis, injecté |
| `flight_parser` | `FlightParser` | Parser HTML → GoogleFlightDTO | Requis, injecté |

**Comportement** :
- Réutilise exactement CrawlerService et FlightParser existants (aucun changement)
- Génère URL via `generate_google_flights_url()` (utilité existante)
- Délègue crawling multi-combinaisons (logique existante dans SearchService)
- Retourne résultats format GoogleFlightDTO (déjà implémenté)

**Validations** :
- Vérifie `request.template_url` valide (déjà fait par SearchRequest validator)
- Lève exceptions si crawling échoue (déjà géré par CrawlerService)

---

## 3. KayakProvider

**Rôle** : Implémentation concrète de FlightProvider pour Kayak. Compose KayakUrlBuilder, ConsentHandler, PollingService, KayakFlightParser.

**Interface** :
```python
class KayakProvider(FlightProvider):
    """Provider Kayak avec polling et consent handler."""

    def __init__(
        self,
        crawler_service: CrawlerService,
        kayak_parser: KayakFlightParser,
        polling_service: PollingService,
        url_builder: KayakUrlBuilder,
    ) -> None:
        """
        Initialise provider Kayak avec services spécifiques.

        Args:
            crawler_service: Service crawling générique
            kayak_parser: Parser JSON Kayak → GoogleFlightDTO
            polling_service: Service polling résultats progressifs
            url_builder: Builder URL Kayak
        """

    async def search(self, request: SearchRequest) -> list[GoogleFlightDTO]:
        """
        Recherche vols via Kayak avec polling.

        Flow :
        1. Construire URL Kayak via KayakUrlBuilder
        2. Crawl page avec CrawlerService (consent handled)
        3. Polling résultats via PollingService (max 45s)
        4. Parser JSON via KayakFlightParser
        5. Retourner Top 10 triés par prix

        Returns:
            Liste GoogleFlightDTO triée par prix croissant
        """

    @property
    def name(self) -> str:
        """Retourne "kayak"."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `crawler_service` | `CrawlerService` | Service crawling réutilisé | Requis, injecté |
| `kayak_parser` | `KayakFlightParser` | Parser JSON Kayak | Requis, injecté (Story 4.2) |
| `polling_service` | `PollingService` | Service polling async | Requis, injecté (Story 4.3) |
| `url_builder` | `KayakUrlBuilder` | Builder URL Kayak | Requis, injecté (Story 4.1) |

**Comportement** :
- Flow asynchrone : crawl → polling → parsing → ranking
- Consent handler appelé automatiquement par CrawlerService (Story 4.1)
- Polling max 45s puis timeout gracieux (Story 4.3)
- Conversion format Kayak → GoogleFlightDTO (Story 4.2)
- Ranking identique à GoogleFlightsProvider (tri prix croissant)

**Validations** :
- Vérifie structure JSON Kayak valide (responsabilité KayakFlightParser)
- Timeout si polling > 45s (responsabilité PollingService)
- Retourne liste vide si parsing échoue (log warning)

---

## 4. ProviderFactory

**Rôle** : Factory pattern pour instancier provider selon nom. Simplifie injection dépendances et gère registry providers disponibles.

**Interface** :
```python
class ProviderFactory:
    """Factory pour obtenir provider selon nom."""

    def __init__(
        self,
        google_provider: GoogleFlightsProvider,
        kayak_provider: KayakProvider,
    ) -> None:
        """
        Initialise factory avec providers pré-configurés.

        Args:
            google_provider: Provider Google Flights
            kayak_provider: Provider Kayak
        """

    def get_provider(self, name: str) -> FlightProvider:
        """
        Retourne provider selon nom.

        Args:
            name: Nom provider ("google_flights" | "kayak")

        Returns:
            Instance FlightProvider correspondante

        Raises:
            ValueError: Si provider name inconnu
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `google_provider` | `GoogleFlightsProvider` | Provider Google pré-configuré | Requis, injecté |
| `kayak_provider` | `KayakProvider` | Provider Kayak pré-configuré | Requis, injecté |
| `_providers` | `dict[str, FlightProvider]` | Registry interne | Privé, initialisé dans __init__ |

**Comportement** :
- Registry interne : `{"google_flights": google_provider, "kayak": kayak_provider}`
- Méthode `get_provider()` lookup dans registry
- Lève ValueError avec message explicite si provider inconnu
- Extensible : ajouter nouveau provider = ajouter dans __init__ et registry

**Validations** :
- Lève `ValueError("Unknown provider: {name}. Available: google_flights, kayak")` si nom invalide

---

## 5. SearchRequest (Modifié)

**Rôle** : Ajouter champ optionnel `provider` pour sélection provider. Backward compatible (default = google_flights).

**Interface modifiée** :
```python
class SearchRequest(BaseModel):
    """Requête recherche vols multi-city avec provider sélectionnable."""

    template_url: str
    segments_date_ranges: list[DateRange]
    provider: Literal["google_flights", "kayak"] = "google_flights"

    @field_validator("provider", mode="after")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """
        Valide provider disponible.

        Args:
            v: Nom provider

        Returns:
            Nom provider validé

        Raises:
            ValueError: Si provider non supporté
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `provider` | `Literal["google_flights", "kayak"]` | Provider de recherche | Optionnel, default = "google_flights" |

**Comportement** :
- **Validation stricte** : ConfigDict `extra="forbid"` rejette champs inconnus avec ValidationError
- Champ optionnel avec default "google_flights" (backward compatible)
- Literal type force validation Pydantic (seulement valeurs autorisées)
- Validation custom redondante mais explicite (message erreur clair)

**Validations** :
- Pydantic rejette automatiquement valeur hors Literal
- Validator custom lève ValueError si valeur non supportée (message explicite)

---

## 6. SearchService (Modifié)

**Rôle** : Utiliser ProviderFactory pour obtenir provider selon SearchRequest.provider. Déléguer search au provider sélectionné.

**Interface modifiée** :
```python
class SearchService:
    """Service orchestration recherche vols avec support multi-provider."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        provider_factory: ProviderFactory,
    ) -> None:
        """
        Initialise service avec factory provider.

        Args:
            combination_generator: Génère combinaisons dates
            provider_factory: Factory pour obtenir provider
        """

    async def search_flights(self, request: SearchRequest) -> SearchResponse:
        """
        Orchestre recherche complète avec provider sélectionné.

        Flow :
        1. Obtenir provider via factory (request.provider)
        2. Générer combinaisons dates (inchangé)
        3. Déléguer search au provider
        4. Ranking Top 10 (inchangé)
        5. Construire SearchResponse (inchangé)

        Args:
            request: Requête avec provider sélectionné

        Returns:
            SearchResponse avec Top 10 résultats

        Raises:
            ValueError: Si provider inconnu (factory)
            CaptchaDetectedError: Si captcha détecté
            NetworkError: Si erreur réseau
        """
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `provider_factory` | `ProviderFactory` | Factory provider | Requis, injecté (remplace crawler_service/parser) |
| `combination_generator` | `CombinationGenerator` | Générateur combinaisons | Inchangé, requis |

**Comportement** :
- Obtient provider via `provider_factory.get_provider(request.provider)`
- Génère combinaisons dates (délègue à CombinationGenerator)
- Délègue search complet au provider (plus de logique crawl/parsing dans SearchService)
- Ranking et conversion format réponse inchangés

**Changements par rapport à version actuelle** :
- Supprime dépendances `crawler_service` et `flight_parser` (remplacées par factory)
- Supprime méthodes `_crawl_all_combinations()`, `_parse_all_results()` (déléguées au provider)
- Garde méthodes `_rank_and_select_top_10()`, `_convert_to_flight_results()` (inchangées)

**Validations** :
- Lève ValueError si provider inconnu (déléguée à factory)
- Propage exceptions provider (CaptchaDetectedError, NetworkError, ParsingError)

---

# Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### FlightProvider ABC (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_flight_provider_cannot_instantiate` | Tentative instanciation directe ABC | `FlightProvider()` | Lève `TypeError` | Vérifie ABC ne peut pas être instancié |
| 2 | `test_flight_provider_forces_search_implementation` | Classe hérite sans implémenter search() | Classe sans `async def search()` | Lève `TypeError` | Vérifie méthode abstraite forcée |
| 3 | `test_flight_provider_forces_name_property` | Classe hérite sans implémenter name | Classe sans `@property name` | Lève `TypeError` | Vérifie property abstraite forcée |

### GoogleFlightsProvider (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 4 | `test_google_provider_search_success` | Search avec request valide (mock) | SearchRequest valide | Liste GoogleFlightDTO triée prix | Vérifie délégation crawler + parser |
| 5 | `test_google_provider_name_property` | Récupérer nom provider | `provider.name` | `"google_flights"` | Vérifie identifiant unique |
| 6 | `test_google_provider_search_propagates_exceptions` | Crawler lève CaptchaDetectedError | Request valide, crawler mock error | Lève `CaptchaDetectedError` | Vérifie propagation exceptions |

### KayakProvider (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 7 | `test_kayak_provider_search_success` | Search avec polling mock | SearchRequest valide | Liste GoogleFlightDTO triée prix | Vérifie composition url_builder + polling + parser |
| 8 | `test_kayak_provider_name_property` | Récupérer nom provider | `provider.name` | `"kayak"` | Vérifie identifiant unique |
| 9 | `test_kayak_provider_search_timeout_graceful` | Polling timeout après 45s | Request valide, polling mock timeout | Retourne liste vide OU résultats partiels | Vérifie timeout gracieux |

### ProviderFactory (3 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 10 | `test_factory_get_google_provider` | Obtenir provider Google | `factory.get_provider("google_flights")` | Instance GoogleFlightsProvider | Vérifie registry lookup |
| 11 | `test_factory_get_kayak_provider` | Obtenir provider Kayak | `factory.get_provider("kayak")` | Instance KayakProvider | Vérifie registry lookup |
| 12 | `test_factory_unknown_provider_raises` | Provider inconnu | `factory.get_provider("skyscanner")` | Lève `ValueError` avec message explicite | Vérifie validation registry |

**Total tests unitaires** : 12 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_search_with_google_provider` | App running, mocks configurés | POST /api/v1/search-flights avec `provider: "google_flights"` | Status 200 + SearchResponse valide |
| 2 | `test_search_with_kayak_provider` | App running, mocks configurés | POST /api/v1/search-flights avec `provider: "kayak"` | Status 200 + SearchResponse valide |
| 3 | `test_search_without_provider_defaults_google` | App running, mocks configurés | POST /api/v1/search-flights SANS champ `provider` | Status 200 + SearchResponse (default Google) |

**Total tests intégration** : 3 tests

---

## Exemples JSON

**Exemple 1 : Request avec provider Google (explicite)** :
```json
{
  "template_url": "https://www.google.com/travel/flights?tfs=CBwQAhopEgoyMDI2LTAxLTE0agcIARIDUEFScgcIARIDU0xaGAEgASgAMAFAAEgBmAEB",
  "segments_date_ranges": [
    {"start": "2026-01-14", "end": "2026-01-20"},
    {"start": "2026-03-28", "end": "2026-04-03"}
  ],
  "provider": "google_flights"
}
```

**Exemple 2 : Request avec provider Kayak** :
```json
{
  "template_url": "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a",
  "segments_date_ranges": [
    {"start": "2026-01-14", "end": "2026-01-20"},
    {"start": "2026-03-28", "end": "2026-04-03"},
    {"start": "2026-04-10", "end": "2026-04-16"}
  ],
  "provider": "kayak"
}
```

**Exemple 3 : Request sans provider (default Google)** :
```json
{
  "template_url": "https://www.google.com/travel/flights?tfs=CBwQAhopEgoyMDI2LTAxLTE0agcIARIDUEFScgcIARIDU0xaGAEgASgAMAFAAEgBmAEB",
  "segments_date_ranges": [
    {"start": "2026-01-14", "end": "2026-01-20"},
    {"start": "2026-03-28", "end": "2026-04-03"}
  ]
}
```

**Exemple 4 : Response succès (identique Google et Kayak)** :
```json
{
  "results": [
    {
      "segment_dates": ["2026-01-14", "2026-03-28"],
      "flights": [
        {
          "price": 1250.00,
          "airline": "Air France",
          "departure_time": "2026-01-14T10:30:00",
          "arrival_time": "2026-01-14T22:45:00",
          "duration": "12h15",
          "stops": 0,
          "departure_airport": "Paris CDG",
          "arrival_airport": "Salvador Intl"
        }
      ]
    }
  ],
  "search_stats": {
    "total_results": 10,
    "search_time_ms": 15234,
    "segments_count": 2
  }
}
```

**Exemple 5 : Error response provider invalide (HTTP 422)** :
```json
{
  "detail": [
    {
      "type": "literal_error",
      "loc": ["body", "provider"],
      "msg": "Input should be 'google_flights' or 'kayak'",
      "input": "skyscanner",
      "ctx": {"expected": "'google_flights' or 'kayak'"}
    }
  ]
}
```

---

# Critères d'acceptation

## Critères fonctionnels
1. **Provider sélectionnable** : SearchRequest accepte champ `provider` avec valeurs `"google_flights"` | `"kayak"`
2. **Backward compatible** : Requêtes sans champ `provider` utilisent Google Flights par défaut
3. **Format unifié** : Réponse SearchResponse identique quelque soit provider sélectionné
4. **Provider invalide rejeté** : Valeur `provider` hors Literal retourne HTTP 422 avec message explicite
5. **Abstraction FlightProvider** : Classe ABC force implémentation search() et name property
6. **Factory functional** : ProviderFactory.get_provider() retourne provider correct selon nom
7. **Google provider fonctionnel** : GoogleFlightsProvider délègue à CrawlerService + FlightParser existants sans régression
8. **Kayak provider fonctionnel** : KayakProvider compose url_builder + polling + parser (Stories 4.1-4.3)
9. **SearchService refactoré** : SearchService utilise ProviderFactory pour sélection provider dynamique
10. **Exceptions propagées** : CaptchaDetectedError, NetworkError, ParsingError remontent depuis providers vers API

## Critères techniques
11. **Type safety strict** : Literal["google_flights", "kayak"] dans SearchRequest force validation Pydantic
12. **ABC compliance** : FlightProvider respecte ABC protocol (abstractmethod + property)
13. **Factory pattern** : ProviderFactory utilise registry interne dict[str, FlightProvider]
14. **Injection dépendances** : Tous services (providers, factory) injectés via __init__ (pas d'instanciation directe)
15. **PEP 695 types** : Annotations modernes (`list[GoogleFlightDTO]`, `dict[str, FlightProvider]`)
16. **ConfigDict extra="forbid"** : SearchRequest rejette champs inconnus (sécurité)

## Critères qualité
17. **Tests unitaires passent** : 12 tests (3 ABC + 3 Google + 3 Kayak + 3 Factory) tous verts
18. **Tests intégration passent** : 3 tests (Google + Kayak + default) tous verts
19. **Coverage ≥ 80%** : app/services/providers/ couvert à minimum 80%
20. **Mypy strict** : Aucune erreur type checking sur modules providers
21. **Ruff compliant** : Code passe ruff check + ruff format sans erreur
22. **Docstrings complets** : Toutes classes et méthodes publiques documentées (1 ligne minimum)

## Critères production (si applicable)
23. **Logs provider** : Logger provider sélectionné dans extra (ex: `{"provider": "kayak"}`)
24. **Timing metrics** : Logger search_time_ms par provider pour comparer performances
25. **Error handling** : ValueError factory logged avec contexte (provider demandé + disponibles)
26. **Extensibilité** : Ajouter nouveau provider = créer classe + ajouter dans factory (pas de changement SearchService)
