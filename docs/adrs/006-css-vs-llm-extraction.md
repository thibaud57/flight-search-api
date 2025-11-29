---
title: "ADR-006 — JsonCssExtractionStrategy vs LLMExtractionStrategy"
description: "Choix de la méthode d'extraction données depuis HTML Google Flights : CSS selectors vs LLM parsing"
date: "2025-11-16"
keywords: ["architecture", "adr", "extraction", "css", "llm", "parsing", "crawl4ai"]
scope: ["docs", "architecture"]
technologies: ["crawl4ai", "openai", "claude"]
---

# 🎯 Contexte

Crawl4AI propose deux stratégies d'extraction de données depuis HTML : `JsonCssExtractionStrategy` (sélecteurs CSS déterministes) et `LLMExtractionStrategy` (parsing via LLM type GPT-4 ou Claude).

---

# 🧩 Problème

Quelle stratégie d'extraction optimise performance, coûts et fiabilité pour extraire les données de vols (prix, horaires, compagnies) depuis Google Flights ?

## 🛠️ Options Envisagées

### Option A : JsonCssExtractionStrategy (CSS Selectors)

**Description :** Extraction déterministe via sélecteurs CSS ciblant éléments HTML spécifiques.

**Avantages :**
- Coût : ✅ $0 (pas d'API LLM)
- Performance : ⚡ Ultra-rapide (<10ms par page)
- Déterminisme : ✅ 100% reproductible (même input → même output)
- Scalabilité : ✅ Excellente (1000+ pages/s sans rate limits)
- Fiabilité : ✅ Haute si HTML structure stable

**Inconvénients :**
- Maintenance : ⚠️ Haute si Google change sélecteurs CSS
- Fragile : Dépend structure HTML exacte

**Configuration exemple :**
```python
schema = {
    "flights": {
        "selector": ".flight-card",
        "fields": {
            "price": ".price-value",
            "departure_time": ".departure-time",
            "arrival_time": ".arrival-time",
            "airline": ".airline-name",
            "duration": ".flight-duration"
        }
    }
}
```

---

### Option B : LLMExtractionStrategy (GPT-4 / Claude)

**Description :** Extraction via LLM qui parse HTML et extrait données selon prompt.

**Avantages :**
- Maintenance : ✅ Faible (LLM adaptatif aux changements HTML)
- Flexibilité : ✅ Parse structures HTML variées
- Robustesse : ✅ Gère variations mineures HTML

**Inconvénients :**
- Coût : ❌ ~$0.01-0.05 par page (OpenAI/Claude API)
- Performance : 🐢 Lent (1-3s par page vs <10ms CSS)
- Déterminisme : ⚠️ Non-déterministe (hallucinations possibles)
- Scalabilité : ⚠️ Limitée par rate limits API LLM
- Fiabilité : ⚠️ Moyenne (risque hallucinations)

**Coût estimé :**
- 1000 recherches × 10 pages/recherche = 10,000 pages/mois
- 10,000 × $0.03 = $300/mois (vs $0 CSS)

---

## 🎉 Décision

**✅ JsonCssExtractionStrategy (CSS Selectors)**

**Justification :**
- **Coût** : $0 vs potentiellement $100-500/mois pour 10k+ recherches
- **Performance** : 100-300x plus rapide que LLM (<10ms vs 1-3s)
- **Déterminisme** : Résultats identiques à chaque exécution (critique pour tests)
- **HTML Google Flights** : Structure relativement stable (observé sur 6 mois)
- **MVP** : Prioriser vitesse et coût zéro

---

## 🔄 Conséquences

**Positives :**
- ✅ Coûts opérationnels minimaux ($0 extraction)
- ✅ Performance optimale (parsing instantané)
- ✅ Tests déterministes (fixtures HTML reproductibles)
- ✅ Scalabilité illimitée (pas de rate limits API)

**Négatives :**
- ⚠️ Maintenance sélecteurs CSS si Google change HTML structure
- ⚠️ Fragile si changements majeurs HTML
- ⚠️ Nécessite monitoring parsing failures

---

# 📝 Notes complémentaires

**Stratégie Maintenance :**
1. Tests end-to-end réguliers sur vraies URLs Google Flights
2. Monitoring parsing failures (alerte si >5%)
3. Fixtures HTML tests pour détecter regressions
4. Fallback LLM uniquement si changement HTML majeur

**Monitoring requis :**
```python
logger.error(
    "Parsing failed",
    extra={
        "search_id": uuid,
        "url": google_flights_url,
        "html_length": len(html),
        "selector": failed_selector
    }
)
```

**Métriques clés :**
- Taux parsing failures : `failed_parses / total_parses`
- Seuil alerte : >5% → Vérifier sélecteurs CSS
- Action : Update sélecteurs ou fallback LLM temporaire

**Fallback LLM possible si nécessaire :**
- Architecture modulaire permet switch stratégie facilement
- LLMExtractionStrategy disponible en backup
- Migration progressive possible (CSS primary, LLM fallback)

**Optimisations bandwidth :**
- Désactiver images, CSS, ads via Crawl4AI `BrowserConfig`
- Économie : ~90% vs scraping full page
- Bandwidth estimé : ~200KB/page (vs 2MB full page)

**Sélecteurs CSS critiques :**
```python
SELECTORS = {
    "price": ".price-value, [data-price]",
    "airline": ".airline-name, [data-airline]",
    "departure": ".departure-time, [data-departure]",
    "arrival": ".arrival-time, [data-arrival]",
    "duration": ".flight-duration, [data-duration]"
}
```

**Tests critiques :**
- `test_parse_google_flights_html()` : Fixtures HTML réelles
- `test_parse_handles_missing_fields()` : Robustesse parsing
- `test_parse_multiple_flights()` : Extraction batch
