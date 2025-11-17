# Refactoring Workflow EPCT - Agents Génériques

**Date** : 2025-11-17
**Contexte** : Refactoring agents explore/plan/code/test + commande execute-plan-phase pour workflow générique (pas spécifique Python/flight-search-api)

---

## 🎯 Objectif Global

Rendre les agents EPCT (Explore, Plan, Code, Test) **génériques** et **réutilisables** pour n'importe quel projet (Python, JS, Go, etc.).

**Approche** : Metadata-driven (YAML frontmatter) + détection automatique stack + optimisation tokens.

---

## 📊 État Final

### ✅ Agent EXPLORE (complété)
- ✅ Ajout Phase 0A : Exploration codebase (stack, conventions, existing_files)
- ✅ Phase 0B : Exploration documentation (metadata YAML)
- ✅ Détection automatique stack via marker files
- ✅ Extraction conventions qualité (linter, formatter, type_checker, test_runner)
- ✅ Retourne JSON structuré (codebase + documentation)
- ✅ Support 8+ langages (Python, JS/TS, Go, Rust, Java, Ruby, PHP, .NET)

### ✅ Agent PLAN (complété)
- ✅ Exemples génériques multi-langages (Python, Node.js, Go)
- ✅ WebSearch adaptatif selon `codebase.stack`
- ✅ Terminologie générique (linter, test_runner, type_checker)
- ✅ Retourne checklist niveau 2 + stratégie exécution
- ✅ Support validation user avec retry

### ✅ Agent CODE (complété)
- ✅ Ajout outil WebSearch
- ✅ Commandes qualité adaptées au stack (Python/JS/Go/Rust)
- ✅ Utilise `codebase.conventions` pour détecter outils
- ✅ Exemples multi-langages (formatage, linting, type checking)
- ✅ Respect conventions projet détectées

### ✅ Agent TEST (complété)
- ✅ Détection dynamique type output via keywords (config, docker, app, docs, tests)
- ✅ Commandes validation adaptées au stack (Python/JS/Go/Rust)
- ✅ Utilise `codebase.conventions` pour détecter test_runner, linter, type_checker
- ✅ Exemples multi-langages (pytest, jest, go test, cargo test)
- ✅ Rapport validation structuré avec diagnostic actionnable

### ✅ Commande execute-plan-phase (complétée)
- ✅ Workflow optimisé 8 étapes (Parser PLAN.md ciblé, EXPLORE, stocke liste, Setup Git, PLAN avec retry, CODE selon stratégie, TEST, Cocher PLAN.md)
- ✅ TodoWrite niveau 1 (orchestration, fixe)
- ✅ PLAN décide stratégie (parallèle/séquentiel/unique)
- ✅ Retry logic validation user (avec feedback loop)
- ✅ Gestion erreurs sub-agents (informer user, user décide)

### ✅ Cleanup Final
- ✅ Suppression anti-patterns (instructions négatives "Ne PAS faire")
- ✅ Suppression références contexte externe ("par EXPLORE", "de l'agent CODE")
- ✅ Instructions context-agnostic (sub-agents ne connaissent que leur input/output)

---

## 🚀 Workflow Optimisé - execute-plan-phase

### Architecture Clarifiée

**execute-plan-phase (orchestrateur)** :
- Rôle : Chef d'orchestre, PAS exécutant
- Responsabilités : Coordonner agents, pas analyser/exécuter

