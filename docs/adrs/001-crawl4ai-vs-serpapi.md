---
title: "ADR-001 — Crawl4AI + Proxies vs SerpAPI"
description: "Choix de la solution de scraping Google Flights : Crawl4AI + proxies résidentiels vs API tierce SerpAPI"
date: "2025-11-16"
keywords: ["architecture", "adr", "scraping", "crawl4ai", "serpapi", "proxies"]
scope: ["docs", "architecture"]
technologies: ["crawl4ai", "decodo", "serpapi"]
---

# 🎯 Contexte

Le projet nécessite de scraper Google Flights pour récupérer les prix et horaires de vols multi-destinations. Deux approches principales existent : scraping direct avec gestion de l'anti-détection, ou utilisation d'une API tierce spécialisée.

---

# 🧩 Problème

Comment récupérer les données Google Flights de manière fiable, scalable et économique tout en gérant les défis techniques (anti-bot, captchas, rate limits) ?

## 🛠️ Options Envisagées

### Option A : Crawl4AI + Decodo Proxies (Scraping Direct)

**Description :** Scraping direct avec Crawl4AI (AsyncWebCrawler + Playwright intégré) + proxies résidentiels Decodo pour anti-détection.

**Avantages :**
- Coût variable ~4€/GB + proxy overhead (~10-15€/mois pour 1000 recherches)
- Contrôle total sur extraction (sélecteurs CSS personnalisés)
- Scalabilité excellente (ajout proxies à la demande)
- Flexibilité maximale (retry, timeout, parsing custom)
- Expérience technique scraping avancé

**Inconvénients :**
- Maintenance élevée (sélecteurs CSS si Google change HTML)
- Gestion manuelle captchas (détection + retry)
- Complexité anti-détection (stealth mode, user-agents)

**Coût estimé :** ~10-15€/mois pour 1000 recherches

---

### Option B : SerpAPI

**Description :** API tierce standardisée fournissant accès Google Flights via endpoints REST.

**Avantages :**
- API stable, peu de maintenance
- Anti-détection géré par SerpAPI
- Pas de gestion captchas
- Support client

**Inconvénients :**
- Coût fixe : $50/mois (plan de base 1000 requêtes) → $0.05/requête
- Flexibilité limitée (API standardisée)
- Rate limits stricts (1000 requêtes/mois plan de base)
- Scalabilité limitée par plan tarifaire
- Dépendance forte à un fournisseur externe

**Coût estimé :** $50/mois pour 1000 recherches

---

## 🎉 Décision

**✅ Crawl4AI + Decodo Proxies**

**Justification :**
- **ROI** : Pour 1000 recherches/mois, coût estimé ~10-15€ vs $50 SerpAPI (70% moins cher)
- **Flexibilité** : Contrôle total sur extraction (CSS selectors spécifiques multi-city)
- **Scalabilité** : Pas de limite artificielle, ajout proxies à la demande
- **Learning** : Expérience scraping avancé (stealth, anti-bot, retry patterns)
- **Autonomie** : Pas de dépendance fournisseur externe

---

## 🔄 Conséquences

**Positives :**
- ✅ Coûts variables mais prévisibles (~10-15€/mois MVP)
- ✅ Contrôle total extraction (JsonCssExtractionStrategy personnalisée)
- ✅ Scalabilité horizontale facile (add proxies)
- ✅ Flexibilité retry logic (tenacity exponential backoff)

**Négatives :**
- ⚠️ Maintenance sélecteurs CSS si Google change HTML (monitoring nécessaire)
- ⚠️ Gestion captchas manuelle (détection + retry avec rotation proxy)
- ⚠️ Complexité technique initiale (stealth mode, anti-détection)

---

# 📝 Notes complémentaires

**Stratégie de mitigation risques :**
- Monitoring parsing failures (alerte si >5%)
- Tests end-to-end réguliers sur vraies URLs Google Flights
- Fallback LLM possible si changement HTML majeur (voir ADR #006)
- Migration SerpAPI facile si coûts maintenance deviennent trop élevés

**Implémentation :**
- Crawl4AI 0.7+ avec AsyncWebCrawler
- Decodo proxies résidentiels (ADR #002)
- JsonCssExtractionStrategy (ADR #006)
- Tenacity retry logic (ADR #004)
