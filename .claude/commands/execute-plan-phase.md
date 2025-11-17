---
description: Orchestrateur intelligent d'exécution de phases de projet selon PLAN.md
argument-hint: <phase_number> (ex: 1.1, 1.2, 5.3)
allowed-tools: TodoWrite, Read, Bash, Task, Edit
---

# Commande execute-plan-phase

Tu orchestres l'exécution autonome d'une sous-phase du PLAN.md avec stratégie adaptative (agents parallèles ou séquentiel).

## Usage

```bash
/execute-plan-phase 1.1
/execute-plan-phase 1.2
/execute-plan-phase 5.3
```

## 🎯 Mission

1. Parser PLAN.md (phase ciblée uniquement)
2. Lancer agent EXPLORE (retourne liste fichiers codebase + docs)
3. Stocker liste fichiers (sans lire le contenu)
4. Setup Git (checkout/create branche)
5. Lancer agent PLAN (génère checklist niveau 2 + stratégie, avec retry si validation fail)
6. Lancer agent(s) CODE (selon stratégie PLAN : parallèle/séquentiel/unique)
7. Lancer agent TEST (validation conformité)
8. Cocher cases dans PLAN.md

## 🚀 Process Exécution

### ÉTAPE PRÉLIMINAIRE : Validation argument

Vérifier que `<phase_number>` est fourni.

**Si manquant** :
```
❌ Erreur : Numéro de phase manquant

Usage : /execute-plan-phase <phase_number>

Exemples :
  /execute-plan-phase 1.1
  /execute-plan-phase 2.3
  /execute-plan-phase 5.1

💡 Consulte .claude/PLAN.md pour voir les phases disponibles
```

**ARRÊTER l'exécution si argument manquant.**

### ÉTAPE 0 : Initialisation Todo List

Créer todo list Niveau 1 (orchestration, fixe) :

```
TodoWrite([
  {content: "Parser PLAN.md (phase ciblée)", status: "pending", activeForm: "Parsing PLAN.md"},
  {content: "Lancer agent EXPLORE", status: "pending", activeForm: "Lancement EXPLORE"},
  {content: "Stocker liste fichiers", status: "pending", activeForm: "Stockage liste"},
  {content: "Setup Git", status: "pending", activeForm: "Configuration Git"},
  {content: "Lancer agent PLAN", status: "pending", activeForm: "Lancement PLAN"},
  {content: "Lancer agent(s) CODE", status: "pending", activeForm: "Lancement CODE"},
  {content: "Lancer agent TEST", status: "pending", activeForm: "Lancement TEST"},
  {content: "Cocher PLAN.md", status: "pending", activeForm: "Mise à jour PLAN"}
])
```

### ÉTAPE 1 : Parser PLAN.md (ciblé)

Marquer "Parser PLAN.md" → in_progress

Lire **uniquement** `.claude/PLAN.md` et parser :

**Phase parente** (ex: Phase 1 pour 1.1) :
- Objectif global
- Branche Git

**Sous-phase** (ex: 1.1) :
- Titre complet
- Checklist complète (toutes `- [ ]`)
- Output attendu (`📝 **Output**`)
- Notes

Marquer → completed

### ÉTAPE 2 : Lancer agent EXPLORE

Marquer "Lancer agent EXPLORE" → in_progress

**Lancer agent via Task tool** :

```
Task(
  subagent_type="explore",
  description="Explorer codebase et docs pour phase X.Y",
  prompt="""
  Explorer le projet pour la Phase {phase_number} : {phase_title}

  **Checklist niveau 1** :
  {checklist_from_plan_md}

  **Output attendu** :
  {expected_output}

  Explorer :
  1. Codebase (Phase 0A) : stack, conventions, fichiers existants
  2. Documentation (Phase 0B) : fichiers pertinents selon metadata YAML

  Retourner JSON avec :
  - codebase (stack, conventions, existing_files)
  - documentation (files_to_read)
  """
)
```

