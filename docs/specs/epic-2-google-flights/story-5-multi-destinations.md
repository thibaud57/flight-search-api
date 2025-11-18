---
title: "Story 5: Multi-destinations (CombinationGenerator)"
scope: "specs"
category: "user-story"
epic: "Epic 2: Google Flights Integration"
story_points: 5
priority: "high"
status: "planned"
dependencies: ["story-4"]
date: 2025-01-18
keywords: [multi-city, combinations, itertools, ranking, top-10]
technologies: [itertools.product, Python, pytest]
business_value: "Feature MVP complète (2-10 destinations), Top 10 meilleurs vols"
acceptance_criteria:
  - "CombinationGenerator génère permutations multi-city (2-10 destinations)"
  - "SearchService orchestre recherches multiples"
  - "Top 10 résultats triés par prix (meilleur en premier)"
  - "8 tests unitaires Generator + 6 SearchService + 3 intégration passent"
---

# Story 5: Multi-destinations (CombinationGenerator)

_Spécifications à compléter en Phase 4.5_

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
- [ ] Spécifications CombinationGenerator (itertools.product)
- [ ] Spécifications SearchService orchestration (multiple crawls)
- [ ] Algorithme Top 10 ranking documenté
- [ ] Tests unitaires listés (8 Generator + 6 Service + 3 intégration)

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1**: Tests + implémentation CombinationGenerator
- [ ] **TDD Phase 2**: Tests + implémentation SearchService orchestration
- [ ] **TDD Phase 3**: Top 10 ranking (tri + limite 10 résultats)
- [ ] **Tests intégration**: 3 tests end-to-end passent
- [ ] Validation manuelle: 3 destinations → Top 10 vols
- [ ] Quality checks: 0 erreurs
- [ ] Coverage ≥ 80%

---

## 📝 Notes d'implémentation

**Dépendances**: Story 4 (CrawlerService, FlightParser fonctionnels 1 destination)

**Ordre TDD**:
1. CombinationGenerator (tests + implémentation)
2. SearchService orchestration (tests + implémentation)
3. Top 10 ranking (tests + implémentation)
4. Tests intégration end-to-end

**Fichiers**:
- `app/services/combination_generator.py`: CombinationGenerator
- `app/services/search_service.py`: Mise à jour (orchestration multi-city)
- `tests/unit/test_combination_generator.py`: 8 tests
- `tests/unit/test_search_service.py`: 6 tests (orchestration)
- `tests/integration/test_multi_city.py`: 3 tests

**Temps estimé**: ~4h (5 story points)
