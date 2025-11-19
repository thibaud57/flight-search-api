---
description: Orchestrateur intelligent d'exécution de phases de projet selon PLAN.md
argument-hint: '[--force] [<phase_number>]' (ex: /execute-plan-phase, /execute-plan-phase 4.2, /execute-plan-phase --force 4.1)
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

**Sous-phase** (ex: 1.1) :
- Titre complet
- Type de tâche (`🏷️ **Type**` : config|code|docs|docker|test)
- **Checklist niveau 1** : Toutes lignes `- [ ]` ou `- [x]`
  - Stocker dans variable : `checklist_niveau_1[]` (liste de strings bruts)
- Output attendu (`📝 **Output**`)
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
  description="Explorer codebase et docs pour phase X.Y",
  prompt="""
  Explorer le projet pour la Phase {phase_number} : {phase_title}

  **Checklist niveau 1** :
  {checklist_niveau_1}

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
  description="Planification détaillée phase X.Y",
  prompt="""
  Créer plan d'implémentation détaillé (checklist niveau 2) pour :

  **Phase** : {phase_number} - {phase_title}

  **Type tâche** : {task_type}

  **Checklist niveau 1** (depuis PLAN.md) :
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

### ÉTAPE 6 : Lancer agent(s) d'exécution (CODE ou DOCUMENT)

Marquer "Lancer agent d'exécution" → in_progress

**Parser agent d'exécution du plan validé** :

Le plan contient une section `## 🤖 Agent d'Exécution` avec :
- **Agent** : CODE ou DOCUMENT
- **Type document** (si agent=DOCUMENT) : specs, references, ou docs

**Stocker** :
- Variable `document_type` : Valeur de "Type document" (specs|references|docs) si agent=DOCUMENT

**Parser stratégie du plan validé** :

Le plan contient une section `## 🚀 Stratégie` avec :
- **Parallèle** : Plusieurs agents en parallèle
- **Unique** : Un seul agent

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
Implémenter partie {N} :

**Checklist** : {sous-checklist_N}
**Contexte** : {codebase}
**Fichiers** : {documentation_files}
**Output** : {expected_output}

Exécuter strictement la checklist, respecter conventions projet.
""")
```

**Si agent=DOCUMENT** :
```
Task(subagent_type="document", prompt="""
Rédiger partie {N} :

**Type** : {document_type}
**Checklist** : {sous-checklist_N}
**Fichiers** : {documentation_files}
**Output** : {expected_output}

Suivre strictement template {TEMPLATE_SPECS.md | TEMPLATE_REFERENCES.md | TEMPLATE.md}.
""")
```

**Cas 2 : Stratégie UNIQUE**

**Si agent=CODE** :
```
Task(subagent_type="code", prompt="""
Implémenter phase complète :

**Checklist** : {checklist_niveau_2}
**Contexte** : {codebase}
**Fichiers** : {documentation_files}
**Output** : {expected_output}

Exécuter strictement la checklist, respecter conventions projet.
""")
```

**Si agent=DOCUMENT** :
```
Task(subagent_type="document", prompt="""
Rédiger documentation complète :

**Type** : {document_type}
**Checklist** : {checklist_niveau_2}
**Fichiers** : {documentation_files}
**Output** : {expected_output}

Suivre strictement template {TEMPLATE_SPECS.md | TEMPLATE_REFERENCES.md | TEMPLATE.md}.
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
  description="Validation phase X.Y",
  prompt="""
  Valider la phase {phase_number} :

  **Checklist Niveau 1 (PLAN.md - Macro)** :
  {checklist_niveau_1}

  **Checklist Niveau 2 (Détaillée - PLAN)** :
  {checklist_niveau_2}

  **Output attendu** :
  {expected_output}

  **Contexte codebase** :
  {codebase}

  **Rapports d'implémentation** :
  {implementation_report}

  Vérifier (PRIORITÉ STRICTE) :
  1. **PRIORITÉ 1 : Checklist niveau 1** (chemins fichiers exacts, outputs macro)
  2. **PRIORITÉ 2 : Checklist niveau 2** (contenu détaillé, qualité)
  3. **PRIORITÉ 3 : Tests techniques** (selon type output)

  ⚠️ IMPORTANT : Si niveau 1 FAIL → ARRÊTER, ne pas valider niveau 2

  Retourner rapport validation avec les 2 checklists.
  """
)
```

**Résultat attendu** : Rapport validation avec conformité niveau 1 + niveau 2 + tests exécutés

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