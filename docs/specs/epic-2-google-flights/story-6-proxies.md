---
title: "Story 6: Proxies Decodo (anti-détection)"
scope: "specs"
category: "user-story"
epic: "Epic 2: Google Flights Integration"
story_points: 5
priority: "high"
status: "planned"
dependencies: ["story-4"]
date: 2025-01-18
keywords: [proxies, decodo, anti-detection, rotation, residential]
technologies: [Decodo Proxies, Crawl4AI proxy config, pytest]
business_value: "Anti-détection Google Flights, coûts proxies optimisés, taux succès élevé"
acceptance_criteria:
  - "ProxyService configure proxies Decodo (residential FR)"
  - "Rotation proxies active (round-robin ou random)"
  - "CrawlerService utilise proxies via ProxyService"
  - "8 tests unitaires + 3 tests intégration passent"
---

# Story 6: Proxies Decodo (anti-détection)

_Spécifications à compléter en Phase 4.6_

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
- [ ] Spécifications ProxyService (Decodo config)
- [ ] Stratégie rotation proxies documentée
- [ ] Configuration CrawlerService avec proxies
- [ ] Tests unitaires listés (8 tests ProxyService + 3 intégration)

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1**: Tests + implémentation ProxyService
- [ ] **TDD Phase 2**: Intégration CrawlerService avec ProxyService
- [ ] **TDD Phase 3**: Rotation proxies (round-robin/random)
- [ ] **Tests intégration**: 3 tests end-to-end avec vraies clés Decodo
- [ ] Validation manuelle: Logs montrent proxies actifs
- [ ] Quality checks: 0 erreurs
- [ ] Coverage ≥ 80%

---

## 📝 Notes d'implémentation

**Dépendances**: Story 4 (CrawlerService implémenté)

**Ordre TDD**:
1. ProxyService (config Decodo)
2. Rotation proxies
3. Integration CrawlerService
4. Tests intégration

**Fichiers**:
- `app/services/proxy_service.py`: ProxyService
- `app/services/crawler_service.py`: Mise à jour (utilise ProxyService)
- `tests/unit/test_proxy_service.py`: 8 tests
- `tests/integration/test_proxies.py`: 3 tests (avec vraies clés)

**Temps estimé**: ~4h (5 story points)

**Note**: Tests intégration nécessitent vraies clés Decodo (coût bandwidth).
