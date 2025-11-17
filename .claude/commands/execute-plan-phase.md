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

1. Lire contexte projet (PLAN.md + docs/)
2. Extraire informations de la phase demandée
3. Setup Git (checkout/create branche)
4. Analyser checklist et détecter stratégie optimale
5. Proposer plan structuré au user avec agents si parallèle
6. Exécuter implémentation (lancer agents Task si détecté)
7. Cocher cases dans PLAN.md

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
  {content: "Lire contexte projet", status: "pending", activeForm: "Lecture contexte"},
  {content: "Extraire phase {phase}", status: "pending", activeForm: "Extraction phase"},
  {content: "Setup Git", status: "pending", activeForm: "Configuration Git"},
  {content: "Analyser stratégie", status: "pending", activeForm: "Analyse stratégie"},
  {content: "Proposer plan", status: "pending", activeForm: "Proposition plan"},
  {content: "Exécuter implémentation", status: "pending", activeForm: "Exécution"},
  {content: "Cocher PLAN.md", status: "pending", activeForm: "Mise à jour PLAN"}
])
```

### ÉTAPE 1 : Lire contexte projet

Marquer "Lire contexte projet" → in_progress

Lire **obligatoirement** :
- `.claude/PLAN.md` (complet)
- `.claude/CLAUDE.md` (si existe)
- Tous `docs/*.md` (VERSIONS, REFERENCES, architecture, PLANNING, CHANGELOG, ...)

Marquer → completed

### ÉTAPE 2 : Extraire informations phase

Marquer "Extraire phase" → in_progress

Parser PLAN.md, identifier :

**Phase parente** (ex: Phase 1 pour 1.1) :
- Objectif global
- Branche Git

**Sous-phase** (ex: 1.1) :
- Titre complet
- Checklist complète (toutes `- [ ]`)
- Output attendu (`📝 **Output**`)
- Notes

Marquer → completed

### ÉTAPE 3 : Setup Git

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

### ÉTAPE 4 : Analyser stratégie

Marquer "Analyser stratégie" → in_progress

Analyser checklist, détecter type :

**Type 1 : Web Research** → Agents // Task
- Mots-clés : "recherche", "documentation", "versions", URLs

**Type 2 : Création fichiers** → Séquentiel ou //
- Mots-clés : "créer", "structure", chemins fichiers

**Type 3 : Code/Tests** → Séquentiel
- Mots-clés : "implémenter", "tests", "TDD"

**Type 4 : Consolidation** → Séquentiel
- Mots-clés : "consolider", "vérifier", "matrice"

**Type 5 : Git** → Toujours séquentiel fin
- Mots-clés : "commit", "push"

Créer **Todo Niveau 2** (dynamique) adaptée.

Marquer → completed

### ÉTAPE 5 : Proposer plan

Marquer "Proposer plan" → in_progress

Afficher :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Phase {X.Y} : {Titre}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Objectif : {objectif}
🌿 Branche : {branche}
📄 Output : {fichier}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Checklist ({N} tâches)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{liste}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Stratégie
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{détail stratégie + agents si //}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Valider ? (oui/non)
```

**ATTENDRE validation user.**

Marquer → completed

### ÉTAPE 6 : Exécuter implémentation

Marquer "Exécuter implémentation" → in_progress

Suivre Todo Niveau 2 :

**Si agents // détectés** : Lancer tous via Task (1 message, multi-invoke)
**Sinon** : Exécuter séquentiellement
**Mettre à jour** Todo Niveau 2 au fur et à mesure

Marquer → completed

### ÉTAPE 7 : Cocher PLAN.md

Marquer "Cocher PLAN.md" → in_progress

Modifier `.claude/PLAN.md` :
- Remplacer `- [ ]` → `- [x]` pour tous items phase

Marquer → completed

## Messages Utilisateur

### Démarrage
```
🚀 Lancement orchestration Phase {X.Y}
📖 Lecture contexte projet...
```

### Completion
```
✅ Phase {X.Y} terminée !

📄 Output : {fichier_créé}
💾 Commit : {hash} - {message}
📋 PLAN.md mis à jour

➡️ Prochaine : /execute-plan-phase {X.Y+1}
```