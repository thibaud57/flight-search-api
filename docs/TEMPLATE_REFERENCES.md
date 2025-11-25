---
title: "TEMPLATE - Documentation Technique Référence"
description: "Template standardisé pour créer des documentations techniques dans docs/references/. Structure recommandée Description → Exemple → Points clés pour frameworks, APIs, outils et libraries."
date: "YYYY-DD-MM"
keywords: ["template", "references", "documentation", "technique", "pattern", "best-practices"]
scope: ["docs"]
technologies: []
---

# 🔍 Description des Champs YAML (Docs Techniques)

## `title`
- **Format** : `"[Technologie] - [Catégorie]"`
- **Exemples** : `"FastAPI - Framework Web Asynchrone"`, `"Tenacity - Retry Logic & Resilience"`

## `description`
- **Format** : `"Référence [Technologie] : [concepts clés]. Consulter pour [cas d'usage concrets]."`
- **Longueur** : 2-3 lignes max

## `date`
- **Format** : `"YYYY-DD-MM"` (ISO 8601)

## `keywords`
- **Contenu** : Nom technologie, concepts clés, patterns techniques, actions
- **Quantité** : 5-15 mots-clés

## `scope`
- **Valeurs courantes** : `["code"]`, `["code", "test"]`, `["deploy"]`, `["code", "deploy"]`

## `technologies`
- **Exemples** : `["fastapi"]`, `["crawl4ai", "playwright"]`, `["tenacity"]`

---

# 📚 Exemples de Metadata

## Documentation Framework/Library

```yaml
---
title: "FastAPI - Framework Web Asynchrone"
description: "Référence FastAPI : Dependency Injection, Async Routes, TestClient. Consulter pour développement API, routes asynchrones, tests."
date: "2025-18-11"
keywords: ["fastapi", "async", "api", "dependency-injection", "testclient", "routes"]
scope: ["code", "test"]
technologies: ["fastapi", "httpx", "pytest"]
---
```

## Documentation Outil/Service

```yaml
---
title: "Decodo Proxies - Residential Proxy Management"
description: "Référence Decodo Proxies : rotation (rotating vs sticky sessions), ciblage France, authentification, pricing. Consulter pour configuration proxies, optimisation coûts."
date: "2025-18-11"
keywords: ["decodo", "proxies", "residential", "rotation", "authentication", "france", "bandwidth", "pricing"]
scope: ["deploy", "code"]
technologies: ["decodo"]
---
```

---

# 🎯 Structure Standard (Template à Copier)

```markdown
---
title: "[Technologie] - [Catégorie]"
description: "Référence [Technologie] : [concepts clés]. Consulter pour [cas d'usage concrets]."
date: "YYYY-DD-MM"
keywords: ["techno", "concept1", "concept2", "pattern"]
scope: ["code"]
technologies: ["nom-techno"]
---

# [Concept Principal 1] - [Titre Descriptif]

## Description

[Texte explicatif : qu'est-ce que c'est, à quoi ça sert, pourquoi l'utiliser]
[2-4 paragraphes courts]

## Exemple minimal

```python/bash/yaml
[Code concret et fonctionnel - copier-coller ready]
```

## Points clés

- Point 1 : [Comportement non-évident]
- Point 2 : [Limitation importante]
- Point 3 : [Recommandation d'usage]
- [3-6 points maximum]

# [Concept Principal 2]

## Description

[...]

## Exemple minimal

```code
[...]
```

## Points clés

[...]

# [Concept Principal 3] (si applicable)

[Répéter structure similaire]

# Best Practices (optionnel)

## ✅ Recommandations

- Recommandation 1 : [Explication]
- Recommandation 2 : [Explication]

## ❌ Anti-Patterns

- Anti-pattern 1 : [Pourquoi éviter]
- Anti-pattern 2 : [Pourquoi éviter]

# Ressources

## Documentation Officielle

- **[Nom Technologie]** : https://...
- **[Guide Spécifique]** : https://...

## Ressources Complémentaires (optionnel, si applicable)

- **[Outil Tiers]** : https://...
- **[Guide Communautaire]** : https://...
```

---

# 📝 Guidelines Rapides

**Structure chaque section** : Description → Exemple → Points clés

**Description** : 2-4 paragraphes (quoi/pourquoi/comment)

**Exemple** : Code fonctionnel, minimal, avec imports

**Points clés** : 3-6 points (comportements non-évidents, limitations, recommandations)

**Éléments optionnels utiles** :
- Tableaux comparatifs (options, types, pricing)
- Sous-sections `###` pour variantes
- Listes numérotées pour workflows

---

# ✅ Checklist Validation

**Metadata YAML** :
- [ ] `title` format : `"[Technologie] - [Catégorie]"`
- [ ] `description` : cas d'usage concrets (2-3 lignes max)
- [ ] `date` au format ISO 8601 (YYYY-DD-MM)
- [ ] `keywords` : 5-15 mots-clés techniques pertinents
- [ ] `scope` : au moins 1 phase
- [ ] `technologies` : liste technologies couvertes

**Structure Contenu** :
- [ ] 2-5 sections `#` par concept majeur
- [ ] Chaque section suit : Description → Exemple → Points clés
- [ ] Code exemples **fonctionnels** (copier-coller ready)
- [ ] Section `# Ressources` en fin de document

**Qualité** :
- [ ] Aucun commentaire inline non justifié (règle CLAUDE.md)
- [ ] Exemples respectent conventions projet
- [ ] Liens ressources valides et à jour
