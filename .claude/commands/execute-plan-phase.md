---
description: Orchestrateur intelligent d'exécution de phases de projet selon PLAN.md
argument-hint: '[--force] [<phase_number>] (ex: /execute-plan-phase, /execute-plan-phase 4.2, /execute-plan-phase --force 4.1)'
allowed-tools: TodoWrite, Read, Bash, Task, Edit
---

# Commande execute-plan-phase

Tu orchestres l'exécution autonome d'une sous-phase du PLAN.md avec stratégie adaptative (agents parallèles ou unique).

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
6. Lancer agent(s) CODE ou DOCUMENT (selon stratégie PLAN : parallèle/unique)
7. Lancer agent TEST (validation conformité)
8. Cocher cases dans PLAN.md

## 🚀 Process Exécution

### ÉTAPE PRÉLIMINAIRE : Parsing arguments & Validation

**A. Parser arguments** :
1. **Aucun arg** : Auto-détection première phase non cochée
2. **`--force <phase>`** : Re-exécution forcée
3. **`<phase>`** : Phase spécifique

**B. Déterminer phase cible** :

**Cas 1 : Auto-détection**
```
🔍 Recherche première phase non cochée...
```
- Lire `.claude/PLAN.md`, parser sous-phases `### X.Y`
- Identifier première avec `- [ ]` → stocker `phase_number`
- **Si toutes cochées** :
  ```
  ✅ Toutes phases terminées !
  💡 Re-exécuter : /execute-plan-phase --force <phase>
  ```
  **ARRÊTER.**
- **Si phase détectée** :
  ```
  📌 Phase {X.Y} détectée : {titre}
  ```
  → Continuer **Étape C**

**Cas 2 : `--force <phase>`**
```
⚠️ Mode force : re-exécution phase {X.Y}
```
- Stocker `phase_number`, `force_mode=true`
- **Sauter Étape C**, aller ÉTAPE 0

**Cas 3 : `<phase>`**
- Stocker `phase_number`, `force_mode=false`
- → Continuer **Étape C**

**C. Vérifier checkbox (si `force_mode=false`)** :

Lire `.claude/PLAN.md`, parser sous-phase `{phase_number}` :
- **Si toutes `- [x]`** (déjà réalisée) :
  ```
  ❌ Phase {X.Y} déjà réalisée
  💡 Re-exécuter : /execute-plan-phase --force {X.Y}
      Lancer prochaine : /execute-plan-phase
  ```
  **ARRÊTER.**
- **Si au moins 1 `- [ ]`** :
  ```
  ✅ Phase valide
  ```
  → Continuer ÉTAPE 0

### ÉTAPE 0 : Initialisation Todo List

Créer todo list Niveau 1 (orchestration, fixe) :

