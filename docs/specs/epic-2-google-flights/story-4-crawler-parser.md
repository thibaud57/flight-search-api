---
title: "Story 4: Crawler + Parser (1 destination)"
epic: "Epic 2: Google Flights Scraping"
story_points: 8
dependencies: ["story-3"]
date: "2025-18-11"
keywords: ["crawler", "parser", "google-flights", "crawl4ai", "scraping", "css-extraction", "anti-detection", "captcha-detection", "decodo-proxies"]
scope: ["specs"]
technologies: ["Crawl4AI", "AsyncWebCrawler", "JsonCssExtractionStrategy", "Decodo Proxies", "Playwright"]
---

# 🎯 Contexte Business

## Besoin utilisateur

### Persona 1: Product Owner
- Besoin de proof of concept scraping réel avant investissement multi-destinations complexe
- Validation technique extraction CSS Google Flights sans dépendance LLM (coût zéro)
- Feedback early sur taux de succès parsing et détection captcha
- Démonstration capacité anti-détection avec Decodo proxies résidentiels

### Persona 2: Développeur Backend (ce projet)
- Besoin de valider stack Crawl4AI + JsonCssExtractionStrategy sur cas simple (1 destination)
- Dérisquage technique avant scaling multi-city (complexité combinatoire Phase 6+)
- Foundation services crawler + parser réutilisables pour toutes stories futures
- Validation intégration Decodo proxies France (country targeting, rotation, stealth mode)

### Persona 3: Utilisateur Final API
- Besoin de données vols réelles (pas mock) pour destination unique Paris → Tokyo
- Prix, compagnie, horaires extraits depuis Google Flights en temps réel
- Résultats Top 10 triés par prix croissant (préparation ranking multi-city)

## Contraintes métier

### Contraintes fonctionnelles
- **1 destination uniquement** : Paris → Tokyo (aller-retour), pas de multi-city dans cette story
- **Top 10 résultats** : Extraction et tri par prix croissant, limite 10 résultats max
- **Format dates** : ISO 8601 (YYYY-MM-DD), plage date_range utilisée pour construction URL
- **Devise EUR** : Paramètre `curr=EUR` dans URL Google Flights

### Contraintes techniques
- **Extraction CSS uniquement** : JsonCssExtractionStrategy, 0 coût LLM, parsing déterministe
- **Pas de base de données** : Résultats retournés en mémoire directement (liste Python)
- **Decodo proxies obligatoires** : Format `customer-{api_key}-country-FR:password`, targeting France
- **Stealth mode activé** : BrowserConfig `enable_stealth=True`, headless=True
- **Type safety strict** : PEP 695 type hints, Mypy strict mode

### Contraintes performance et coûts
- **Bandwidth Decodo limité** : 1 crawl = ~500KB-2MB HTML, optimiser nombre requêtes
- **Timeout crawl 30s** : AsyncWebCrawler timeout max 30 secondes par URL
- **Pas de retry dans cette story** : Retry logic avec Tenacity reporté Story 7
- **Détection captcha MVP** : Détection uniquement (logging), pas de résolution (Phase 7 optionnelle)

## Valeur business

- ✅ **Validation technique extraction CSS** : Proof of concept parsing Google Flights sans LLM, validation sélecteurs CSS robustes
- ✅ **Dérisquage avant scaling** : Validation stack sur cas simple avant complexité multi-city, réduction risque erreurs architecturales
- ✅ **Foundation services réutilisables** : CrawlerService + FlightParser utilisables pour toutes stories futures (multi-city, retry, ranking)
- ✅ **Feedback early taux captcha** : Monitoring taux détection captcha pour décision Phase 7 (seuil >5% = résolution 2Captcha nécessaire)
- ✅ **Validation anti-détection** : Test Decodo proxies France + stealth mode sur Google Flights réel

## Métriques succès

### Métriques fonctionnelles
- **Taux parsing success ≥ 80%** : Sur 10 crawls test manuels, minimum 8 retournent 1+ vol
- **Temps crawl < 10s** : p95 crawl + parsing < 10 secondes (1 destination simple)
- **Top 10 résultats** : Résultats triés prix croissant, max 10 vols retournés
- **Prix positifs cohérents** : 100% résultats ont prix > 0 et < 10000 EUR (validation métier)

### Métriques qualité
- **Coverage ≥ 80%** : pytest --cov=app atteint 80%+ sur CrawlerService et FlightParser
- **18 tests passent** : 8 crawler + 7 parser + 3 intégration tous verts
- **Mypy strict mode** : 0 erreur de type
- **Ruff lint/format** : 0 erreur

