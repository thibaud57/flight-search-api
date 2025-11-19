---
title: "TEMPLATE - Format Metadata Documentation Générique"
description: "Template standardisé pour metadata YAML des documentations projet (ARCHITECTURE, CHANGELOG, VERSIONS, etc.). Pour docs techniques references/, voir TEMPLATE_REFERENCES.md."
date: "2025-18-11"
keywords: ["template", "metadata", "yaml", "documentation", "format", "standard"]
scope: ["docs"]
technologies: []
---

# 📌 Scope de ce Template

**Ce template couvre** :
- Documentation architecture (ARCHITECTURE.md)
- Documentation versions (VERSIONS.md, CHANGELOG.md)
- Index et guides (REFERENCES.md, SPECS.md)

**Templates spécialisés** :
- **Docs techniques** (`docs/references/`) → [TEMPLATE_REFERENCES.md](TEMPLATE_REFERENCES.md)
- **User stories** (`docs/specs/`) → [TEMPLATE_SPECS.md](TEMPLATE_SPECS.md)

---

# 🔍 Description des Champs YAML

Chaque documentation doit commencer par un bloc YAML frontmatter contenant les champs suivants :

## `title`
- **Type** : String
- **Description** : Titre court identifiant rapidement le contenu
- **Format** : `"NOM - Catégorie"` ou `"NOM - Résumé"`

## `description`
- **Type** : String (2-3 lignes max)
- **Description** : Quand et pourquoi consulter cette doc. Focus sur **cas d'usage concrets**.
- **Format** : Phrase(s) courte(s) décrivant utilité + contexte

## `date`
- **Type** : String (format ISO 8601)
- **Description** : Date de dernière mise à jour de la documentation
- **Format** : `"YYYY-DD-MM"`

## `keywords`
- **Type** : Array of strings
- **Description** : Mots-clés techniques pour découverte et recherche
- **Guidelines** :
  - Inclure **noms technologies** (`"fastapi"`, `"pydantic"`, `"docker"`)
  - Inclure **concepts clés** (`"validation"`, `"async"`, `"testing"`)
  - Inclure **fichiers concernés** (`"pyproject"`, `"dockerfile"`, `".env"`)
  - Inclure **actions** (`"configuration"`, `"deployment"`, `"migration"`)
  - **5-15 keywords** recommandés

## `scope`
- **Type** : Array of strings
- **Description** : Phases projet concernées par cette doc
- **Valeurs possibles** :
  - `"config"` : Configuration projet (pyproject.toml, .env, settings)
  - `"code"` : Développement code (patterns, best practices)
  - `"test"` : Tests (unitaires, intégration, e2e)
  - `"deploy"` : Déploiement (Docker, CI/CD, hosting)
  - `"docs"` : Documentation (CHANGELOG, README, architecture)
  - `"setup"` : Installation initiale (dependencies, environment)

## `technologies`
- **Type** : Array of strings
- **Description** : Technologies/frameworks spécifiques couverts
- **Guidelines** :
  - Langages : `"python"`, `"javascript"`, `"java"`
  - Frameworks : `"fastapi"`, `"spring"`, `"angular"`
  - Outils : `"docker"`, `"pytest"`, `"github-actions"`
  - Vide `[]` pour docs architecture/ADR génériques

---

# 📚 Exemples de Metadata par Type de Doc

## Documentation Versions/Dependencies

```yaml
---
title: "VERSIONS - Matrice de compatibilité"
description: "Versions exactes des dépendances et compatibilité croisée. Consulter pour configuration pyproject.toml, installation dependencies."
date: "2025-17-11"
keywords: ["versions", "dependencies", "compatibility", "python", "pyproject", "packages"]
scope: ["config", "setup"]
technologies: ["python"]
---
```

## Documentation Technique (Framework/Library)

```yaml
---
title: "FastAPI - Référence Technique"
description: "Patterns FastAPI (Dependency Injection, Async Routes, TestClient). Consulter pour développement API, routes asynchrones, tests."
date: "2025-17-11"
keywords: ["fastapi", "api", "routes", "async", "dependency-injection", "testing", "endpoints"]
scope: ["code", "test"]
technologies: ["python", "fastapi"]
---
```

## Documentation Architecture/Design

```yaml
---
title: "ARCHITECTURE - Vision d'ensemble"
description: "Architecture globale, diagrammes, ADRs. Consulter pour comprendre structure générale, décisions architecturales."
date: "2025-17-11"
keywords: ["architecture", "design", "adr", "diagrams", "overview", "decisions"]
scope: ["docs", "code"]
technologies: ["python", "fastapi", "docker"]
---
```

---

# 🎯 Guidelines de Rédaction

## Structure Fichier Documentation