```
TodoWrite([
  {content: "Parser PLAN.md (phase ciblée)", status: "pending", activeForm: "Parsing PLAN.md"},
  {content: "Lancer agent EXPLORE", status: "pending", activeForm: "Lancement EXPLORE"},
  {content: "Stocker liste fichiers", status: "pending", activeForm: "Stockage liste"},
  {content: "Setup Git", status: "pending", activeForm: "Configuration Git"},
  {content: "Lancer agent PLAN", status: "pending", activeForm: "Lancement PLAN"},
  {content: "Lancer agent d'exécution", status: "pending", activeForm: "Lancement agent"},
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
  - Stocker dans variable : `nom_branche`

**Sous-phase** (ex: 1.1) :
- Titre complet
- Type de tâche (`🏷️ **Type**` : config|code|docs|docker|test)
  - Stocker dans variable : `task_type`
- **Checklist niveau 1** : Toutes lignes `- [ ]` ou `- [x]`
  - Stocker dans variable : `checklist_niveau_1` (liste de strings bruts)
- Output attendu (`📝 **Output**`)
  - Stocker dans variable : `expected_output`
- Notes

**Exemple** :
```
checklist_niveau_1 = [
  "Specs : CrawlerService (Crawl4AI + AsyncWebCrawler)",
  "Specs : FlightParser (JsonCssExtractionStrategy, sélecteurs CSS)",
  "Ajouter à `docs/specs/epic-2-google-flights/story-4-crawler-parser.md`",
  "Commit : `docs(specs): add story 4 specifications`"
]
```

Marquer → completed

### ÉTAPE 2 : Lancer agent EXPLORE

Marquer "Lancer agent EXPLORE" → in_progress

**Lancer agent via Task tool** :

```
Task(
  subagent_type="explore",
  description="Explorer codebase et docs",
  prompt="""
  Explorer le projet pour cette tâche :

  **Checklist niveau 1** :
  {checklist_niveau_1}

  **Output attendu** :
  {expected_output}

  Explorer :
  1. Codebase : stack, conventions, fichiers existants
  2. Documentation : fichiers pertinents selon metadata YAML

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
- `codebase` : Tout le bloc `codebase`
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
  description="Planification détaillée",
  prompt="""
  Créer plan d'implémentation détaillé (checklist niveau 2) pour :

  **Type tâche** : {task_type}

  **Checklist niveau 1** :
  {checklist_niveau_1}

  **Output attendu** :
  {expected_output}

  **Contexte codebase** :
  {codebase}

  **Fichiers pertinents** :
  {documentation_files}

  Génère :
  1. Checklist niveau 2 (détaillée, exécutable)
  2. Stratégie d'exécution (parallèle/unique)
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
2. **Ajuster le plan markdown directement** sans relancer l'agent :
   - Appliquer les modifications demandées sur le plan
   - Exemples : inverser étapes, changer mots, ajouter détails, retirer ligne, etc.
   - Conserver la structure markdown du plan
3. Afficher plan ajusté
4. Redemander validation
5. **Répéter jusqu'à validation "oui"**

**Si user répond "oui"** :

**Stocker et parser metadata orchestration** :

1. **Stocker plan complet** :
   - Variable `plan_details` = plan markdown complet retourné par agent PLAN
   - Ce plan sera transmis intégralement aux agents d'exécution et de validation

2. **Extraire metadata orchestration** (parsing minimal pour workflow uniquement) :

   **a) Déterminer agent d'exécution** :
   - Rechercher section `## 🤖 Agent d'Exécution`
   - Ligne `**Agent** : [CODE|DOCUMENT]`
   - Stocker dans variable `agent_type`

   **b) Extraire `document_type`** (si agent=DOCUMENT) :
   - Ligne `**Type document** : [specs|references|docs]`
   - Stocker dans variable `document_type`

   **c) Extraire stratégie d'exécution** :
   - Rechercher section `## 🚀 Stratégie`
   - Ligne `**Exécution** : [UNIQUE|PARALLÈLE]`
   - Stocker dans variable `strategie`

   **d) Si PARALLÈLE** :
   - Ligne `**Nombre d'agents** : [N agents]`
   - Ligne `**Division** : [description division]`
   - Stocker division pour orchestration

→ Continuer à ÉTAPE 6

Marquer → completed

### ÉTAPE 6 : Lancer agent(s) d'exécution (CODE ou DOCUMENT)

Marquer "Lancer agent d'exécution" → in_progress

**Variables disponibles depuis ÉTAPE 5** :
- `plan_details` : Plan markdown complet (transmis aux agents)
- `agent_type` : Agent d'exécution (CODE|DOCUMENT)
- `document_type` : Type de document (specs|references|docs) si agent=DOCUMENT
- `strategie` : Stratégie d'exécution (UNIQUE|PARALLÈLE)
- Division : Description répartition agents (si PARALLÈLE)

**Cas 1 : Stratégie PARALLÈLE**

**📋 Division Manuelle**

**Étape 1 : Lire division** dans `## 🚀 Stratégie` du plan :
- Nombre d'agents : N
- Division : "Agent 1: Étapes 1-3, Agent 2: Étapes 4-6, ..."

**Étape 2 : Parser checklist** (dans `## 📝 Checklist Niveau 2`) :
- Identifier étapes assignées par agent selon division
- Créer N sous-checklists contenant **UNIQUEMENT** les étapes respectives de chaque agent

**Étape 3 : Préparer N prompts** :
- Checklist : Sous-checklist agent
- Contexte : `codebase`, `documentation_files`, `expected_output`
- Type : Si DOCUMENT, ajouter `type` from plan

---

Lancer tous agents en **1 seul message** multi-invoke :

**Si agent=CODE** :
```
Task(subagent_type="code", prompt="""
Implémenter partie {N} du plan d'implémentation :

**Plan d'implémentation** :
{plan_details}

**checklist** :
{sous-checklist_N}

**Contexte codebase** : {codebase}
**Fichiers documentation** : {documentation_files}

**Instructions** :
1. Lire le plan complet pour comprendre le contexte global
2. Implémenter UNIQUEMENT la checklist assignée (variable `checklist`)
3. Respecter les Points d'Attention mentionnés dans le plan
4. Viser les Critères de Validation Finale du plan
5. Respecter conventions projet (codebase)

⚠️ Ne pas implémenter les étapes des autres agents.
""")
```

