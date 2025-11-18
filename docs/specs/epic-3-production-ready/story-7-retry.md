---
title: "Story 7: Retry + Error handling"
scope: "specs"
category: "user-story"
epic: "Epic 3: Production Ready"
story_points: 5
priority: "high"
status: "planned"
dependencies: ["story-4", "story-5", "story-6"]
date: 2025-01-18
keywords: [retry, tenacity, error-handling, resilience, logging]
technologies: [Tenacity, exponential backoff, jitter, pytest]
business_value: "Robustesse production, SLA garantis, retry automatique sur échecs temporaires"
acceptance_criteria:
  - "Retry logic implémenté avec Tenacity (exponential backoff + jitter)"
  - "CrawlerService retry automatique sur timeouts/erreurs 5xx"
  - "Logs détaillés avant chaque retry (contexte métier)"
  - "10 tests unitaires retry + 5 tests intégration passent"
---

# Story 7: Retry + Error handling

_Spécifications à compléter en Phase 4.7_

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
- [ ] Spécifications retry logic (Tenacity decorators)
- [ ] Stratégie exponential backoff + jitter documentée
- [ ] Erreurs retry vs non-retry documentées (5xx retry, 4xx non-retry)
- [ ] Logging before_sleep callback spécifié
- [ ] Tests unitaires listés (10 tests retry + 5 intégration)

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1**: Tests + implémentation retry decorators
- [ ] **TDD Phase 2**: Intégration CrawlerService avec retry
- [ ] **TDD Phase 3**: Error handling et logging
- [ ] **Tests intégration**: 5 tests end-to-end avec échecs simulés
- [ ] Validation manuelle: Logs montrent retry en action
- [ ] Quality checks: 0 erreurs
- [ ] Coverage ≥ 80%

---

## 📝 Notes d'implémentation

**Dépendances**:
- Story 4 (CrawlerService)
- Story 5 (SearchService orchestration)
- Story 6 (ProxyService)

**Ordre TDD**:
1. Retry decorators (Tenacity)
2. Integration CrawlerService
3. Error handling + logging
4. Tests intégration

**Fichiers**:
- `app/services/crawler_service.py`: Mise à jour (retry logic)
- `app/core/retry.py`: Retry decorators (Tenacity)
- `tests/unit/test_retry.py`: 10 tests
- `tests/integration/test_retry.py`: 5 tests

**Temps estimé**: ~4h (5 story points)

**Note**: Tests intégration simulent échecs (timeouts, 5xx) pour valider retry.
