---
title: "SPECS - Index Spécifications Techniques MVP"
description: "Index centralisé des spécifications techniques détaillées par user story. Consulter pour naviguer vers specs Epic/Story spécifique."
date: "2025-18-11"
keywords: ["specs", "specifications", "user-stories", "epic", "tdd", "mvp", "api", "models", "services", "tests"]
scope: ["docs"]
technologies: ["fastapi", "pydantic", "crawl4ai", "decodo", "tenacity", "pytest"]
---

# Spécifications Techniques - flight-search-api

Vue d'ensemble des spécifications MVP organisées par Epic et User Story.

## 🎯 Vue d'ensemble MVP

**Objectif** : API recherche vols multi-destinations via Google Flights

**Stack** : FastAPI + Crawl4AI + Decodo Proxies + Pydantic v2

**Release target** : v1.0.0 (MVP Production)

**Structure** : `docs/specs/epic-X/story-Y.md` (1 fichier par story)

**Template** : `docs/TEMPLATE_SPECS.md` (structure standardisée)

---

## Epic 1: API Foundation (v0.5.0)

**Objectif** : Foundation API testable

**Stories** :
- [Story 1: Health check endpoint](specs/epic-1-api-foundation/story-1-health-check.md) - 2 pts
- [Story 2: Configuration & Logging](specs/epic-1-api-foundation/story-2-config-logging.md) - 3 pts
- [Story 3: Search endpoint (mock)](specs/epic-1-api-foundation/story-3-search-endpoint.md) - 8 pts

**Total** : 13 story points

**Valeur business** : API testable par client, contrat validé

**Déployable** : ✅ API répond, contrat JSON validé

---

## Epic 2: Google Flights Integration (v0.6.0)

**Objectif** : Intégration Google Flights complète

**Stories** :
- [Story 4: Crawler + Parser](specs/epic-2-google-flights/story-4-crawler-parser.md) - 8 pts
- [Story 5: Proxies Decodo](specs/epic-2-google-flights/story-5-proxies.md) - 5 pts
- [Story 6: Multi-city Search](specs/epic-2-google-flights/story-6-multi-city-search.md) - 5 pts

**Total** : 18 story points

**Valeur business** : Feature MVP complète (vraies données multi-destinations)

**Déployable** : ✅ Recherche multi-destinations fonctionne

---

## Epic 3: Production Ready (v0.7.0)

**Objectif** : Robustesse production

**Stories** :
- [Story 7: Retry + Error handling](specs/epic-3-production-ready/story-7-retry.md) - 5 pts

**Total** : 5 story points

**Valeur business** : SLA production, robustesse

**Déployable** : ✅ Production-ready

---

## 📊 Statistiques

- **Total stories** : 7
- **Total story points** : 36
- **Epics** : 3
- **Releases** : v0.5.0, v0.6.0, v0.7.0 → v1.0.0

---

## 🔄 Process

**Phase 4 : Spécifications**
- 4.1 : Créer structure `docs/specs/epic-X/`
- 4.2-4.8 : Remplir stories (1 fichier .md par story)
- 4.9 : Mise à jour CHANGELOG v0.4.0-specs

**Phase 5 : Implémentation TDD**
- Par Epic : Implémenter stories → CHANGELOG → Release
- Epic 1 (Stories 1-3) → CHANGELOG → v0.5.0
- Epic 2 (Stories 4-6) → CHANGELOG → v0.6.0
- Epic 3 (Story 7) → CHANGELOG → v0.7.0

**Phase 6 : Documentation & Production**
- 6.1 : Documentation utilisateur (README, API docs)
- 6.2 : CHANGELOG consolidé v1.0.0
- 6.3 : Tests end-to-end manuels
- 6.4 : Déploiement Dokploy MVP

**Phase 7 : Captcha (Post-MVP - Optionnel)**
- 7A : Specs Story 8 (si monitoring >5% blocages)
- 7B : Implémentation Story 8 → v1.1.0

**Ordre exécution** : Story 1 → 2 → 3 → 4 → 5 (Proxies) → 6 (Multi-city) → 7 (→ 8 si Phase 7)

---

## 📝 Notes importantes

**Template specs** : Toutes les stories suivent le template `docs/TEMPLATE_SPECS.md`

**Metadata complètes** : Chaque story contient :
- `story_points` : Estimation complexité (1, 2, 3, 5, 8)
- `dependencies` : Stories prérequises
- `date` : Date dernière mise à jour (YYYY-DD-MM)
- `keywords` : Mots-clés techniques pour découverte
- `scope` : Portée documentation (["specs"])
- `technologies` : Stack technique utilisée

**Workflow TDD** : Voir `.claude/CLAUDE.md` - Section Tests / Workflow TDD par story

**Captcha** : Phase 7 post-MVP uniquement (si monitoring >5% blocages)

**MVP** : SearchStats **sans** `captcha_detected` (correction appliquée Story 3)

---

## 🔗 Ressources

- [TEMPLATE_SPECS.md](TEMPLATE_SPECS.md) - Template stories
- [PLAN.md](../.claude/PLAN.md) - Plan d'action complet
- [CLAUDE.md](../.claude/CLAUDE.md) - Standards et conventions
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture + ADR
- [REFERENCES.md](REFERENCES.md) - Index documentation technique
