---
title: "ADR-003 — Top 10 en Mémoire vs Base de Données"
description: "Choix de l'architecture de stockage des résultats de recherche : en mémoire vs persistance DB"
date: "2025-11-16"
keywords: ["architecture", "adr", "storage", "stateless", "database", "redis"]
scope: ["docs", "architecture"]
technologies: ["postgresql", "redis"]
---

# 🎯 Contexte

L'API doit retourner les meilleurs résultats de vols (Top 10 triés par prix) pour chaque recherche multi-city. La question du stockage des résultats se pose : persistance en base de données ou traitement en mémoire ?

---

# 🧩 Problème

Quelle architecture de stockage optimise performance, coûts et simplicité pour le use case MVP (API stateless pour n8n) ?

## 🛠️ Options Envisagées

### Option A : Top 10 en Mémoire (Stateless)

**Description :** Résultats calculés à la volée, triés par prix, Top 10 retournés dans response JSON, aucune persistance.

**Avantages :**
- Complexité très faible (pas d'infrastructure DB)
- Performance ultra-rapide (pas d'I/O DB)
- Architecture stateless → scaling horizontal facile
- Coûts : $0 (pas de DB à héberger)
- Use case parfait pour n8n (recherche → response immédiate)

**Inconvénients :**
- Pas de persistance (résultats perdus après response)
- Pas d'historique recherches
- Pas d'analytics possibles sans DB

---

### Option B : PostgreSQL

**Description :** Stockage persistant des résultats dans base relationnelle.

**Avantages :**
- Persistance complète
- Historique recherches
- Analytics possibles (tendances prix, destinations populaires)
- Requêtes complexes (SQL)

**Inconvénients :**
- Complexité moyenne (migrations, ORM, maintenance)
- Coûts : ~10€/mois (hébergement DB)
- Performance : I/O DB overhead
- Architecture stateful (scaling plus complexe)
- Overkill pour use case MVP (pas besoin historique)

---

### Option C : Redis

**Description :** Cache en mémoire avec TTL optionnel.

**Avantages :**
- Performance ultra-rapide
- TTL pour cache temporaire (ex: 15min)
- Persistance optionnelle

**Inconvénients :**
- Coûts : ~5€/mois
- Complexité moyenne
- Historique limité (cache volatile)
- Pas nécessaire pour MVP stateless

---

## 🎉 Décision

**✅ Top 10 en Mémoire (Stateless)**

**Justification :**
- **Use Case** : API stateless pour n8n → pas besoin persistance (recherche → response → fin)
- **Performance** : Réponse instantanée, pas d'I/O DB
- **Simplicité** : Zéro infrastructure additionnelle (pas de DB à gérer)
- **Coûts** : $0 vs 5-10€/mois DB
- **Scalabilité** : Stateless → scaling horizontal trivial (add containers)

---

## 🔄 Conséquences

**Positives :**
- ✅ Architecture simplifiée (API + Scraping, pas de DB layer)
- ✅ Déploiement minimal (Dockerfile sans DB dependencies)
- ✅ Performance optimale (pas de latence DB)
- ✅ Coûts $0 (pas d'hébergement DB)
- ✅ Stateless → scaling horizontal facile

**Négatives :**
- ❌ Pas d'historique recherches (acceptable pour MVP)
- ❌ Pas d'analytics sans DB (acceptable pour MVP)
- ⚠️ Si besoin futur analytics → migration DB facile (architecture modulaire)

---

# 📝 Notes complémentaires

**Migration DB possible si nécessaire :**
- Architecture service layer permet ajout DB sans refactor majeur
- Cas d'usage futurs : analytics, tendances prix, notifications prix
- Redis cache possible en Phase 7+ si besoin

**Implémentation actuelle :**
```python
# SearchService.rank_results()
results = sorted(all_flights, key=lambda x: x.total_price)
top_10 = results[:10]
return SearchResponse(results=top_10)
```

**Monitoring :**
- Pas de métriques stockage nécessaires
- Logs structurés JSON suffisants pour debugging