### Métriques production
- **Logs structurés JSON** : Chaque crawl loggé avec extra context (url, proxy_used, captcha_detected, result_count)
- **Taux captcha detection** : Logging taux détection captcha (target < 5% pour éviter résolution coûteuse)
- **Stealth mode actif** : Vérification BrowserConfig enable_stealth=True dans logs

---

# 📋 Spécifications Techniques

## 1. CrawlerService

**Rôle** : Service orchestrant le crawl Google Flights avec AsyncWebCrawler, intégration Decodo proxies, stealth mode, et détection captcha MVP.

**Interface** :
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

class CrawlerService:
    """Service de crawling Google Flights avec anti-détection."""

    def __init__(self, proxy_service: ProxyService) -> None:
        """Initialise CrawlerService avec ProxyService injecté."""

    async def crawl_google_flights(self, url: str) -> str:
        """Crawl une URL Google Flights et retourne HTML brut.

        Args:
            url: URL Google Flights complète avec paramètres

        Returns:
            HTML brut de la page Google Flights

        Raises:
            CaptchaDetectedException: Si captcha détecté dans HTML
            CrawlException: Si crawl échoue (timeout, erreur réseau)
        """
```

**Dépendances** :
- `ProxyService` : Injection dépendance pour rotation proxies Decodo
- `AsyncWebCrawler` : Crawl4AI crawler asynchrone
- `BrowserConfig` : Configuration navigateur (stealth, proxy, user-agent)
- `CrawlerRunConfig` : Configuration exécution (cache mode, timeout)

**Configuration BrowserConfig** :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `browser_type` | `"chromium"` | Navigateur Chromium via Playwright |
| `headless` | `True` | Mode sans interface (performance) |
| `enable_stealth` | `True` | Active playwright-stealth (masque indicateurs bot) |
| `proxy` | `get_next_proxy()` | Proxy Decodo format `http://customer-{api_key}-country-FR:password@pr.decodo.com:8080` |
| `user_agent` | Pool rotation | Rotation pondérée 3+ user-agents modernes |
| `viewport` | `{"width": 1920, "height": 1080}` | Viewport standard desktop |

**Configuration CrawlerRunConfig** :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `cache_mode` | `CacheMode.BYPASS` | Pas de cache (chaque crawl frais) |
| `timeout` | `30` | Timeout max 30 secondes |

**User-Agent Pool** :
```python
USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.4),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 0.3),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", 0.3),
]
```

**Workflow crawl_google_flights** :
1. Récupérer proxy suivant via `proxy_service.get_next_proxy()`
2. Sélectionner user-agent aléatoire pondéré depuis pool
3. Construire BrowserConfig avec stealth + proxy + user-agent
4. Créer AsyncWebCrawler avec config
5. Exécuter `crawler.arun(url)` avec timeout 30s
6. Vérifier `CrawlResult.success == True`, sinon lever `CrawlException`
7. Détecter captcha dans `CrawlResult.html` via patterns regex
8. Si captcha détecté → Log WARNING + lever `CaptchaDetectedException`
9. Si succès → Log INFO + retourner HTML brut

**Détection Captcha MVP** :

**Patterns regex** :
```python
RECAPTCHA_V2_PATTERN = r'class=["\']g-recaptcha["\']'
RECAPTCHA_V3_PATTERN = r'recaptcha/api\.js\?render='
HCAPTCHA_PATTERN = r'class=["\']h-captcha["\']'
```

**Comportement si captcha détecté** :
```python
import logging

logger = logging.getLogger(__name__)

if any([re.search(pattern, html) for pattern in CAPTCHA_PATTERNS]):
    logger.warning(
        "Captcha detected",
        extra={
            "url": url,
            "proxy_used": proxy,
            "captcha_type": "recaptcha_v2"
        }
    )
    raise CaptchaDetectedException(f"Captcha detected at {url}")
```

**Logging structuré** :
```python
logger.info(
    "Starting crawl",
    extra={
        "url": url,
        "proxy": proxy,
        "user_agent": user_agent[:50]
    }
)

logger.info(
    "Crawl successful",
    extra={
        "url": url,
        "proxy_used": proxy,
        "html_size_kb": len(html) / 1024,
        "crawl_duration_ms": duration_ms
    }
)
```

**Exceptions custom** :
```python
class CrawlException(Exception):
    """Exception levée si crawl échoue."""

class CaptchaDetectedException(Exception):
    """Exception levée si captcha détecté."""
```

**Exemple usage** :
```python
from app.services.crawler_service import CrawlerService
from app.services.proxy_service import ProxyService

proxy_service = ProxyService()
crawler_service = CrawlerService(proxy_service=proxy_service)

url = "https://www.google.com/travel/flights?flight_type=2&departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01&return_date=2025-06-15&hl=fr&curr=EUR"

html = await crawler_service.crawl_google_flights(url)
print(f"HTML size: {len(html)} bytes")
```