**Résultat attendu** : JSON avec structure définie dans agent explore.md

Marquer → completed

### ÉTAPE 3 : Stocker liste fichiers

Marquer "Stocker liste fichiers" → in_progress

**Extraire du JSON retourné par EXPLORE** :

```json
{
  "codebase": {
    "stack": "python|javascript|go|rust|...",
    "package_manager": "uv|npm|yarn|pnpm|cargo|go|...",
    "conventions": {
      "linter": "ruff|eslint|golangci-lint|clippy",
      "formatter": "ruff|prettier|gofmt|rustfmt",
      "type_checker": "mypy|tsc|flow|...",
      "test_runner": "pytest|vitest|go test|cargo test"
    },
    "existing_files": {
      "config": [...],
      "code": [...]
    }
  },
  "documentation": {
    "files_to_read": [...]
  }
}
```

**Stocker dans variables** :
- `codebase_context` : Tout le bloc `codebase`
- `documentation_files` : Liste de `documentation.files_to_read`

Marquer → completed

### ÉTAPE 4 : Setup Git

Marquer "Setup Git" → in_progress

```bash
# Vérifier branche
git branch --list <nom_branche>

# Si existe
git checkout <nom_branche>

# Sinon
git checkout develop
git checkout -b <nom_branche>
```

Marquer → completed

### ÉTAPE 5 : Lancer agent PLAN

Marquer "Lancer agent PLAN" → in_progress

**Lancer agent via Task tool** :

```
Task(
  subagent_type="plan",
  description="Planification détaillée phase X.Y",
  prompt="""
  Créer plan d'implémentation détaillé (checklist niveau 2) pour :

  **Phase** : {phase_number} - {phase_title}

  **Checklist niveau 1** (depuis PLAN.md) :
  {checklist_niveau_1}

  **Output attendu** :
  {expected_output}

  **Contexte codebase** :
  {codebase_context}

  **Fichiers pertinents** :
  {documentation_files}

  Génère :
  1. Checklist niveau 2 (détaillée, exécutable)
  2. Stratégie d'exécution (parallèle/séquentiel/unique)
  3. Points d'attention
  4. Critères validation finale
  """
)
```

**Résultat attendu** : Markdown avec checklist niveau 2 + stratégie

**Validation user avec retry** :

```
Afficher le plan généré :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Plan d'Implémentation - Phase {X.Y}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{plan_markdown_from_agent}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Valider ce plan ? (oui/non)
```

**Si user répond "non"** ou demande ajustements :
1. Capturer feedback user
2. Relancer Task(subagent_type="plan") avec retry_context :
   ```
   Task(
     subagent_type="plan",
     prompt="""
     Le plan précédent a été rejeté. Voici le feedback :

     {user_feedback}

     Plan précédent :
     {previous_plan}

     Ajuste le plan selon le feedback et re-génère.
     """
   )
   ```
3. Afficher nouveau plan
4. Redemander validation
5. **Répéter jusqu'à validation "oui"**

**Si user répond "oui"** :
→ Continuer à ÉTAPE 6

Marquer → completed

### ÉTAPE 6 : Lancer agent(s) CODE

Marquer "Lancer agent(s) CODE" → in_progress

**Parser stratégie du plan validé** :

Le plan contient une section `## 🚀 Stratégie` avec :
- **Parallèle** : Plusieurs agents CODE en parallèle
- **Séquentiel** : Un seul agent CODE ou plusieurs séquentiels
- **Unique** : Un seul agent CODE

**Cas 1 : Stratégie PARALLÈLE** (ex: "lancer 3 agents en parallèle")

Lancer tous agents CODE en **1 seul message** avec multi-invoke :

```
# Message unique avec 3 Task calls
Task(subagent_type="code", prompt="Agent 1: {instructions}") +
Task(subagent_type="code", prompt="Agent 2: {instructions}") +
Task(subagent_type="code", prompt="Agent 3: {instructions}")
```