**Si agent=DOCUMENT** :
```
Task(subagent_type="document", prompt="""
Rédiger partie {N} du plan d'implémentation :

**Plan d'implémentation** :
{plan_details}

**checklist** :
{sous-checklist_N}

**Type document** : {document_type}
**Fichiers documentation** : {documentation_files}

**Instructions** :
1. Lire le plan complet pour comprendre le contexte global
2. Rédiger UNIQUEMENT la checklist assignée (variable `checklist`)
3. Respecter les Points d'Attention mentionnés dans le plan
4. Viser les Critères de Validation Finale du plan
5. Suivre template {TEMPLATE_SPECS.md | TEMPLATE_REFERENCES.md | TEMPLATE.md}

⚠️ Ne pas rédiger les sections des autres agents.
""")
```

**Cas 2 : Stratégie UNIQUE**

**Si agent=CODE** :
```
Task(subagent_type="code", prompt="""
Implémenter phase complète selon plan d'implémentation :

**Plan d'implémentation** :
{plan_details}

**Contexte codebase** : {codebase}
**Fichiers documentation** : {documentation_files}

**Instructions** :
1. Lire le plan complet (Objectif, Checklist, Points d'Attention, Critères Validation)
2. Implémenter TOUTES les étapes de la checklist niveau 2 dans l'ordre
3. Respecter les Points d'Attention mentionnés dans le plan
4. Viser les Critères de Validation Finale du plan
5. Respecter conventions projet (codebase)
""")
```

**Si agent=DOCUMENT** :
```
Task(subagent_type="document", prompt="""
Rédiger documentation complète selon plan d'implémentation :

**Plan d'implémentation** :
{plan_details}

**Type document** : {document_type}
**Fichiers documentation** : {documentation_files}

**Instructions** :
1. Lire le plan complet (Objectif, Checklist, Points d'Attention, Critères Validation)
2. Rédiger TOUTES les sections de la checklist niveau 2 dans l'ordre
3. Respecter les Points d'Attention mentionnés dans le plan
4. Viser les Critères de Validation Finale du plan
5. Suivre template {TEMPLATE_SPECS.md | TEMPLATE_REFERENCES.md | TEMPLATE.md}
""")
```

**Résultat attendu** : Rapport d'implémentation avec fichiers créés/modifiés

**Stocker résultat** :
- Variable `implementation_report` : Rapport(s) markdown retourné(s) par agent(s) CODE/DOCUMENT
- Si PARALLÈLE : Concaténer tous les rapports en un seul texte

Marquer → completed

### ÉTAPE 7 : Lancer agent TEST

Marquer "Lancer agent TEST" → in_progress

**Lancer agent via Task tool** :

```
Task(
  subagent_type="test",
  description="Validation implémentation",
  prompt="""
  Valider l'implémentation réalisée selon le plan d'implémentation :

  **Checklist Niveau 1 (PLAN.md - Macro)** :
  {checklist_niveau_1}

  **Plan d'implémentation complet** :
  {plan_details}

  **Contexte codebase** :
  {codebase}

  **Rapports d'implémentation** :
  {implementation_report}

  **Instructions de validation** :

  1. Lire le plan complet pour comprendre :
     - Checklist Niveau 2 (critères détaillés par étape)
     - Points d'Attention (risques/contraintes à vérifier en priorité)
     - Critères de Validation Finale (objectifs globaux de réussite)

  2. Vérifier conformité selon PRIORITÉ STRICTE (5 niveaux) :
     - **PRIORITÉ 1** : Checklist Niveau 1 (chemins fichiers exacts, outputs macro)
     - **PRIORITÉ 2** : Checklist Niveau 2 (contenu détaillé, critères succès par étape)
     - **PRIORITÉ 3** : Critères de Validation Finale (objectifs globaux du plan)
     - **PRIORITÉ 4** : Points d'Attention (risques/contraintes du plan)
     - **PRIORITÉ 5** : Tests techniques (selon type output + stack)

  3. Tenir compte des Points d'Attention du plan lors de la validation

  ⚠️ IMPORTANT : Si niveau 1 FAIL → ARRÊTER, ne pas valider niveaux suivants

  Retourner rapport validation complet (5 niveaux de validation).
  """
)
```

**Résultat attendu** : Rapport validation avec conformité niveau 1 + niveau 2 + critères globaux + points d'attention + tests techniques exécutés

**Si TEST échoue** :
- Afficher erreurs détectées (différencier niveau 1 vs niveau 2)
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
{checklist_niveau_1}

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

### Pendant Exécution (CODE ou DOCUMENT)
```
{si CODE} → 💻 Lancement agent(s) CODE...
{si DOCUMENT} → 📝 Lancement agent(s) DOCUMENT ({type})...
{si parallèle} → 🔀 {N} agents en parallèle
{si unique} → 🎯 1 agent unique
```

### Après Exécution
```
✅ {Implémentation | Rédaction} terminée
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