---

## 2. FlightParser

**Rôle** : Service de parsing HTML Google Flights via JsonCssExtractionStrategy, transformation données brutes en FlightResult Pydantic.

**Interface** :
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

class FlightParser:
    """Parser HTML Google Flights via extraction CSS."""

    def __init__(self) -> None:
        """Initialise FlightParser avec schema JSON extraction."""

    def parse_flights(self, html: str, destinations: list[str]) -> list[FlightResult]:
        """Parse HTML Google Flights et extrait vols.

        Args:
            html: HTML brut depuis CrawlerService
            destinations: Liste villes recherche (pour validation itinéraire)

        Returns:
            Liste FlightResult triée par prix croissant, max 10 résultats

        Raises:
            Aucune exception levée. Retourne liste vide si parsing échoue.
        """
```

**Schema JSON Extraction** :

Basé sur analyse structure HTML Google Flights (voir section Analyse & Recherche).

```json
{
  "name": "Google Flights Results",
  "baseSelector": "div.pIav2d",
  "fields": [
    {
      "name": "price",
      "selector": "div.YMlIz.FpEdX span",
      "type": "text"
    },
    {
      "name": "airline",
      "selector": "div.sSHqwe.tPgKwe.ogfYpf span",
      "type": "text"
    },
    {
      "name": "departure_time",
      "selector": "div.zxVSec.YMlIz.tPgKwe span[aria-label*='Departure']",
      "type": "attribute",
      "attribute": "aria-label"
    },
    {
      "name": "arrival_time",
      "selector": "div.zxVSec.YMlIz.tPgKwe span[aria-label*='Arrival']",
      "type": "attribute",
      "attribute": "aria-label"
    },
    {
      "name": "duration",
      "selector": "div.gvkrdb.AdWm1c.tPgKwe",
      "type": "text"
    },
    {
      "name": "stops",
      "selector": "div.EfT7Ae.AdWm1c.tPgKwe span",
      "type": "text"
    }
  ]
}
```

**Note** : Les sélecteurs CSS ci-dessus sont **exemples basés sur structure HTML typique Google Flights**. Étape 1 de la checklist (Analyser structure HTML) doit valider et ajuster ces sélecteurs sur vraie page Google Flights en 2025.

**Workflow parse_flights** :

1. **Validation input** :
   - Si `html` vide ou None → Log WARNING + retour `[]`
   - Si `destinations` vide → Log WARNING + retour `[]`

2. **Extraction CSS** :
   ```python
   extraction_strategy = JsonCssExtractionStrategy(schema=GOOGLE_FLIGHTS_SCHEMA)
   # Note: Crawl4AI JsonCssExtractionStrategy nécessite AsyncWebCrawler
   # Parser doit recevoir JSON extrait déjà parsé, ou réutiliser crawler
   ```

3. **Transformation données** :
   - **Prix** : Extraction "1 250 €" → float 1250.00
     ```python
     def parse_price(price_str: str) -> float:
         cleaned = re.sub(r'[^\d,.]', '', price_str)
         cleaned = cleaned.replace(',', '.')
         return float(cleaned)
     ```

   - **Dates** : Extraction "1 juin" → conversion ISO "2025-06-01"
     ```python
     def parse_date(date_str: str, year: int) -> str:
         from datetime import datetime
         import locale

         locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
         date_obj = datetime.strptime(f"{date_str} {year}", "%d %B %Y")
         return date_obj.strftime("%Y-%m-%d")
     ```

   - **Compagnie** : Extraction nom complet → mapping IATA si disponible
     ```python
     AIRLINE_MAPPING = {
         "Air France": "AF",
         "Japan Airlines": "JL",
         "ANA": "NH",
     }

     def parse_airline(airline_str: str) -> str:
         return AIRLINE_MAPPING.get(airline_str, airline_str)
     ```

4. **Construction FlightResult** :
   ```python
   from app.models.response import FlightResult

   flights = []
   for raw_flight in extracted_data:
       try:
           flight = FlightResult(
               itinerary=destinations,
               price=parse_price(raw_flight["price"]),
               currency="EUR",
               departure_date=parse_date(raw_flight["departure_time"], 2025),
               return_date=parse_date(raw_flight["arrival_time"], 2025)
           )
           flights.append(flight)
       except (ValueError, KeyError) as e:
           logger.warning(
               "Failed to parse flight",
               extra={
                   "raw_data": raw_flight,
                   "error": str(e)
               }
           )
           continue
   ```

5. **Tri et limite Top 10** :
   ```python
   sorted_flights = sorted(flights, key=lambda f: f.price)
   top_10 = sorted_flights[:10]
   return top_10
   ```

**Edge cases gestion** :

| Edge case | Comportement |
|-----------|--------------|
| HTML vide | Log WARNING + retour `[]` |
| Sélecteurs non trouvés | Log ERROR avec sélecteurs manquants + retour `[]` |
| Prix format invalide | Skip vol (log WARNING) + continuer parsing autres |
| Date parsing échoue | Skip vol (log WARNING) + continuer parsing autres |
| 0 vol extrait | Log INFO "No flights found" + retour `[]` |

**Logging structuré** :
```python
logger.info(
    "Starting flight parsing",
    extra={
        "html_size_kb": len(html) / 1024,
        "destinations": destinations
    }
)

