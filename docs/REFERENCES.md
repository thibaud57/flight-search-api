# REFERENCES.md - flight-search-api

Documentation technique complète pour toutes les technologies utilisées dans le projet.

**Date de dernière mise à jour** : 16 novembre 2025

---

## Structure de la Documentation

La documentation technique est organisée en fichiers séparés pour optimiser la gestion du contexte LLM et faciliter la navigation.

### Références Disponibles

1. **[FastAPI](references/fastapi.md)** - Framework web asynchrone
   - Dependency Injection
   - Async Routes
   - TestClient

2. **[Pydantic v2](references/pydantic-v2.md)** - Validation et settings
   - BaseSettings & Configuration
   - Field Validator & Model Validator
   - Migration v1 → v2

3. **[Crawl4AI](references/crawl4ai.md)** - Web scraping asynchrone
   - AsyncWebCrawler
   - BrowserConfig & Stealth Mode
   - JsonCssExtractionStrategy

4. **[Decodo Proxies](references/decodo-proxies.md)** - Proxies résidentiels
   - Residential Rotation
   - France Targeting
   - Authentication
   - Bandwidth Optimization

5. **[Google Flights URL Structure](references/google-flights.md)** - Construction d'URLs de recherche
   - Structure URL de Base
   - Format des Dates
   - Paramètres Multi-City
   - Localisation & Devise (France/EUR)

6. **[Techniques Anti-Détection](references/anti-detection.md)** - Contournement des protections
   - Stealth Mode Crawl4AI
   - Undetected Browser Mode
   - User-Agent Rotation
   - Proxy Rotation
   - Stratégie Complète Combinée

7. **[Détection de Captchas](references/captcha-detection.md)** - Identification et gestion
   - Patterns HTML reCAPTCHA
   - Patterns HTML hCaptcha
   - Code de Détection Python
   - Stratégie de Retry avec Rotation IP
   - Configuration Optimale de Retry

8. **[Tenacity](references/tenacity.md)** - Retry et résilience
   - @retry Decorator
   - Wait Strategies (Exponential Backoff, Jitter)
   - Async Support

9. **[Dokploy](references/dokploy.md)** - Déploiement et hébergement
   - Dockerfile Best Practices
   - Gestion des Variables d'Environnement
   - Deployment Workflow

---

## Ressources Additionnelles

| Technologie | Documentation Principale |
|-------------|--------------------------|
| FastAPI | https://fastapi.tiangolo.com/ |
| Pydantic v2 | https://docs.pydantic.dev/latest/ |
| Crawl4AI | https://docs.crawl4ai.com/ |
| Decodo | https://help.decodo.com/docs |
| Tenacity | https://tenacity.readthedocs.io/ |
| Dokploy | https://docs.dokploy.com/ |

---

## Usage

Pour consulter une référence spécifique, ouvrez le fichier correspondant dans [docs/references/](references/).

Cette organisation modulaire permet :
- ✅ Chargement ciblé des références nécessaires
- ✅ Réduction de la consommation de tokens (~44% d'économie)
- ✅ Navigation plus rapide dans les IDEs
- ✅ Meilleure gestion Git (historique, conflits)
- ✅ Maintenance facilitée

**Dernière validation** : 16 novembre 2025
