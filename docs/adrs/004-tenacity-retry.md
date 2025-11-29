---
title: "ADR-004 — Tenacity pour Retry Logic"
description: "Choix de la bibliothèque de retry pour gestion des erreurs réseau et timeouts lors du scraping"
date: "2025-11-16"
keywords: ["architecture", "adr", "retry", "tenacity", "resilience", "async"]
scope: ["docs", "architecture"]
technologies: ["tenacity", "backoff", "python"]
---

# 🎯 Contexte

Le scraping de Google Flights est sujet à des erreurs réseau, timeouts, et refus de connexion. Une stratégie de retry robuste avec exponential backoff + jitter est nécessaire pour garantir la résilience du système.

---

# 🧩 Problème

Quelle bibliothèque/approche utiliser pour implémenter une retry logic robuste, configurable et compatible avec l'architecture async (FastAPI + AsyncWebCrawler) ?

## 🛠️ Options Envisagées

### Option A : Tenacity

**Description :** Bibliothèque Python spécialisée retry avec support async natif, wait strategies avancées, et callbacks logging.

**Avantages :**
- Async support natif (`async def`)
- 8+ wait strategies (exponential, random, fixed, etc.)
- Configurabilité excellente (retry conditions, stop conditions)
- Callbacks natifs (`before_sleep`, `after`) pour structured logging
- Production-ready (utilisé par Airflow, Celery, OpenStack)
- Maintenance stable (version 9.1.2)

**Inconvénients :**
- Dépendance externe (minime, lib stable)

---

### Option B : backoff (lib)

**Description :** Bibliothèque alternative retry avec decorators.

**Avantages :**
- Syntaxe simple
- 3 wait strategies principales
- Stable

**Inconvénients :**
- Support async partiel (moins mature que Tenacity)
- Logging callbacks limités
- Moins de configurabilité

---

### Option C : Retry Manuel

**Description :** Implémentation custom avec `asyncio` + loops.

**Avantages :**
- Contrôle total
- Pas de dépendance

**Inconvénients :**
- Code custom à maintenir
- Risque bugs (edge cases retry)
- Pas de best practices intégrées (jitter, exponential backoff)

---

## 🎉 Décision

**✅ Tenacity**

**Justification :**
- **Async-First** : Support `async def` natif (FastAPI + AsyncWebCrawler)
- **Wait Strategies** : Exponential backoff + jitter (best practice anti-collision)
- **Configurabilité** : Retry conditions spécifiques (ex: retry network errors, pas 404)
- **Logging** : Callbacks `before_sleep`, `after` pour structured logging JSON
- **Production-Ready** : Utilisé par projets enterprise (Airflow, Celery)

---

## 🔄 Conséquences

**Positives :**
- ✅ Résilience réseau optimale (retry automatique erreurs temporaires)
- ✅ Logging détaillé des retries (before_sleep callback → JSON logs)
- ✅ Configuration flexible (retry network errors only, pas 4xx client errors)
- ✅ Best practices intégrées (exponential backoff + jitter)

**Négatives :**
- ⚠️ Dépendance externe (minime, bibliothèque stable et mature)

---

# 📝 Notes complémentaires

**Configuration recommandée :**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    before_sleep=log_retry_attempt
)
async def crawl_google_flights(url: str) -> str:
    ...
```

**Retry strategy :**
- Max 5 tentatives par combinaison
- Exponential backoff : 1s, 2s, 4s, 8s, 16s (max 60s)
- Jitter : randomisation pour éviter collision simultanée
- Retry si : TimeoutException, NetworkError, ProxyError
- No retry si : 4xx client errors, parsing errors

**Logging callback :**
```python
def log_retry_attempt(retry_state):
    logger.warning(
        "Retry attempt",
        extra={
            "attempt": retry_state.attempt_number,
            "wait_time": retry_state.next_action.sleep,
            "exception": str(retry_state.outcome.exception())
        }
    )
```