logger.info(
    "Flight parsing completed",
    extra={
        "total_extracted": len(extracted_data),
        "valid_flights": len(flights),
        "top_10_count": len(top_10),
        "price_range": f"{top_10[0].price}-{top_10[-1].price}" if top_10 else "N/A"
    }
)
```

**Exemple usage** :
```python
from app.services.flight_parser import FlightParser

parser = FlightParser()
html = "<html>... Google Flights HTML ...</html>"
destinations = ["Paris", "Tokyo"]

flights = parser.parse_flights(html=html, destinations=destinations)
print(f"Parsed {len(flights)} flights, Top 10 cheapest")
for flight in flights:
    print(f"{flight.price} EUR - {flight.airline}")
```

---

## 3. URL Construction Helper

**Rôle** : Helper fonction construisant URL Google Flights depuis SearchRequest.

**Interface** :
```python
from app.models.request import SearchRequest

def build_google_flights_url(request: SearchRequest) -> str:
    """Construit URL Google Flights pour 1 destination aller-retour.

    Args:
        request: SearchRequest avec destinations[0:2] et date_range

    Returns:
        URL Google Flights complète avec paramètres

    Example:
        >>> request = SearchRequest(
        ...     destinations=["Paris", "Tokyo"],
        ...     date_range=DateRange(start="2025-06-01", end="2025-06-15")
        ... )
        >>> url = build_google_flights_url(request)
        >>> print(url)
        https://www.google.com/travel/flights?flight_type=2&departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01&return_date=2025-06-15&hl=fr&curr=EUR
    """
```

**Mapping villes → codes IATA** :

```python
CITY_TO_IATA = {
    "Paris": "CDG",
    "Tokyo": "NRT",
    "New York": "JFK",
    "Los Angeles": "LAX",
    "London": "LHR",
}

def get_iata_code(city: str) -> str:
    """Retourne code IATA pour ville, ou ville si non trouvé."""
    return CITY_TO_IATA.get(city, city)
```

**Construction URL** :

```python
from urllib.parse import urlencode

def build_google_flights_url(request: SearchRequest) -> str:
    """Construit URL Google Flights."""
    origin = get_iata_code(request.destinations[0])
    destination = get_iata_code(request.destinations[1])

    params = {
        "flight_type": "2",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": request.date_range.start,
        "return_date": request.date_range.end,
        "hl": "fr",
        "curr": "EUR"
    }

    base_url = "https://www.google.com/travel/flights"
    return f"{base_url}?{urlencode(params)}"
```

**Validation** :
- Si `len(request.destinations) < 2` → Lever `ValueError`
- Si `request.date_range.start >= request.date_range.end` → Lever `ValueError` (déjà validé par Pydantic)

---

## 4. Intégration SearchService (modification)

**Modification SearchService existant** :

Remplacer mock implementation (Story 3) par vraie logique crawling + parsing.

**Nouvelle signature** :
```python
class SearchService:
    """Service orchestration recherche vols."""

    def __init__(
        self,
        crawler_service: CrawlerService,
        flight_parser: FlightParser
    ) -> None:
        """Initialise SearchService avec dépendances injectées."""

    async def search_flights(self, request: SearchRequest) -> list[FlightResult]:
        """Recherche vols réels via Google Flights.

        Args:
            request: SearchRequest avec destinations (min 2) et date_range

        Returns:
            Liste FlightResult Top 10 triée prix croissant

        Raises:
            CaptchaDetectedException: Si captcha bloque crawl
            CrawlException: Si crawl échoue
        """