**Sub-agents** :
- EXPLORE : Découvrir contexte (codebase + docs)
- PLAN : Analyser + décomposer + décider stratégie
- CODE : Exécuter checklist (1 ou N agents en //)
- TEST : Valider conformité

**Règle importante** : Sub-agents ne peuvent PAS lancer d'autres agents ni interagir avec user.

```
User
  ↓
Claude (execute-plan-phase)
  ↓
Sub-agents (explore, plan, code, test)
  ↓ (retour résultats)
Claude
  ↓
User
```

### Workflow Étape par Étape

#### **ÉTAPE 0 : TodoWrite optimisé**
```javascript
TodoWrite([
  {content: "Parser PLAN.md phase {X.Y}", status: "pending", activeForm: "Parsing PLAN.md"},
  {content: "Lancer EXPLORE (découvrir contexte)", status: "pending", activeForm: "Lancement EXPLORE"},
  {content: "Lire contexte minimal", status: "pending", activeForm: "Lecture contexte"},
  {content: "Setup Git", status: "pending", activeForm: "Configuration Git"},
  {content: "Lancer PLAN (checklist niveau 2)", status: "pending", activeForm: "Lancement PLAN"},
  {content: "Valider plan avec user", status: "pending", activeForm: "Validation user"},
  {content: "Lancer CODE (exécution)", status: "pending", activeForm: "Lancement CODE"},
  {content: "Lancer TEST (validation)", status: "pending", activeForm: "Lancement TEST"},
  {content: "Cocher PLAN.md", status: "pending", activeForm: "Mise à jour PLAN"}
])
```

#### **ÉTAPE 1 : Parser PLAN.md (ciblé)**
**Objectif** : Extraire SEULEMENT Phase {X.Y} demandée (optimisation tokens).

```markdown
1. Read(".claude/PLAN.md")
2. Parser pour trouver "## Phase {X}" et "### {X.Y}"
3. Extraire :
   - Titre phase parente
   - Objectif global
   - Branche Git
   - Titre sous-phase
   - Checklist niveau 1 (toutes `- [ ]`)
   - Output attendu (`📝 **Output**`)
   - Notes spécifiques

Token saved : 700 lignes → 50 lignes pertinentes
```

#### **ÉTAPE 2 : Lancer EXPLORE**
**Objectif** : Identifier fichiers nécessaires SANS tout lire.

**Input EXPLORE** :
- Checklist niveau 1
- Phase context (objectif, output attendu)

**EXPLORE fait** :
1. Scanner codebase (fichiers pertinents selon keywords checklist)
2. Scanner docs (metadata YAML matching)
3. Identifier conventions projet

**EXPLORE retourne** : **JSON liste fichiers** (PAS le contenu)
```json
{
  "codebase": {
    "stack": "python",
    "existing_files": ["app/main.py"]
  },
  "documentation": {
    "files_to_read": [
      {
        "path": "docs/VERSIONS.md",
        "reason": "Versions exactes pour recherches",
        "priority": "critical"
      },
      {
        "path": ".claude/CLAUDE.md",
        "sections": ["Standards Python"],
        "reason": "Conventions metadata",
        "priority": "critical"
      }
    ]
  }
}
```

**Pourquoi liste et pas contenu ?** :
- Pas de duplication tokens (EXPLORE lit → Claude reçoit → passe aux autres)
- EXPLORE = découverte pure, pas lecture complète
- Claude contrôle ce qui est lu ensuite

#### **ÉTAPE 3 : Lire contexte minimal**
**Objectif** : Lire UNIQUEMENT fichiers identifiés par EXPLORE.

```markdown
Pour chaque fichier dans EXPLORE.files_to_read :
  Read(file_path)
  Si sections spécifiques : Grep/parser sections
  Stocker contexte

Token saved : 3 fichiers ciblés au lieu de 10+ fichiers
```

**Question ouverte** : Que contient `context_loaded` ?
- Option A : Contenu complet fichiers → transmettre aux sub-agents (duplication tokens)
- Option B : Liste fichiers → sub-agents Read() eux-mêmes (pas de duplication)
- **À décider** : Approche B semble plus optimale

#### **ÉTAPE 4 : Setup Git**
```bash
git branch --list <branche>
# Si existe : git checkout <branche>
# Sinon : git checkout develop && git checkout -b <branche>
```

#### **ÉTAPE 5 : Lancer PLAN (avec retry)**
**Objectif** : Générer checklist niveau 2 + stratégie.

**Input PLAN** :
```javascript
{
  checklist_niveau_1: [...],
  context_loaded: {...},  // Ou liste fichiers si Option B
  retry_context: {        // null si première exécution
    plan_precedent: "...",
    feedback_user: "..."
  }
}
```

**PLAN fait** :
1. Analyser checklist niveau 1
2. Détecter stratégie (parallèle/séquentiel/unique)
3. Générer checklist niveau 2 détaillée

**PLAN retourne** :
```markdown
# Plan Niveau 2

## 🚀 Stratégie : Agents Parallèles
Lancer 10 agents CODE en parallèle.

## Checklist :
1. mkdir docs/references/ (séquentiel)
2-11. [PARALLÈLE] WebSearch + Write (x10)
12. Edit REFERENCES.md (séquentiel)
13. Commit
```

**Validation user avec retry** :
```
Claude formate plan généré
Claude demande : "✅ Valider ? (oui/non)"

Si NON :
  feedback_user = demander "Pourquoi ?"
  retry_context = {plan_precedent, feedback_user}
  Relancer PLAN avec retry_context

Si OUI :
  Continue
```

#### **ÉTAPE 6 : Lancer CODE (selon stratégie PLAN)**
**Objectif** : Exécuter checklist niveau 2.

**PLAN décide, Claude exécute** :

```javascript
if PLAN.strategie == "parallèle" :
  // Lancer N agents CODE en 1 message (multi-invoke)
  Task([
    {subagent_type: "code", prompt: "Étape 2"},
    {subagent_type: "code", prompt: "Étape 3"},
    ... x10
  ])

else if PLAN.strategie == "séquentiel" :
  Task(code_1) → attendre → Task(code_2) → ...

else :
  Task(code_unique)
```

**CODE tools** : `Bash(*), Read, Edit, MultiEdit, Write, Glob, Grep, WebSearch`

**CODE utilise WebSearch** :
- Phase 1-2 (recherche docs) : WebSearch actif
- Phase 5+ (code) : Documentation déjà créée (pas besoin WebSearch)

#### **ÉTAPE 7 : Lancer TEST**
**Objectif** : Valider conformité output.

**Input TEST** :
- Expected output
- Rapport CODE (coder_results)
- Plan (planner_results)

**TEST fait** :
1. Valider conformité au plan
2. Exécuter commandes validation (détectées dynamiquement)
3. Diagnostiquer erreurs si échec

**TEST retourne** :
```markdown
Status : ✅ PASS | ❌ FAIL

Si FAIL :
- Problèmes détectés
- Diagnostic cause
- Stratégie correction
```

#### **ÉTAPE 8 : Cocher PLAN.md**
```markdown
Edit(".claude/PLAN.md",
  old="- [ ] Item checklist",
  new="- [x] Item checklist"
)
```

---

## 🔧 Refactoring Par Agent

### 1. Agent EXPLORE

**Ajouts** :
- Phase 0 : Explore Codebase
  - Glob structure projet
  - Détecter stack (markers)
  - Identifier conventions
- Clarifier parsing YAML frontmatter
- Dictionnaire normalisation keywords
- Extraction sections CLAUDE.md

**Output étendu** :
```json
{
  "codebase": {...},
  "documentation": {
    "files_to_read": [...]
  }
}
```

### 2. Agent PLAN

**Modifications** :
- Retirer exemples Python hardcodés
- Garder logique décomposition générique
- Ajouter détection stratégie (parallèle/séquentiel)
- Supporter retry_context

**Output** :
```markdown
## Stratégie : [Parallèle|Séquentiel|Unique]
## Checklist Niveau 2 : [...]
```

### 3. Agent CODE

**Ajouts** :
- Tool WebSearch
- Phase détection stack (si nécessaire)

**Modifications** :
- Retirer commandes Python hardcodées
- Détecter outils qualité dynamiquement

### 4. Agent TEST

**Modifications** :
- Parser expected_output génériquement (pas de types hardcodés)
- Détecter commandes test depuis config projet
- Adapter validations selon stack

### 5. Commande execute-plan-phase

**Refactoring complet** selon workflow optimisé ci-dessus.

---

## 📝 Décisions Techniques

### Context_loaded : Quelle approche ?

**Question** : Que transmettre aux sub-agents ?

**Option A** : Claude lit fichiers complets → transmet contenu dans prompts
- ❌ Duplication tokens énorme (Claude lit + PLAN reçoit + CODE reçoit)

**Option B** : Claude transmet liste fichiers → sub-agents Read() eux-mêmes
- ✅ Pas de duplication
- ✅ Sub-agents ont Read tool
- ✅ Chaque agent lit ce dont il a besoin

**Option C** : Hybride (EXPLORE identifie sections précises + sub-agents lisent)
- ✅ Optimal
- Sub-agents extraient sections pertinentes

**Recommandation** : Option B ou C (à valider)

### Metadata YAML Template

Docs doivent avoir metadata :
```yaml
---
title: "..."
description: "..."
keywords: [...]
scope: ["code", "test", "deploy", "docs", "setup"]
technologies: [...]
---
```

Permet à EXPLORE de découvrir automatiquement.

---

## 🎯 Plan d'Action

### **Ordre** : Bottom-Up (Agents → Commande)

**Rationale** : Commande utilise agents → refactoriser agents d'abord pour que commande puisse les appeler correctement.

### Phase 1 : Refactoring Agents (ordre séquentiel)

1. ✅ **EXPLORE**
   - Ajouter exploration codebase (Glob markers, détecter stack)
   - Scanner docs (metadata YAML)
   - Retourner JSON : `{codebase: {...}, documentation: {files_to_read: [...]}}`
   - Optimisations : parsing YAML, extraction keywords, normalisation

2. ✅ **PLAN**
   - Retirer exemples Python hardcodés
   - Garder logique stratégie actuelle (parallèle/séquentiel/unique)
   - Supporter retry_context (feedback user)
   - Output : Checklist niveau 2 + stratégie markdown

3. ✅ **CODE**
   - Ajouter WebSearch dans tools
   - Utiliser info stack depuis EXPLORE (pas re-détecter)
   - Retirer commandes Python hardcodées
   - Peut être lancé x N en parallèle (selon PLAN)

4. ✅ **TEST**
   - Parser expected_output génériquement (pas types hardcodés)
   - Détecter commandes validation depuis config projet
   - Adapter selon stack

### Phase 2 : Refactoring Commande

5. ✅ **execute-plan-phase**
   - Workflow optimisé 8 étapes (Parser PLAN.md ciblé, EXPLORE, stocke liste, Setup Git, PLAN avec retry, CODE selon stratégie, TEST, Cocher PLAN.md)
   - Gestion erreurs sub-agents : informer user, user décide
   - TodoWrite optimisé

### Phase 3 : Cleanup & Quality

6. ✅ **Suppression anti-patterns**
   - Retirer toutes instructions négatives ("Ne PAS", "❌ NE PAS")
   - Convertir en instructions positives (ce qu'il faut faire)
   - Commits : `77b4632`, `8b617c4`

7. ✅ **Context-agnostic instructions**
   - Retirer références agents externes ("par EXPLORE", "de l'agent CODE")
   - Sub-agents ne connaissent que leur input/output
   - Instructions génériques et réutilisables

### Phase 4 : Audit & Validation (COMPLÉTÉ)

8. ✅ **Audit Agents (Best Practices)** - Commit `572146b`
   - Référence : https://code.claude.com/docs/en/sub-agents
   - ✅ Isolation contexte : variables context-agnostic
   - ✅ Suppression références orchestration externe
   - ✅ Réduction verbosité 50-65% (best practices)
   - ✅ Instructions directes vs pseudo-code
   - ✅ 1 exemple par agent (vs 2-3)

9. ✅ **Audit Commande execute-plan-phase** - Commit `572146b`
   - Référence : https://code.claude.com/docs/en/slash-commands
   - ✅ Conformité metadata, validation args, gestion erreurs
   - ✅ Alignement variables avec agents corrigés
   - ✅ TodoWrite usage correct

10. ⏳ **Simulation End-to-End Système Complet**
    - ✅ Plan de tests amélioré (8 tests vs 5 initiaux)
    - ✅ Ajout Phase 0 (manquante) : Test 0.2 (Git Workflow & Release)
    - ✅ Correction phases inexistantes (4.2, 5.1 → 4.3, 6.1)
    - ✅ Couverture complète : Phases 0, 1, 2, 3, 4, 6
    - ✅ Diversité outputs : docs (4), config (3), CI/CD (2)
    - Tests à exécuter :
      - Test 1 : Phase 0.2 (Git Workflow & Release Automation)
      - Test 2 : Phase 1.2 (VERSIONS.md)
      - Test 3 : Phase 2.4 (PR Template)
      - Test 4 : Phase 3.1 (pyproject.toml complet - critique)
      - Test 5 : Phase 3.2 (Dockerfile multi-stage)
      - Test 6 : Phase 3.6 (CI Quality Checks)
      - Test 7 : Phase 4.3 (Spécifications Services)
      - Test 8 : Phase 6.1 (README.md complet)
    - ⏳ Exécution tests end-to-end
    - ⏳ Vérifier workflow complet fonctionne de bout en bout
    - ⏳ Identifier bugs/problèmes dans orchestration réelle

---

## 🔄 Workflow EPCT - Résumé Visuel

```
User : /execute-plan-phase 1.2
  ↓
execute-plan-phase (orchestrateur)
  │
  ├─ ÉTAPE 1 : Parser PLAN.md → extraire Phase 1.2
  │
  ├─ ÉTAPE 2 : Task(explore)
  │   └─ EXPLORE retourne : liste fichiers
  │
  ├─ ÉTAPE 3 : Claude stocke liste fichiers (ne lit PAS)
  │
  ├─ ÉTAPE 4 : Setup Git
  │
  ├─ ÉTAPE 5 : Task(plan)
  │   └─ PLAN retourne : checklist niveau 2 + stratégie
  │   └─ Validation user (retry si non)
  │
  ├─ ÉTAPE 6 : Task(code) x N (selon stratégie PLAN)
  │   └─ CODE exécute checklist
  │
  ├─ ÉTAPE 7 : Task(test)
  │   └─ TEST valide conformité
  │
  └─ ÉTAPE 8 : Edit PLAN.md (cocher cases)

  ↓
User : Phase terminée ✅
```

---

## 📚 Références

- **Workflow EPCT** : https://gist.github.com/sergeyk/2517cb64f1888226b7acc983cd3bd651
- **TEMPLATE.md** : Format metadata YAML docs
- **PLAN.md** : Phases projet (checklist niveau 1)
- **CLAUDE.md** : Standards et conventions projet

---

## ✅ Points Validés

1. ✅ **Retry logic PLAN** : Contexte + feedback user si validation échoue
2. ✅ **EXPLORE retourne liste fichiers** (pas contenu)
3. ✅ **Sub-agents lisent eux-mêmes** (pas de duplication tokens)
4. ✅ **PLAN décide stratégie** (parallèle/séquentiel/unique - logique actuelle fonctionne bien)
5. ✅ **Claude lance agents** selon décision PLAN
6. ✅ **CODE a WebSearch** pour phases recherche
7. ✅ **Ordre refactoring** : Agents d'abord (bottom-up), puis commande
8. ✅ **Gestion erreurs sub-agents** : Claude informe user, user décide (pas auto-retry)
9. ✅ **Fallback metadata** : Ignorer (docs toujours dans `docs/` avec metadata YAML)
10. ✅ **Détection stack** : EXPLORE détecte, Claude passe info à CODE (pas re-détection)

---

## 📋 Décisions Points d'Attention

### 1. Fallback docs sans metadata
**Décision** : Ignorer fichiers sans metadata YAML.

**Rationale** :
- Docs standardisées TOUJOURS dans `docs/` avec metadata YAML (selon TEMPLATE.md)
- README.md à la racine → pas scanné par EXPLORE (pas dans `docs/`)
- Si edge case (fichier dans `docs/` sans metadata) → warning mais continuer

### 2. Stratégie parallèle PLAN
**Décision** : Garder logique actuelle (séquentiel par défaut, PLAN juge au cas par cas).

**Rationale** :
- Logique actuelle dans execute-plan-phase fonctionne bien
- PLAN comprend déjà tâches indépendantes vs dépendances
- Pas besoin de sur-documenter critères

### 3. Détection stack CODE
**Décision** : CODE utilise info stack depuis EXPLORE (pas de re-détection).

**Workflow** :
- EXPLORE détecte stack (Phase 2) → retourne dans JSON
- Claude stocke info stack
- Claude passe à CODE dans prompt
- CODE utilise directement pour adapter commandes qualité

### 4. Gestion erreurs sub-agents
**Décision** : Claude informe user, user décide.

**Comportement** :
```
Si sub-agent échoue :
1. Claude reçoit erreur
2. Claude informe user : "[Agent] a échoué : [raison]"
3. Claude demande : "Continuer / Retry / Abort ?"
4. User choisit action
```

Pas d'auto-retry automatique → user garde contrôle.

### 5. Exploration codebase EXPLORE
**Décision** : EXPLORE scanne codebase + docs (comme workflow EPCT original).

**Phase 0 : Explore Codebase**
```markdown
1. Détecter stack :
   - Glob("pyproject.toml") → Python
   - Glob("package.json") → JS/TS
   - Glob("go.mod") → Go
   - Glob("Cargo.toml") → Rust

2. Identifier fichiers existants pertinents :
   - Glob selon keywords checklist
   - Exemples : "API" → **/*routes*, "models" → **/*models*

3. Parser config projet (si existe) :
   - Python : Read("pyproject.toml") → [tool.ruff], [tool.mypy]
   - JS : Read("package.json") → scripts
   - Extraire conventions

4. Scanner docs (metadata YAML)

5. Retourner JSON :
   {
     "codebase": {
       "stack": "python",
       "markers": ["pyproject.toml"],
       "existing_files": ["app/main.py"],
       "conventions": {"linter": "ruff"}
     },
     "documentation": {
       "files_to_read": [...]
     }
   }
```

### 6. Ordre refactoring
**Décision** : **Option A - Bottom-Up** (Agents → Commande)

**Rationale** :
- Commande appelle agents → agents doivent être prêts d'abord
- Testable itérativement (1 agent à la fois)
- Moins risqué (fondations solides avant orchestration)

**Ordre** : EXPLORE → PLAN → CODE → TEST → execute-plan-phase

---

## ✅ Décision Finale : Option B (Liste Fichiers)

### Context_loaded : Sub-agents lisent eux-mêmes

**Décision** : **Option B** - Claude transmet liste, sub-agents Read() eux-mêmes.

**Pourquoi ?**

1. **Simplicité** ✅
   - Facile à implémenter
   - Pas de logique extraction complexe
   - Utilise Read() (tool existant dans tous les agents)

2. **Optimisation suffisante** ✅
   - EXPLORE filtre au niveau **fichier** (3 fichiers au lieu de 10)
   - Token saved **significatif** : 5000 tokens vs Option A
   - Différence vs Option C : ~1000 tokens seulement (pas worth la complexité)

3. **Robuste** ✅
   - Agents ont **tout le contexte** du fichier
   - Pas de risque de rater une info importante
   - Si agent a besoin d'une partie, il l'a déjà

4. **Pragmatique** ✅
   - Fichiers docs pas énormes (CLAUDE.md ~500 lignes = 2000 tokens)
   - Filtrer au niveau fichier suffit
   - Option C = optimisation prématurée (complexité >> gain marginal)

**Option C rejetée** : Trop complexe
- EXPLORE doit lire fichiers pour identifier sections → double lecture
- Agents doivent parser markdown + extraire sections → logique complexe
- Gain marginal (~1000 tokens) ne justifie pas la complexité

**Workflow final avec Option B** :

```javascript
// ÉTAPE 2 : EXPLORE retourne
{
  "files_to_read": [
    {"path": "docs/VERSIONS.md", "reason": "Versions exactes"},
    {"path": ".claude/CLAUDE.md", "reason": "Conventions code"}
  ]
}

// ÉTAPE 3 : Claude stocke liste (NE LIT PAS)
files_list = EXPLORE.files_to_read

// ÉTAPE 5 : PLAN
Task(plan, prompt="""
  Files disponibles (Read() toi-même) :
  - docs/VERSIONS.md
  - .claude/CLAUDE.md

  Génère checklist niveau 2.
""")

// PLAN fait :
versions = Read("docs/VERSIONS.md")  // 2000 tokens
claude = Read(".claude/CLAUDE.md")   // 3000 tokens
// Génère plan avec contexte complet

// ÉTAPE 6 : CODE
Task(code, prompt="""
  Files disponibles (Read() toi-même) :
  - docs/VERSIONS.md
  - .claude/CLAUDE.md

  Checklist : [...]
""")

// CODE fait :
versions = Read("docs/VERSIONS.md")  // 2000 tokens
claude = Read(".claude/CLAUDE.md")   // 3000 tokens
// Exécute checklist avec contexte complet
```

**Token usage** :
- Option A (contenu dans prompts) : 15000 tokens ❌
- **Option B (agents lisent)** : **10000 tokens** ✅
- Option C (agents lisent + filtrent) : 11000 tokens (trop complexe pour gain marginal)

---

## 📋 Phase 4 : Audit & Validation Détaillé

### 🔍 Audit 1 : Agents (Best Practices)

**Référence** : https://code.claude.com/docs/en/sub-agents

**Checklist de conformité pour chaque agent (EXPLORE, PLAN, CODE, TEST)** :

#### 1. **Responsabilités Claires**
- [ ] Mission principale définie en 1-2 phrases
- [ ] Scope limité et bien défini (pas de responsabilités qui débordent)
- [ ] Pas de chevauchement avec autres agents
- [ ] Exemples concrets d'usage dans description

#### 2. **Isolation Contexte**
- [ ] Agent ne connaît QUE ce qui est dans son prompt
- [ ] Aucune référence à orchestration externe (autres agents, commandes)
- [ ] Input clairement documenté (ce qu'il reçoit)
- [ ] Output clairement documenté (ce qu'il retourne)
- [ ] Pas d'assumptions sur workflow global

#### 3. **Instructions Context-Agnostic**
- [ ] Terminologie générique (pas "EXPLORE dit", mais "contexte fourni")
- [ ] Aucun "par EXPLORE", "depuis PLAN", "de l'agent CODE"
- [ ] Instructions positives (ce qu'il faut faire, pas ce qu'il ne faut PAS)
- [ ] Adaptable à n'importe quel projet/stack

#### 4. **Tools Appropriés**
- [ ] Only tools nécessaires listés (pas de tools inutilisés)
- [ ] Bash avec restrictions appropriées (patterns autorisés)
- [ ] Read/Write/Edit utilisés correctement
- [ ] WebSearch uniquement si nécessaire (PLAN, CODE pour recherche docs)

#### 5. **Output Structuré**
- [ ] Format de sortie bien défini (JSON, Markdown, etc.)
- [ ] Schéma explicite si JSON
- [ ] Exemples de sortie fournis
- [ ] Validation output possible (parsable, structure connue)

#### 6. **Gestion Erreurs**
- [ ] Comportement en cas d'erreur documenté
- [ ] Pas d'auto-retry (orchestrateur décide)
- [ ] Rapport d'erreur structuré
- [ ] Diagnostic actionnable si échec

**Actions à effectuer** :
1. Lire docs Claude Code sur sub-agents
2. Vérifier chaque agent contre checklist
3. Corriger non-conformités identifiées
4. Documenter changements dans commits

---

### 🔍 Audit 2 : Commande execute-plan-phase

**Référence** : https://code.claude.com/docs/en/slash-commands

**Checklist de conformité** :

#### 1. **Metadata YAML**
- [ ] `description` : Claire et concise (1 phrase)
- [ ] `argument-hint` : Format attendu explicite (ex: `<phase_number>`)
- [ ] `allowed-tools` : Liste complète et justifiée
- [ ] Pas de metadata inutile

#### 2. **Validation Arguments**
- [ ] Vérification argument requis AVANT exécution
- [ ] Message d'erreur clair si manquant
- [ ] Exemples d'usage fournis
- [ ] Stop immédiat si validation échoue

#### 3. **Gestion Erreurs**
- [ ] Erreurs sub-agents capturées et reportées
- [ ] User informé en cas d'échec
- [ ] User décide de la suite (retry/skip/abort)
- [ ] Pas d'auto-retry silencieux

#### 4. **Messages User**
- [ ] Messages clairs à chaque étape
- [ ] Feedback progression (émojis, statuts)
- [ ] Résultats intermédiaires affichés
- [ ] Résumé final complet

#### 5. **TodoWrite Usage**
- [ ] Todo list niveau 1 (orchestration)
- [ ] Status mis à jour en temps réel
- [ ] 1 seul todo in_progress à la fois
- [ ] Completed marqué immédiatement après fin

#### 6. **Robustesse**
- [ ] Gestion branche Git (existe/créer)
- [ ] Validation plan user avec retry loop
- [ ] Cleanup si interruption (git, docker, etc.)
- [ ] Logs structurés pour debugging

**Actions à effectuer** :
1. Lire docs Claude Code sur slash commands
2. Vérifier commande contre checklist
3. Tester edge cases (argument manquant, erreur agent, etc.)
4. Améliorer gestion erreurs si nécessaire

---

### 🧪 Simulation End-to-End : Plan de Test

**Objectif** : Valider que le système EPCT fonctionne de bout en bout sur phases variées couvrant tous les types d'outputs

**Stratégie** : 1-2 tests par phase majeure, diversité maximale (docs, config, code, docker, CI/CD)

**Couverture** :
- Phase 0 : Setup Documentation & Git
- Phase 1 : Recherche & Documentation
- Phase 2 : Architecture & Squelette
- Phase 3 : Configuration & Build
- Phase 4 : Planning détaillé développement
- Phase 6 : Documentation finale & Release MVP

---

#### **Test 1 : Phase 0.2 (Git Workflow & Release Automation)**
**Type** : Configuration Git + GitHub Actions
**Complexité** : Moyenne
**Attendu** :
- EXPLORE trouve docs/references/github-actions.md
- PLAN génère checklist ~10 étapes (workflow release.yml + branch protection)
- CODE crée .github/workflows/release.yml + .gitignore adapté
- TEST valide syntaxe YAML workflow + structure .gitignore

**Commande** :
```bash
/execute-plan-phase 0.2
```

**Success Criteria** :
- ✅ release.yml créé avec triggers corrects (tags v*)
- ✅ .gitignore adapté stack Python (venv, __pycache__, .env)
- ✅ YAML valide et testable
- ✅ Commit conventional commits effectué

---

#### **Test 2 : Phase 1.2 (VERSIONS.md)**
**Type** : Documentation technique avec metadata
**Complexité** : Faible
**Attendu** :
- EXPLORE trouve docs/TEMPLATE.md + .claude/CLAUDE.md
- PLAN génère checklist ~6 étapes
- CODE crée VERSIONS.md avec metadata YAML + matrice compatibilité
- TEST valide format markdown + metadata parsable

**Commande** :
```bash
/execute-plan-phase 1.2
```

**Success Criteria** :
- ✅ VERSIONS.md créé avec frontmatter YAML valide
- ✅ Sections attendues présentes (Python 3.13.1+, FastAPI 0.121.2+, etc.)
- ✅ Matrice compatibilité complète
- ✅ Commit conventional commits effectué

---

#### **Test 3 : Phase 2.4 (Création PR Template)**
**Type** : Documentation GitHub markdown
**Complexité** : Faible-Moyenne
**Attendu** :
- EXPLORE détecte .github/ existant, conventions Conventional Commits
- PLAN génère checklist ~5 étapes
- CODE crée .github/PULL_REQUEST_TEMPLATE.md avec sections standards
- TEST valide format markdown + checklist présente

**Commande** :
```bash
/execute-plan-phase 2.4
```

**Success Criteria** :
- ✅ Template créé avec sections (Description, Type, Testing, Checklist)
- ✅ Format markdown valide
- ✅ Cohérent avec Conventional Commits

---

#### **Test 4 : Phase 3.1 (pyproject.toml complet)**
**Type** : Configuration projet Python (critique)
**Complexité** : Haute
**Attendu** :
- EXPLORE détecte stack Python, lit VERSIONS.md + CLAUDE.md pour standards
- PLAN génère checklist ~15 étapes (metadata + deps + tools)
- CODE crée pyproject.toml complet (dependencies, ruff, mypy, pytest)
- TEST valide syntaxe TOML + install deps + lint/typecheck

**Commande** :
```bash
/execute-plan-phase 3.1
```

**Success Criteria** :
- ✅ pyproject.toml parsable et complet (5 sections minimum)
- ✅ Dependencies avec versions exactes depuis VERSIONS.md
- ✅ Config ruff + mypy stricte conforme CLAUDE.md
- ✅ `uv sync` réussit sans erreur

---

#### **Test 5 : Phase 3.2 (Dockerfile multi-stage)**
**Type** : Configuration Docker production
**Complexité** : Haute
**Attendu** :
- EXPLORE détecte stack Python, package_manager uv, docs/references/dokploy.md
- PLAN génère checklist ~12 étapes (multi-stage, healthcheck, security)
- CODE crée Dockerfile optimisé (builder + runtime)
- TEST valide docker build + run + healthcheck

**Commande** :
```bash
/execute-plan-phase 3.2
```

**Success Criteria** :
- ✅ Dockerfile multi-stage (builder + runtime)
- ✅ User non-root configuré
- ✅ Healthcheck défini
- ✅ `docker build` + `docker run` OK + health endpoint répond

---

#### **Test 6 : Phase 3.6 (CI Quality Checks)**
**Type** : Configuration CI/CD GitHub Actions
**Complexité** : Moyenne-Haute
**Attendu** :
- EXPLORE détecte stack Python, conventions (ruff, mypy), docs/references/github-actions.md
- PLAN génère checklist ~14 étapes (workflow avec jobs parallèles)
- CODE crée .github/workflows/ci.yml adapté au stack
- TEST valide syntaxe YAML + jobs définis

**Commande** :
```bash
/execute-plan-phase 3.6
```

**Success Criteria** :
- ✅ Workflow adapté au stack (Python → ruff, mypy, pytest)
- ✅ Jobs parallèles configurés (lint, format, typecheck, test)
- ✅ Cache uv dependencies configuré
- ✅ YAML valide et testable (syntax check)

---

#### **Test 7 : Phase 4.3 (Spécifications Services)**
**Type** : Documentation planning détaillé
**Complexité** : Moyenne
**Attendu** :
- EXPLORE identifie docs/references/ pertinents (crawl4ai, tenacity, decodo-proxies)
- PLAN génère checklist ~8 étapes (5 services à documenter)
- CODE crée section complète dans docs/PLANNING.md
- TEST valide format markdown + cohérence specs

**Commande** :
```bash
/execute-plan-phase 4.3
```

**Success Criteria** :
- ✅ Section Services ajoutée à PLANNING.md
- ✅ Specs détaillées pour 5 services (CombinationGenerator, ProxyService, CrawlerService, FlightParser, SearchService)
- ✅ Liste tests unitaires par service
- ✅ Format markdown valide

---

#### **Test 8 : Phase 6.1 (README.md complet)**
**Type** : Documentation utilisateur finale
**Complexité** : Moyenne-Haute
**Attendu** :
- EXPLORE lit ARCHITECTURE.md, PLANNING.md, pyproject.toml, Dockerfile
- PLAN génère checklist ~10 étapes (9 sections README)
- CODE crée README.md professionnel avec exemples
- TEST valide format markdown + liens valides + code blocks syntaxe correcte

**Commande** :
```bash
/execute-plan-phase 6.1
```

**Success Criteria** :
- ✅ README complet avec 9 sections (Description, Prérequis, Installation, Config, Usage, Tests, Déploiement, Limites, Monitoring)
- ✅ Exemples curl fonctionnels
- ✅ Liens internes valides
- ✅ Code blocks avec syntaxe highlighting

---

### 📊 Métriques Validation Globale

**Pour chaque test, tracker** :

1. **Performance** :
   - Temps total exécution
   - Tokens utilisés par agent
   - Nombre d'itérations retry (plan validation)

2. **Qualité** :
   - Conformité checklist (100% étapes complétées ?)
   - Tests passent (linter, type check, unit tests)
   - Output conforme à expected_output

3. **Robustesse** :
   - Gestion erreurs (détection + report)
   - Recovery après échec sub-agent
   - Messages user clairs et actionnables

4. **Bugs Identifiés** :
   - Lister tous problèmes rencontrés
   - Classifier (critique/majeur/mineur)
   - Créer issues GitHub si nécessaire

**Success Global** :
- ✅ 8/8 tests passent sans intervention manuelle
- ✅ Aucun bug critique
- ✅ Workflow utilisable en production
- ✅ Documentation agents conforme best practices
- ✅ Couverture complète : toutes les phases majeures testées (0-6)
- ✅ Diversité outputs : docs (4), config (3), CI/CD (2)

---

## 📝 Commits Refactoring

**Session actuelle** :
- `6058738` - refactor(commands): implement 8-step optimized workflow in execute-plan-phase
- `77b4632` - refactor(agents+commands): remove anti-patterns (negative instructions)
- `8b617c4` - fix(agents): remove external context references in sub-agents

**Sessions précédentes** :
- `2b902d9` - refactor(agents): make TEST agent fully generic
- `d35e576` - refactor(agents): make CODE agent generic + add WebSearch
- (voir git log pour historique complet)

---

**Fin du document de refactoring**
