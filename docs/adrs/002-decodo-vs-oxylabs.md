---
title: "ADR-002 — Decodo vs Oxylabs (Proxies Résidentiels)"
description: "Choix du fournisseur de proxies résidentiels pour anti-détection Google Flights"
date: "2025-11-16"
keywords: ["architecture", "adr", "proxies", "decodo", "oxylabs", "anti-detection"]
scope: ["docs", "architecture"]
technologies: ["decodo", "oxylabs"]
---

# 🎯 Contexte

Pour éviter la détection par Google Flights lors du scraping, des proxies résidentiels sont nécessaires. Le choix du fournisseur impacte directement les coûts, la fiabilité et la performance du scraping.

---

# 🧩 Problème

Quel fournisseur de proxies résidentiels offre le meilleur rapport qualité/prix pour le cas d'usage MVP (scraping Google Flights France) ?

## 🛠️ Options Envisagées

### Option A : Decodo

**Description :** Proxies résidentiels avec pool 10M+ IPs, targeting géographique France natif.

**Avantages :**
- Prix compétitif : ~4€/GB
- France targeting natif (format auth : `customer-{key}-country-FR`)
- Pool IP : 10M+ IPs résidentiels largement suffisant
- Documentation claire et complète
- Rotation automatique (sticky sessions disponibles)
- Pay-as-you-go bandwidth

**Inconvénients :**
- Support email uniquement (pas de 24/7)
- Pool IP plus petit qu'Oxylabs

**Coût estimé :** ~4€/GB

---

### Option B : Oxylabs

**Description :** Leader marché proxies avec pool 100M+ IPs, support premium.

**Avantages :**
- Pool IP massif : 100M+ IPs
- France targeting natif
- Support 24/7 + Account Manager
- Rotation automatique avancée
- Réputation enterprise

**Inconvénients :**
- Prix premium : ~10-15€/GB (2,5-4x plus cher que Decodo)
- Plans fixes ou PAYG
- Overkill pour MVP

**Coût estimé :** ~10-15€/GB

---

## 🎉 Décision

**✅ Decodo**

**Justification :**
- **Coût** : 60% moins cher qu'Oxylabs (~4€/GB vs 10-15€/GB)
- **France Targeting** : Format auth simple et efficace (`customer-{key}-country-FR`)
- **Pool IP** : 10M+ IPs largement suffisant pour MVP (pas besoin de 100M)
- **Documentation** : Claire et complète, facile à intégrer
- **Pay-as-you-go** : Pas d'engagement mensuel, coûts variables

---

## 🔄 Conséquences

**Positives :**
- ✅ Coûts optimisés pour MVP (~10-15€/mois vs 25-60€ avec Oxylabs)
- ✅ Intégration simple (format auth standard HTTP proxy)
- ✅ Pool IP suffisant pour éviter détection
- ✅ Rotation automatique fonctionnelle

**Négatives :**
- ⚠️ Support moins premium qu'Oxylabs (acceptable pour MVP)
- ⚠️ Pool IP plus petit (mais suffisant pour use case actuel)

---

# 📝 Notes complémentaires

**Migration facile si besoin :**
- Format auth similaire entre providers
- Code ProxyService agnostique (rotation round-robin)
- Migration Oxylabs possible si volume augmente drastiquement

**Configuration recommandée :**
```python
PROXY_USERNAME=customer-{API_KEY}-country-FR
PROXY_PASSWORD=your_password
PROXY_HOST=pr.decodo.com:8080
PROXY_ROTATION_ENABLED=true
```

**Monitoring bandwidth :**
- Objectif : <50GB/mois
- Optimisations actives : désactiver images/CSS/ads (ADR #006)