```

**Workflow search_flights** :

1. **Validation request** :
   ```python
   if len(request.destinations) < 2:
       raise ValueError("destinations must contain at least 2 cities")
   ```

2. **Construction URL** :
   ```python
   url = build_google_flights_url(request)
   logger.info("Built Google Flights URL", extra={"url": url})
   ```

3. **Crawl** :
   ```python
   try:
       html = await self.crawler_service.crawl_google_flights(url)
   except CaptchaDetectedException as e:
       logger.error("Captcha blocked crawl", extra={"url": url})
       raise
   except CrawlException as e:
       logger.error("Crawl failed", extra={"url": url, "error": str(e)})
       raise
   ```

4. **Parsing** :
   ```python
   flights = self.flight_parser.parse_flights(
       html=html,
       destinations=request.destinations[:2]
   )

   if not flights:
       logger.warning("No flights parsed", extra={"url": url})
       return []
   ```

5. **Retour résultats** :
   ```python
   logger.info(
       "Search completed",
       extra={
           "search_id": str(uuid.uuid4()),
           "destinations": request.destinations[:2],
           "result_count": len(flights),
           "price_range": f"{flights[0].price}-{flights[-1].price}"
       }
   )

   return flights
   ```

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### CrawlerService (8 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_crawl_valid_url_returns_html` | URL valide + mock AsyncWebCrawler | HTML non vide | Vérifier `len(html) > 0` |
| 2 | `test_crawl_with_stealth_enabled` | Mock BrowserConfig | BrowserConfig créé | Vérifier `enable_stealth == True` |
| 3 | `test_crawl_with_proxy_rotation` | Mock ProxyService | Proxy utilisé | Vérifier `proxy_service.get_next_proxy()` appelé |
| 4 | `test_crawl_captcha_detected_raises_exception` | Mock HTML avec `g-recaptcha` | CaptchaDetectedException levée | Vérifier exception + log WARNING |
| 5 | `test_crawl_timeout_raises_exception` | Mock timeout crawler | CrawlException levée | Vérifier exception timeout |
| 6 | `test_crawl_failed_result_raises_exception` | Mock `CrawlResult.success=False` | CrawlException levée | Vérifier exception + message |
| 7 | `test_crawl_logs_structured_context` | URL valide | Log INFO appelé | Vérifier `logger.info` avec extra context |
| 8 | `test_crawl_user_agent_rotation` | Mock user-agent pool | User-agent sélectionné | Vérifier rotation pondérée |

**Exemple code test AAA** :

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crawler_service import CrawlerService, CaptchaDetectedException
from app.services.proxy_service import ProxyService


@pytest.fixture
def mock_proxy_service():
    """Mock ProxyService."""
    service = MagicMock(spec=ProxyService)
    service.get_next_proxy.return_value = "http://customer-test-country-FR:password@pr.decodo.com:8080"
    return service


@pytest.fixture
def mock_crawler():
    """Mock AsyncWebCrawler."""
    crawler = AsyncMock()
    crawler.arun.return_value = MagicMock(
        html="<html><body>Google Flights Results</body></html>",
        success=True,
        status_code=200
    )
    return crawler


@pytest.mark.asyncio
async def test_crawl_valid_url_returns_html(mock_proxy_service, mock_crawler):
    # Arrange: Setup CrawlerService with mocks
    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        service = CrawlerService(proxy_service=mock_proxy_service)
        url = "https://www.google.com/travel/flights?test=1"

        # Act: Call crawl_google_flights
        html = await service.crawl_google_flights(url)

        # Assert: Verify HTML returned
        assert html is not None
        assert len(html) > 0
        assert "Google Flights" in html


@pytest.mark.asyncio
async def test_crawl_captcha_detected_raises_exception(mock_proxy_service, mock_crawler):
    # Arrange: Mock HTML with captcha
    mock_crawler.arun.return_value.html = '<html><div class="g-recaptcha">Captcha</div></html>'

    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        service = CrawlerService(proxy_service=mock_proxy_service)
        url = "https://www.google.com/travel/flights?test=1"

        # Act & Assert: Verify CaptchaDetectedException raised
        with pytest.raises(CaptchaDetectedException) as exc_info:
            await service.crawl_google_flights(url)

        # Assert: Verify exception message
        assert "Captcha detected" in str(exc_info.value)


@pytest.mark.asyncio
async def test_crawl_with_proxy_rotation(mock_proxy_service, mock_crawler):
    # Arrange: Setup service
    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        service = CrawlerService(proxy_service=mock_proxy_service)
        url = "https://www.google.com/travel/flights?test=1"

        # Act: Call crawl
        await service.crawl_google_flights(url)

        # Assert: Verify proxy service called
        mock_proxy_service.get_next_proxy.assert_called_once()
```

**Total tests unitaires CrawlerService** : 8 tests

---

### FlightParser (7 tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_parse_valid_html_returns_flights` | Mock HTML valide + destinations | `list[FlightResult]` non vide | Vérifier `len(flights) >= 1` |
| 2 | `test_parse_empty_html_returns_empty_list` | HTML vide `""` | `[]` | Vérifier `len(flights) == 0` |
| 3 | `test_parse_missing_selector_returns_empty_list` | HTML sans sélecteurs attendus | `[]` | Log ERROR + retour vide |
| 4 | `test_parse_price_transformation` | Mock HTML prix "1 250 €" | `flight.price == 1250.00` | Vérifier transformation float |
| 5 | `test_parse_date_iso_format` | Mock date "1 juin" | `flight.departure_date == "2025-06-01"` | Vérifier conversion ISO |
| 6 | `test_parse_top_10_limit` | Mock 15 résultats | `len(flights) == 10` | Vérifier limite Top 10 |
| 7 | `test_parse_validates_flight_result_fields` | Mock prix négatif | Skip vol invalide | Vérifier ValidationError géré |

