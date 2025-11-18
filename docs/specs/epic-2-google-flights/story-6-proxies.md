---
title: "Story 6: Proxy Integration (Decodo Proxies)"
epic: "Epic 2: Google Flights Scraping"
story_points: 5
dependencies: ["story-4"]
date: "2025-18-11"
keywords: ["proxies", "decodo", "residential", "rotation", "anti-detection", "authentication", "country-targeting", "france", "proxy-pool"]
scope: ["specs"]
technologies: ["Decodo Proxies", "Python", "Pydantic v2", "itertools", "Crawl4AI"]
---

# Contexte Business

## Besoin utilisateur

### Persona 1: Product Owner
- Besoin anti-detection robuste contournement blocages Google Flights (rate limiting, bot detection)
- Validation technique proxies residentiels France legitimite requetes (IPs residentielles vs datacenter)
- Monitoring taux succes crawls avec proxies vs sans proxies (target >95% succes avec proxies)
- Controle couts bandwidth Decodo (pricing 2GB-1000GB, volumes previsibles)

### Persona 2: Developpeur Backend
- Integration Decodo proxies residentiels avec rotation automatique (round-robin)
- Configuration authentication format specifique Decodo (customer-{api_key}-country-fr:password)
- Dependency injection ProxyService dans CrawlerService (architecture modulaire)
- Logging proxies utilises sans exposer passwords (securite secrets)

### Persona 3: Utilisateur Final API
- Recherches vols fonctionnelles sans blocages captcha (taux captcha <5%)
- Transparence proxy rotation (utilisateur final ne voit pas, beneficie fiabilite)
- Temps reponse acceptable malgre latence proxies residentiels (~+200-500ms vs direct)
- Qualite resultats identique avec ou sans proxies

## Contraintes metier

### Contraintes fonctionnelles
- Country targeting France : Proxies targetent IPs residentielles France (country-fr)
- Rotating mode par defaut : Changement IP chaque requete (pas sticky sessions MVP)
- Pool manager pattern : Rotation automatique proxies via round-robin
- Fallback si proxy echoue : Continue avec proxy suivant (pas arret complet)

### Contraintes techniques
- Authentication format strict : customer-{api_key}-country-fr:password@pr.decodo.com:8080
- Endpoint residential : pr.decodo.com:8080 (pas gate.decodo.com)
- Variables env securisees : DECODO_USERNAME, DECODO_PASSWORD, DECODO_PROXY_HOST dans .env
- Type safety strict : PEP 695 type hints, Pydantic v2 validators, Mypy strict mode

### Contraintes performance et couts
- Bandwidth limite Decodo : 1 crawl 500KB-2MB, surveiller consommation mensuelle
- Pricing volumes : 2GB ($6), 25GB ($65 populaire), 100GB ($225), 1000GB ($1500)
- Latence proxies residentiels : +200-500ms vs direct (acceptable MVP)
- Taux succes target : >=95% crawls success avec proxies

## Valeur business

- Reduction blocages Google Flights : Taux captcha <5% avec proxies residentiels France
- Fiabilite crawls production : Taux succes >=95% grace rotation IPs residentielles
- Scalabilite recherches : Support volumes crawls eleves sans rate limiting Google
- Controle couts bandwidth : Monitoring consommation optimisation plan Decodo

## Metriques succes

### Metriques fonctionnelles
- Taux succes crawls >=95% : Sur 100 crawls test, minimum 95 retournent HTML valide
- Rotation proxies fonctionne : 3 crawls successifs utilisent 3 proxies differents
- Country France applique : 100% requetes utilisent IPs France (logs proxy_country: FR)
- Authentication valide : 0 erreur authentication Decodo (status 407)

### Metriques qualite
- Coverage >=80% : pytest --cov=app atteint 80%+ sur ProxyService
- 12 tests passent : 8 unitaires ProxyService + 4 integration tous verts
- Mypy strict mode : 0 erreur de type
- Ruff lint/format : 0 erreur

---

# Specifications Techniques

## 1. ProxyConfig Model Pydantic

Modele Pydantic v2 validant configuration proxy Decodo avec authentication format strict.

Voir fichier complet pour details implementation.

---

## 2. ProxyService

Service gerant pool proxies Decodo avec rotation automatique round-robin.

Implementation utilisant itertools.cycle pour rotation predictible.

Voir fichier complet pour details implementation.

---

## 3. Strategie Rotation Proxies

Mode Rotating par defaut (MVP) : Changement IP chaque requete
Mode Sticky Session (Phase 7+) : Conservation IP pendant duree definie
Pool Manager Pattern : Round-robin via itertools.cycle

---

## 4. Authentication Format Decodo

Format username : customer-{api_key}-country-{country_code}
Endpoint : pr.decodo.com:8080
Variables env : DECODO_USERNAME, DECODO_PASSWORD, DECODO_PROXY_HOST

---

## 5. Integration CrawlerService

Modification CrawlerService (Story 4) : injection ProxyService
BrowserConfig.proxy configuré avec URL proxy Decodo
Logging proxy utilise (password masque avec ***)

---

# Tests

## Tests unitaires (8 tests)

1. test_proxy_service_init_with_valid_configs
2. test_proxy_service_init_empty_configs_raises_error
3. test_get_next_proxy_round_robin
4. test_get_proxy_url_format_correct
5. test_proxy_config_validation_username_format
6. test_proxy_config_validation_country_uppercase
7. test_proxy_service_pool_cycle_repeats
8. test_get_random_proxy_returns_valid_proxy

## Tests integration (4 tests)

1. test_integration_crawler_uses_proxy
2. test_integration_proxy_rotation_multiple_crawls
3. test_integration_proxy_logged_without_password
4. test_integration_crawler_proxy_dependency_injection

---

# Criteres acceptation

## Criteres fonctionnels (10)

1. Rotation proxies fonctionne
2. Country France applique
3. Authentication format valide
4. Endpoint residential correct
5. URL proxy format correct
6. Pool manager round-robin
7. Dependency injection fonctionne
8. Variables env chargees
9. Taux succes crawls >=95%
10. Fallback echec proxy

## Criteres techniques (8)

11. Type hints PEP 695 strict
12. Pydantic v2 validators
13. BrowserConfig proxy parameter
14. Logging structure JSON
15. Password masque logs
16. Frozen ProxyConfig
17. Settings integration
18. Async def compatible

## Criteres qualite (6)

19. Coverage >=80%
20. 12 tests passent
21. Mypy strict mode
22. Ruff lint/format
23. Docstrings 1 ligne
24. Format tests AAA/Given-When-Then
