---
title: "Story 4: Crawler + Parser (1 destination)"
scope: "specs"
category: "user-story"
epic: "Epic 2: Google Flights Integration"
story_points: 8
priority: "high"
status: "planned"
dependencies: ["story-3"]
date: 2025-01-18
keywords: [crawl4ai, parser, google-flights, css-extraction, scraping]
technologies: [Crawl4AI, AsyncWebCrawler, JsonCssExtractionStrategy, pytest]
business_value: "Vraies données Google Flights (1 destination), proof of concept scraping"
acceptance_criteria:
  - "CrawlerService crawl Google Flights URL avec Crawl4AI"
  - "FlightParser extrait vols depuis HTML (JsonCssExtractionStrategy)"
  - "SearchService retourne vraies données (1 destination)"
  - "10 tests unitaires Crawler + 8 tests Parser + 4 intégration passent"
---

# Story 4: Crawler + Parser (1 destination)

_Spécifications à compléter en Phase 4.4_

## 🎯 Contexte Business

_À remplir_

---

## 📋 Spécifications Techniques

_À remplir_

---

## 🧪 Tests

_À remplir_

---

## ✅ Critères d'acceptation

**Phase 4 (Specs)**:
- [ ] Spécifications CrawlerService (Crawl4AI + AsyncWebCrawler)
- [ ] Spécifications FlightParser (JsonCssExtractionStrategy)
- [ ] Sélecteurs CSS Google Flights documentés
- [ ] Tests unitaires listés (10 Crawler + 8 Parser + 4 intégration)

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1**: Tests + implémentation CrawlerService
- [ ] **TDD Phase 2**: Tests + implémentation FlightParser
- [ ] **TDD Phase 3**: Intégrer dans SearchService (1 destination)
- [ ] **Tests intégration**: 4 tests end-to-end passent
- [ ] Validation manuelle: Vraies données Google Flights
- [ ] Quality checks: 0 erreurs
- [ ] Coverage ≥ 80%

---

## 📝 Notes d'implémentation

**Dépendances**: Story 3 (Models SearchRequest, SearchResponse, FlightResult)

**Ordre TDD**:
1. CrawlerService (tests + implémentation)
2. FlightParser (tests + implémentation)
3. SearchService integration (remplacer mock)
4. Tests intégration end-to-end

**Fichiers**:
- `app/services/crawler_service.py`: CrawlerService
- `app/services/flight_parser.py`: FlightParser
- `app/services/search_service.py`: Mise à jour (vraies données)
- `tests/unit/test_crawler_service.py`: 10 tests
- `tests/unit/test_flight_parser.py`: 8 tests
- `tests/integration/test_google_flights.py`: 4 tests

**Temps estimé**: ~6h (8 story points)