**Exemple code test AAA** :

```python
import pytest
from app.services.flight_parser import FlightParser
from app.models.response import FlightResult


@pytest.fixture
def mock_valid_html():
    """Mock HTML Google Flights avec résultats."""
    return """
    <html>
        <div class="pIav2d">
            <div class="YMlIz FpEdX"><span>1 250 €</span></div>
            <div class="sSHqwe tPgKwe ogfYpf"><span>Air France</span></div>
            <div class="zxVSec YMlIz tPgKwe">
                <span aria-label="Departure 1 juin 10h30">10h30</span>
            </div>
            <div class="zxVSec YMlIz tPgKwe">
                <span aria-label="Arrival 15 juin 18h00">18h00</span>
            </div>
        </div>
    </html>
    """


def test_parse_valid_html_returns_flights(mock_valid_html):
    # Arrange: Setup parser and valid HTML
    parser = FlightParser()
    destinations = ["Paris", "Tokyo"]

    # Act: Parse HTML
    flights = parser.parse_flights(html=mock_valid_html, destinations=destinations)

    # Assert: Verify flights extracted
    assert len(flights) >= 1
    assert isinstance(flights[0], FlightResult)
    assert flights[0].price > 0


def test_parse_empty_html_returns_empty_list():
    # Arrange: Setup parser with empty HTML
    parser = FlightParser()
    empty_html = ""
    destinations = ["Paris", "Tokyo"]

    # Act: Parse empty HTML
    flights = parser.parse_flights(html=empty_html, destinations=destinations)

    # Assert: Verify empty list returned
    assert len(flights) == 0


def test_parse_top_10_limit():
    # Arrange: Mock HTML with 15 results
    parser = FlightParser()
    html_parts = ['<html>']
    for i in range(15):
        price = 1000 + (i * 100)
        html_parts.append(f"""
        <div class="pIav2d">
            <div class="YMlIz FpEdX"><span>{price} €</span></div>
            <div class="sSHqwe tPgKwe ogfYpf"><span>Air France</span></div>
        </div>
        """)
    html_parts.append('</html>')
    mock_html_15_results = ''.join(html_parts)

    destinations = ["Paris", "Tokyo"]

    # Act: Parse HTML
    flights = parser.parse_flights(html=mock_html_15_results, destinations=destinations)

    # Assert: Verify only Top 10 returned
    assert len(flights) == 10
```

**Total tests unitaires FlightParser** : 7 tests

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

**End-to-end** (3 tests) :

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_crawler_parser_end_to_end` | Mock crawler HTML → parser | Crawl + parse pipeline | FlightResult valide retourné |
| 2 | `test_integration_captcha_detection_workflow` | Mock HTML captcha | Crawl détecte captcha | CaptchaDetectedException propagée |
| 3 | `test_integration_proxy_rotation_multiple_crawls` | 3 crawls successifs | Vérifier rotation proxies | 3 proxies différents utilisés |

**Exemple code test Given/When/Then** :

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crawler_service import CrawlerService, CaptchaDetectedException
from app.services.flight_parser import FlightParser
from app.services.proxy_service import ProxyService


@pytest.mark.asyncio
async def test_integration_crawler_parser_end_to_end():
    # Given: Mock crawler returns valid HTML and parser configured
    mock_proxy_service = MagicMock(spec=ProxyService)
    mock_proxy_service.get_next_proxy.return_value = "http://test-proxy:8080"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = MagicMock(
        html="""
        <html>
            <div class="pIav2d">
                <div class="YMlIz FpEdX"><span>1 250 €</span></div>
                <div class="sSHqwe tPgKwe ogfYpf"><span>Air France</span></div>
            </div>
        </html>
        """,
        success=True
    )

    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        crawler_service = CrawlerService(proxy_service=mock_proxy_service)
        parser = FlightParser()

        url = "https://www.google.com/travel/flights?test=1"
        destinations = ["Paris", "Tokyo"]

        # When: Execute full pipeline
        html = await crawler_service.crawl_google_flights(url)
        flights = parser.parse_flights(html=html, destinations=destinations)

        # Then: Verify valid flight result
        assert len(flights) >= 1
        assert flights[0].price > 0
        assert flights[0].currency == "EUR"


@pytest.mark.asyncio
async def test_integration_captcha_detection_workflow():
    # Given: Mock crawler returns HTML with captcha
    mock_proxy_service = MagicMock(spec=ProxyService)
    mock_proxy_service.get_next_proxy.return_value = "http://test-proxy:8080"

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = MagicMock(
        html='<html><div class="g-recaptcha">Captcha</div></html>',
        success=True
    )

    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        crawler_service = CrawlerService(proxy_service=mock_proxy_service)
        url = "https://www.google.com/travel/flights?test=1"

        # When: Crawl with captcha present
        # Then: CaptchaDetectedException raised
        with pytest.raises(CaptchaDetectedException):
            await crawler_service.crawl_google_flights(url)


@pytest.mark.asyncio
async def test_integration_proxy_rotation_multiple_crawls():
    # Given: Mock proxy service with rotating proxies
    mock_proxy_service = MagicMock(spec=ProxyService)
    proxies = [
        "http://proxy1:8080",
        "http://proxy2:8080",
        "http://proxy3:8080"
    ]
    mock_proxy_service.get_next_proxy.side_effect = proxies

    mock_crawler = AsyncMock()
    mock_crawler.arun.return_value = MagicMock(
        html="<html>Google Flights</html>",
        success=True
    )

    with patch('app.services.crawler_service.AsyncWebCrawler', return_value=mock_crawler):
        crawler_service = CrawlerService(proxy_service=mock_proxy_service)
        url = "https://www.google.com/travel/flights?test=1"

        # When: Execute 3 crawls
        for _ in range(3):
            await service.crawl_google_flights(url)

        # Then: Verify 3 different proxies used
        assert mock_proxy_service.get_next_proxy.call_count == 3
```