```markdown
---
title: "..."
description: "..."
date: "YYYY-DD-MM"
keywords: [...]
scope: [...]
technologies: [...]
---

# Section Principale 1

Contenu markdown normal...

## Sous-section 1.1

Code examples, tableaux, etc.

### Sous-sous-section 1.1.1

Détails techniques précis.

## Sous-section 1.2

Autre contenu...

# Section Principale 2

...
```

## Ressources

### Structure Section Ressources

Chaque documentation **peut** contenir une section **Ressources** en fin de document (si applicable) :

```markdown
# Ressources

## Documentation Officielle

- **Nom Technologie** : https://...
- **Guide Spécifique** : https://...

## Ressources Complémentaires

- **Outil Tiers** : https://...
- **Guide Communautaire** : https://...
```

### Catégories Ressources (optionnel, uniquement si applicable) 

**Documentation Officielle** (optionnel, uniquement si applicable)  :
- Documentation maintenue par l'auteur/organisation de la technologie
- Guides officiels, API references, release notes
- Exemples : FastAPI docs, Pydantic docs, Tenacity docs

**Ressources Complémentaires** (optionnel, uniquement si applicable) :
- **Outils tiers** : Databases UA, tools externes (ex: User-Agent database)
- **Ressources communautaires** : Awesome lists, GitHub Marketplace, ...
- **Dépendances sous-jacentes** : Docs de libs utilisées (ex: Playwright pour Crawl4AI)
- **Cross-références** : Liens vers autres docs projet (ex: Crawl4AI Stealth → Captcha Detection)
- **Technologies concurrentes** : Docs alternatives/competitors (ex: Cloudflare, DataDome)

### Exemples Complets

**Documentation SANS Ressources Complémentaires** :
```markdown
# Ressources

## Documentation Officielle

- **FastAPI Documentation** : https://fastapi.tiangolo.com
- **Async Routes** : https://fastapi.tiangolo.com/async/
```

**Documentation AVEC Ressources Complémentaires** :
```markdown
# Ressources

## Documentation Officielle

- **Crawl4AI Documentation** : https://docs.crawl4ai.com/

## Ressources Complémentaires

- **Playwright Documentation** : https://playwright.dev/python/docs/intro
```

## Bonnes Pratiques

**✅ DO** :
- Utiliser **mots-clés techniques précis** (`"pyproject.toml"`, `"async"`)
- Inclure **synonymes** (`"dependencies"` + `"packages"` + `"deps"`)
- Mentionner **fichiers/commandes** concernés dans keywords
- Garder description **concise** (2-3 lignes max)
- **Mettre à jour `date`** à chaque modification significative
- **Ajouter section Ressources** en fin de document si liens pertinents
- **Consolider sources** au lieu de liens éparpillés

**❌ DON'T** :
- Répéter le titre dans description
- Oublier keywords techniques importants
- Mettre technologies non pertinentes
- Description trop vague ("Doc sur FastAPI")
- Keywords trop génériques seuls (`"code"`, `"config"`)
- Titre markdown redondant après YAML
- Ajouter Ressources Complémentaires sans justification

## Cas Particuliers

**Documentation Architecture/ADR** :
- `technologies: []` (générique, pas de stack spécifique)
- `scope: ["docs", "code"]`
- Keywords focus design (`"adr"`, `"decisions"`, `"architecture"`)

**Documentation Installation/Setup** :
- `scope: ["setup", "config"]`
- Keywords focus installation (`"install"`, `"dependencies"`, `"setup"`)

**Documentation Déploiement** :
- `scope: ["deploy"]`
- Keywords focus ops (`"deployment"`, `"production"`, `"ci-cd"`, `"docker"`)

---

# 📝 Checklist Validation

Avant de merger une doc avec metadata :

**Metadata YAML** :
- [ ] Bloc YAML en **en-tête** (avant tout contenu markdown)
- [ ] `title` descriptif et court
- [ ] `description` 2-3 lignes max, cas d'usage clairs
- [ ] `date` au format ISO 8601 (YYYY-DD-MM)
- [ ] `keywords` 5-15 mots-clés pertinents et techniques
- [ ] `scope` au moins 1 phase
- [ ] `technologies` cohérentes avec contenu doc
- [ ] Syntaxe YAML valide (`:`, `[]`, indentation correcte)
- [ ] Pas de titre markdown redondant après YAML

**Section Ressources (optionnelle, si applicable)** :
- [ ] Si section **Ressources** présente : utilise `# Ressources` (non-numérotée)
- [ ] Sous-section **## Documentation Officielle** ajoutée si liens officiels pertinents
- [ ] Sous-section **## Ressources Complémentaires** ajoutée UNIQUEMENT si :
  - Outils tiers / databases externes utilisés
  - Ressources communautaires référencées (Awesome lists, Marketplace)
  - Dépendances sous-jacentes documentées (ex: Playwright pour Crawl4AI)
  - Cross-références autres docs projet nécessaires
  - Technologies concurrentes/alternatives mentionnées