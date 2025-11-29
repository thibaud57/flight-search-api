---
title: "ADR-005 — Captcha Handling Strategy (MVP : Détection Only)"
description: "Stratégie de gestion des captchas Google Flights pour MVP : détection + retry vs résolution automatique"
date: "2025-11-16"
keywords: ["architecture", "adr", "captcha", "2captcha", "anti-detection", "mvp"]
scope: ["docs", "architecture"]
technologies: ["crawl4ai", "decodo", "2captcha"]
---

# 🎯 Contexte

Google Flights peut afficher des captchas (reCAPTCHA, hCaptcha) pour bloquer les bots. Plusieurs stratégies existent : évitement via proxies, détection + retry, ou résolution automatique via services tiers (2Captcha).

---

# 🧩 Problème

Quelle stratégie de gestion captcha offre le meilleur compromis efficacité/coût/complexité pour le MVP ?

## 🛠️ Options Envisagées

### Option A : Proxies Résidentiels Uniquement

**Description :** Utilisation exclusive de proxies résidentiels Decodo pour éviter détection.

**Avantages :**
- Coût : ~4€/GB uniquement
- Complexité faible
- Efficacité : 90-95% bypass captcha

**Inconvénients :**
- 5-10% de recherches peuvent échouer
- Pas de stratégie si captcha détecté

---

### Option B : Détection + Retry avec Rotation IP (MVP)

**Description :** Détecter captchas via patterns HTML, logger + retry avec nouveau proxy (rotation IP).

**Avantages :**
- Coût : ~4€/GB (pas de coût additionnel)
- Complexité faible
- Efficacité : 95-98% bypass (retry avec nouveau proxy)
- Monitoring en place pour décision data-driven

**Inconvénients :**
- ~2-5% de recherches peuvent échouer après retries

**Détection Captcha :**
```python
def is_captcha_detected(html: str) -> bool:
    captcha_patterns = [
        "recaptcha",
        "hcaptcha",
        "g-recaptcha",
        "captcha-container"
    ]
    return any(pattern in html.lower() for pattern in captcha_patterns)
```

---

### Option C : 2Captcha (Résolution Auto)

**Description :** Intégration service résolution automatique captchas.

**Avantages :**
- Efficacité : 99%+ bypass
- Résolution automatique reCAPTCHA/hCaptcha

**Inconvénients :**
- Coût additionnel : $0.001-0.003 par captcha résolu
- Complexité moyenne (intégration API 2Captcha)
- Temps résolution : 10-60s par captcha
- Coût mensuel estimé : $10-50 selon volume

---

### Option D : hCaptcha Solver

**Description :** Alternative 2Captcha spécialisée hCaptcha.

**Avantages :**
- Coût : ~$0.001/captcha

**Inconvénients :**
- Même inconvénients que 2Captcha
- Spécialisé hCaptcha uniquement

---

## 🎉 Décision

**✅ Option B : Détection + Retry avec Rotation IP (MVP)**

**Post-MVP (Phase 7 - Optionnel) :** Intégration 2Captcha si monitoring montre >5% blocages

**Justification MVP :**
- **Proxies résidentiels Decodo** : Évitent déjà 90-95% des captchas
- **Stealth mode Crawl4AI** : Anti-détection enterprise (undetected browser)
- **Retry + Rotation IP** : Nouveau proxy → nouvelle session → contourne captcha temporaire
- **ROI** : Coût $0 vs résolution captcha ($0.001-0.003 × volume)
- **Monitoring** : Logger taux captcha pour décision data-driven Post-MVP

---

## 🔄 Conséquences

**Positives :**
- ✅ MVP rapide et économique (pas de coût additionnel)
- ✅ Monitoring en place pour décision éclairée Post-MVP
- ✅ Efficacité 95-98% acceptable pour MVP
- ✅ Migration 2Captcha facile si nécessaire (architecture modulaire)

**Négatives :**
- ⚠️ ~2-5% de recherches peuvent échouer après 5 retries (acceptable MVP)
- ⚠️ Temps retry additionnel si captcha détecté (~10-30s)

---

# 📝 Notes complémentaires

**Stratégie Retry :**
1. Captcha détecté → Log warning + metrics
2. Rotation proxy automatique (ProxyService)
3. Retry avec nouveau proxy (tenacity)
4. Max 5 tentatives par combinaison

**Monitoring requis :**
```python
logger.warning(
    "Captcha detected",
    extra={
        "search_id": uuid,
        "combination": combination,
        "proxy_used": proxy_host,
        "retry_attempt": attempt_number
    }
)
```

**Métriques clés :**
- Taux captcha : `captcha_detected / total_requests`
- Seuil alerte : >5% → Évaluer intégration 2Captcha

**Post-MVP (Phase 7) :**
- **Trigger** : Monitoring montre >5% taux captcha persistant
- **Solution** : Intégration 2Captcha en fallback
- **Décision** : Data-driven après 1-2 semaines monitoring production
- **Implémentation** : CaptchaSolverService + 2Captcha API

**Extensions possibles :**
- Optimisation pools proxies dédiés (IPs moins utilisées)
- Rate limiting intelligent (throttling requests)
- Webhooks notifications si taux captcha critique