**Total tests intégration** : 3 tests

---

## Exemples JSON et Données

### Exemple 1: URL Google Flights construite

**Input SearchRequest** :
```json
{
  "destinations": ["Paris", "Tokyo"],
  "date_range": {
    "start": "2025-06-01",
    "end": "2025-06-15"
  }
}
```

**URL générée** :
```
https://www.google.com/travel/flights?flight_type=2&departure_id=CDG&arrival_id=NRT&outbound_date=2025-06-01&return_date=2025-06-15&hl=fr&curr=EUR
```

---

### Exemple 2: Schema JSON Extraction CSS

```json
{
  "name": "Google Flights Results",
  "baseSelector": "div.pIav2d",
  "fields": [
    {
      "name": "price",
      "selector": "div.YMlIz.FpEdX span",
      "type": "text"
    },
    {
      "name": "airline",
      "selector": "div.sSHqwe.tPgKwe.ogfYpf span",
      "type": "text"
    },
    {
      "name": "departure_time",
      "selector": "div.zxVSec.YMlIz.tPgKwe span[aria-label*='Departure']",
      "type": "attribute",
      "attribute": "aria-label"
    },
    {
      "name": "arrival_time",
      "selector": "div.zxVSec.YMlIz.tPgKwe span[aria-label*='Arrival']",
      "type": "attribute",
      "attribute": "aria-label"
    },
    {
      "name": "duration",
      "selector": "div.gvkrdb.AdWm1c.tPgKwe",
      "type": "text"
    }
  ]
}
```

---

### Exemple 3: HTML brut extrait (tronqué)

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <title>Google Flights - Paris vers Tokyo</title>
</head>
<body>
    <div class="pIav2d">
        <div class="YMlIz FpEdX">
            <span>1 250 €</span>
        </div>
        <div class="sSHqwe tPgKwe ogfYpf">
            <span>Air France</span>
        </div>
        <div class="zxVSec YMlIz tPgKwe">
            <span aria-label="Departure 1 juin 10h30">10h30</span>
        </div>
        <div class="zxVSec YMlIz tPgKwe">
            <span aria-label="Arrival 15 juin 18h00">18h00</span>
        </div>
        <div class="gvkrdb AdWm1c tPgKwe">14h 30min</div>
    </div>

    <div class="pIav2d">
        <div class="YMlIz FpEdX">
            <span>1 350 €</span>
        </div>
        <div class="sSHqwe tPgKwe ogfYpf">
            <span>Japan Airlines</span>
        </div>
    </div>