Chaque agent reçoit :
```
Implémenter partie {N} de la checklist niveau 2 :

**Checklist niveau 2** :
{sous-ensemble_checklist_pour_cet_agent}

**Contexte codebase** :
{codebase}

**Fichiers pertinents** :
{documentation_files}

**Output attendu** :
{expected_output_partial}

Exécuter strictement la checklist, respecter conventions projet.
```

**Cas 2 : Stratégie SÉQUENTIEL**

Lancer agent(s) CODE un par un :

```
Task(
  subagent_type="code",
  description="Implémentation phase X.Y",
  prompt="""
  Implémenter la phase complète :

  **Checklist niveau 2** :
  {checklist}

  **Contexte codebase** :
  {codebase}

  **Fichiers pertinents** :
  {documentation_files}

  **Output attendu** :
  {expected_output}

  Exécuter strictement la checklist, respecter conventions projet.
  """
)
```

**Cas 3 : Stratégie UNIQUE**

Même que séquentiel, un seul agent CODE.

**Résultat attendu** : Rapport(s) d'implémentation avec fichiers créés/modifiés

Marquer → completed

### ÉTAPE 7 : Lancer agent TEST

Marquer "Lancer agent TEST" → in_progress

**Lancer agent via Task tool** :

```
Task(
  subagent_type="test",
  description="Validation phase X.Y",
  prompt="""
  Valider la phase {phase_number} :

  **Checklist niveau 2** (ce qui devait être fait) :
  {checklist_details}

  **Output attendu** :
  {expected_output}

  **Contexte codebase** :
  {codebase}

  **Rapports CODE** :
  {implementation_report}

  Vérifier :
  1. Conformité checklist (toutes étapes implémentées)
  2. Output produit (fichier existe, contenu valide)
  3. Qualité code (tests appropriés selon type output)

  Retourner rapport validation.
  """
)
```

**Résultat attendu** : Rapport validation avec conformité + tests exécutés

**Si TEST échoue** :
- Afficher erreurs détectées
- Demander au user : "Corriger et relancer TEST ? (oui/non)"
- Si oui : Relancer CODE puis TEST
- Si non : Arrêter (phase incomplète)

**Si TEST passe** :
→ Continuer à ÉTAPE 8

Marquer → completed

### ÉTAPE 8 : Cocher PLAN.md

Marquer "Cocher PLAN.md" → in_progress

Modifier `.claude/PLAN.md` :
- Remplacer `- [ ]` → `- [x]` pour tous items phase

Marquer → completed

## Messages Utilisateur

### Démarrage
```
🚀 Lancement orchestration Phase {X.Y}
📖 Parsing PLAN.md...
🔍 Lancement agent EXPLORE...
```

### Après EXPLORE
```
✅ Contexte exploré
📦 Stack : {stack}
🔧 Outils : linter={linter}, type_checker={type_checker}
📁 Fichiers pertinents : {N} fichiers identifiés
```

### Après PLAN
```
📋 Plan d'implémentation généré
{afficher_plan_markdown}

✅ Valider ce plan ? (oui/non)
```

### Pendant CODE
```
💻 Lancement agent(s) CODE...
{si parallèle} → 🔀 {N} agents en parallèle
{si séquentiel} → 🔄 Exécution séquentielle
```

### Après CODE
```
✅ Implémentation terminée
📝 Fichiers créés : {liste}
✏️ Fichiers modifiés : {liste}
```

### Pendant TEST
```
🧪 Lancement agent TEST...
```

### Après TEST (succès)
```
✅ Validation réussie !
{rapport_test}
```

### Après TEST (échec)
```
❌ Validation échouée
{erreurs}

Corriger et relancer TEST ? (oui/non)
```

### Completion
```
✅ Phase {X.Y} terminée !

📄 Output : {fichier_créé}
💾 Commits : {hash1}, {hash2}
📋 PLAN.md mis à jour

➡️ Prochaine : /execute-plan-phase {X.Y+1}
```