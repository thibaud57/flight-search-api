---
description: Orchestrateur intelligent d'exécution de phases de projet selon PLAN.md
argument-hint: '[--force] [<phase_number>]' (ex: /execute-plan-phase, /execute-plan-phase 4.2, /execute-plan-phase --force 4.1)
allowed-tools: TodoWrite, Read, Bash, Task, Edit
---

# Commande execute-plan-phase

Tu orchestres l'exécution autonome d'une sous-phase du PLAN.md avec stratégie adaptative (agents parallèles ou séquentiel).

## Usage

```bash
# Auto-détection : lance la première phase non cochée
/execute-plan-phase

# Phase spécifique
/execute-plan-phase 4.2

# Re-exécution forcée d'une phase déjà réalisée
/execute-plan-phase --force 4.1
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

### ÉTAPE PRÉLIMINAIRE : Parsing arguments & Validation checkbox

**A. Parser les arguments** :

Détecter 3 cas possibles :
1. **Aucun argument** : Mode auto-détection
2. **`--force <phase_number>`** : Re-exécution forcée
3. **`<phase_number>`** : Exécution phase spécifique

**B. Déterminer la phase cible** :

**Cas 1 : Aucun argument** (mode auto-détection)
```
🔍 Recherche de la première phase non cochée dans PLAN.md...
```
- Lire `.claude/PLAN.md`
- Parser toutes les sous-phases (format `### X.Y`)
- Identifier la **première** sous-phase avec au moins une case `- [ ]` (non cochée)
- Stocker : `phase_number` = X.Y détectée

**Si toutes les phases cochées** :
```
✅ Toutes les phases du PLAN.md sont terminées !

🎉 Projet complet selon PLAN.md

💡 Pour re-exécuter une phase : /execute-plan-phase --force <phase_number>
```
**ARRÊTER l'exécution.**

**Si phase détectée** :
```
📌 Phase {X.Y} détectée : {titre_phase}
🚀 Lancement de l'orchestration...
```
→ Continuer à **Étape C**

**Cas 2 : `--force <phase_number>`** (re-exécution forcée)
```
⚠️ Mode force activé : re-exécution de la phase {X.Y}
```
- Stocker : `phase_number` = argument fourni
- Stocker : `force_mode` = true
→ **Sauter Étape C** (pas de vérification checkbox), aller directement à ÉTAPE 0

**Cas 3 : `<phase_number>`** (exécution normale)
- Stocker : `phase_number` = argument fourni
- Stocker : `force_mode` = false
→ Continuer à **Étape C**

**C. Vérifier checkbox (si `force_mode` = false)** :

Lire `.claude/PLAN.md` et parser la sous-phase `{phase_number}` :
- Vérifier si **toutes** les cases de cette sous-phase sont cochées `- [x]`

**Si toutes cochées** (phase déjà réalisée) :
```
❌ Phase {X.Y} déjà réalisée (toutes les cases cochées)

📋 Checklist actuelle :
- [x] Item 1
- [x] Item 2
- [x] Item 3

💡 Options :
  • Re-exécuter quand même : /execute-plan-phase --force {X.Y}
  • Lancer prochaine phase : /execute-plan-phase
```
**ARRÊTER l'exécution.**

**Si au moins une case non cochée** `- [ ]` :
```
✅ Phase {X.Y} valide (items restants détectés)
🚀 Lancement de l'orchestration...
```
→ Continuer à ÉTAPE 0

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
  {content: "Cocher PLAN.md", status: "pending", activeForm: "Mise à jour PLAN"},
  {content: "Commit, Push & Pull Request", status: "pending", activeForm: "Création Pull Request"}
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

**⚠️ IMPORTANT** : Stocker le plan retourné pour retry éventuel.

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
2. Relancer Task(subagent_type="plan") avec le prompt suivant :
   ```
   Le plan précédent a été rejeté. Voici le feedback :

   {user_feedback}

   Plan précédent (AJUSTER selon feedback, NE PAS refaire from scratch) :
   {plan_complet_précédent}

   Ajuste le plan ci-dessus selon le feedback et re-génère.
   Conserve la structure existante, modifie uniquement ce qui est mentionné dans le feedback.
   ```

   ⚠️ **CRITIQUE** : Inclure le plan précédent complet dans le prompt, sinon l'agent va tout refaire.

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

### ÉTAPE 9 : Commit, Push & Pull Request

Marquer "Commit, Push & PR" → in_progress

**9A. Récupérer message(s) commit depuis PLAN.md** :

Dans la sous-phase parsée (ÉTAPE 1), chercher pattern(s) :
- `- [x] Commit : "message"`

**Cas 1 : Un seul commit**
```bash
git add .
git commit -m "{message}"
LAST_COMMIT_MSG="{message}"
```

**Cas 2 : Plusieurs commits** (ex: Phase 0.2 a 2 commits)
```bash
# Parser ordre commits dans PLAN.md
# Identifier fichiers concernés par chaque étape avant le commit

# Commit 1
git add {fichiers_avant_premier_commit}
git commit -m "{message_1}"

# Commit 2
git add {fichiers_avant_deuxième_commit}
git commit -m "{message_2}"
LAST_COMMIT_MSG="{message_2}"
```

**9B. Push branche** :
```bash
git push origin {nom_branche} --set-upstream
```

**9C. Créer Pull Request** :
```bash
PR_URL=$(gh pr create \
  --base develop \
  --title "$LAST_COMMIT_MSG" \
  --body "Implements Phase {X.Y}

## Story Changes
{checklist_niveau_1_resumé}

## Output
{expected_output}" \
  --json url --jq .url)
```

**Capturer URL PR** :
Stocker : `pr_url`

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
✅ Story {X.Y} terminée !

📄 Output : {expected_output}
📋 PLAN.md : Cases cochées
🔀 Pull Request : {pr_url}

🔄 **Prochaine étape** :

1. **Merger la PR sur GitHub** :
   Ouvrir {pr_url} et cliquer sur "Merge pull request"

2. **Continuer l'Epic** :
   ➡️ Lancer prochaine story automatiquement : /execute-plan-phase
   ➡️ Ou cibler manuellement : /execute-plan-phase {X.Y+1}
   (Attendre que la PR soit mergée avant de lancer)

3. **Si Epic complet** (voir "Fin de phase" dans PLAN.md) :
   ```bash
   git checkout develop && git pull
   git checkout master && git merge develop --ff-only
   git tag {version_tag}
   git push origin master --tags
   ```
   → GitHub Actions crée Release automatiquement
```