</body>
</html>
```

---

### Exemple 4: JSON brut après extraction CSS

```json
[
  {
    "price": "1 250 €",
    "airline": "Air France",
    "departure_time": "Departure 1 juin 10h30",
    "arrival_time": "Arrival 15 juin 18h00",
    "duration": "14h 30min"
  },
  {
    "price": "1 350 €",
    "airline": "Japan Airlines",
    "departure_time": "Departure 1 juin 12h00",
    "arrival_time": "Arrival 15 juin 20h30",
    "duration": "16h 30min"
  }
]
```

---

### Exemple 5: FlightResult final (après parsing)

```json
[
  {
    "itinerary": ["Paris", "Tokyo"],
    "price": 1250.00,
    "currency": "EUR",
    "departure_date": "2025-06-01",
    "return_date": "2025-06-15"
  },
  {
    "itinerary": ["Paris", "Tokyo"],
    "price": 1350.00,
    "currency": "EUR",
    "departure_date": "2025-06-01",
    "return_date": "2025-06-15"
  }
]
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Crawl retourne HTML non vide** : `crawl_google_flights(url)` retourne HTML string > 0 bytes pour URL valide
2. **Parser extrait 1+ vol** : `parse_flights(html)` retourne liste non vide si HTML contient résultats Google Flights
3. **Prix positifs cohérents** : 100% résultats parsés ont `0 < price < 10000` (validation métier)
4. **Dates ISO 8601** : Tous `departure_date` et `return_date` respectent format YYYY-MM-DD
5. **Itinéraire cohérent** : FlightResult.itinerary contient destinations de la requête (Paris, Tokyo)
6. **Top 10 limite respectée** : `parse_flights` retourne max 10 résultats même si HTML contient plus
7. **Tri par prix croissant** : Résultats retournés triés `flights[i].price <= flights[i+1].price`
8. **Devise EUR fixe** : 100% résultats ont `currency == "EUR"`
9. **URL construction valide** : `build_google_flights_url(request)` génère URL avec tous paramètres (flight_type, departure_id, arrival_id, dates, hl=fr, curr=EUR)
10. **Captcha détection fonctionne** : HTML avec `g-recaptcha` ou `h-captcha` lève `CaptchaDetectedException`

## Critères techniques

11. **Type hints PEP 695 strict** : CrawlerService, FlightParser utilisent `list[str]`, `str | None`, async def
12. **Pydantic validation appliquée** : FlightResult validators (price positive) appliqués lors parsing
13. **Crawl4AI JsonCssExtractionStrategy** : Parsing utilise extraction CSS, 0 appel LLM
14. **Decodo proxies format correct** : Proxy format `customer-{api_key}-country-FR:password@pr.decodo.com:8080`
15. **Stealth mode activé** : BrowserConfig `enable_stealth=True` configuré dans CrawlerService
16. **Async def crawler** : `crawl_google_flights` est async def pour non-blocage event loop
17. **Dependency injection** : SearchService reçoit CrawlerService + FlightParser via `__init__`
18. **Exceptions custom** : CaptchaDetectedException et CrawlException définies et levées correctement

## Critères qualité

19. **Coverage ≥ 80%** : pytest --cov=app atteint 80%+ sur CrawlerService et FlightParser modules
20. **18 tests passent** : 8 crawler + 7 parser + 3 intégration tous verts
21. **Mypy strict mode** : mypy app/ retourne 0 erreur de type
22. **Ruff lint/format** : ruff check . && ruff format . passent sans erreur
23. **Docstrings 1 ligne** : CrawlerService, FlightParser, helpers ont docstrings explicites

## Critères production

24. **Logs structurés JSON** : Chaque crawl loggé avec extra context (url, proxy_used, html_size_kb, crawl_duration_ms)
25. **Log captcha detection** : Captcha détecté loggé WARNING avec captcha_type (recaptcha_v2, hcaptcha)
26. **Taux captcha monitorable** : Logs permettent calcul `captcha_detected / total_crawls` pour décision Phase 7
27. **Pas de secrets dans logs** : Proxy password masqué dans logs (vérification manuelle)

---

**💡 Note importante** : Cette story (8 story points) valide extraction CSS + anti-détection sur cas simple **1 destination aller-retour** (Paris → Tokyo). Les stories suivantes (Phase 6) géreront multi-city avec combinaisons complexes, mais foundation crawler + parser est réutilisable sans refactoring.

**Sélecteurs CSS à valider** : Étape 1 de la checklist (Analyser structure HTML) doit confirmer/ajuster sélecteurs CSS sur vraie page Google Flights 2025. Les sélecteurs fournis (`div.pIav2d`, `div.YMlIz.FpEdX`) sont basés sur patterns historiques mais peuvent changer.

**Dépendances externes** :
- Decodo API key valide (variable env `DECODO_USERNAME` format `customer-{api_key}-country-FR`)
- Playwright browsers installés via `crawl4ai-setup` (Phase 3.1 déjà complétée)

**Principe SMART** : Chaque critère est **S**pécifique (cible claire), **M**esurable (tests automatisés + métriques logs), **A**tteignable (scope 1 destination simple), **R**elevant (valeur business dérisquage), **T**emporel (Phase 4.5).
