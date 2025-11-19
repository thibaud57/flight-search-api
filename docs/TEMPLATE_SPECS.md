---
title: "Story X: [Nom story]"
epic: "Epic X: [Nom epic]"
story_points: 0
dependencies: []
date: "YYYY-DD-MM"
keywords: []
scope: ["specs"]
technologies: []
---

<!--
⚠️ RÈGLES IMPORTANTES - Spécifications (à titre informatif, ne pas inclure dans stories)

**Ce template doit contenir UNIQUEMENT** :
- ✅ Interfaces/signatures (SANS implémentation)
- ✅ Descriptions comportements (texte structuré)
- ✅ Tableaux scénarios tests (descriptif, PAS code Python)
- ✅ Exemples JSON (inputs/outputs)

**CODE PRODUCTION INTERDIT** :
- ❌ Implémentation complète fonctions/classes
- ❌ Logique métier (algorithmes, boucles, conditions)
- ❌ Tests Python écrits

**Principe fondamental** :
- (Specs) = QUOI faire → Décrire comportements attendus
- (TDD) = COMMENT faire → Implémenter code production

Note: Agent DOCUMENT respecte automatiquement ces règles selon type "specs"
-->

# 🎯 Contexte Business

## Besoin utilisateur
- [Décrire le besoin métier concret]
- [Qui utilise cette feature ?]
- [Quel problème résout-elle ?]

## Contraintes métier
- [Contrainte 1: limites techniques, budgets, SLA]
- [Contrainte 2]
- [Contrainte 3]
- ...

## Valeur business
- ✅ [Valeur 1: qu'apporte cette story au client final ?]
- ✅ [Valeur 2: feedback rapide, validation early, dérisquage]
- ✅ [Valeur 3: foundation pour stories futures]
- ✅ [Valeur 4: métriques observables]
- ...

## Métriques succès
- [Métrique 1: temps de réponse, taux d'erreur, etc.]
- [Métrique 2: adoption client, feedback qualitatif]
- [Métrique 3: coverage tests, qualité code]
- ...

---

# 📋 Spécifications Techniques

## 1. [Composant 1]

**Rôle**: [Décrire responsabilité unique du composant]

**Interface**:
```python
class ComposantExemple:
    """Docstring 1 ligne."""

    def methode_principale(self, param: Type) -> ReturnType:
        """Docstring méthode."""
```

**Champs/Paramètres**:

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `field_name` | `str` | Description | min_length=2, max_length=100 |
| `field_number` | `int` | Description | ≥ 0, ≤ 1000 |

**Comportement**:
- [Comportement normal]
- [Edge cases]
- [Erreurs levées]

**Validations** (si Pydantic):
- `field_validator`: [Validation custom]
- `model_validator`: [Validation cross-field]

## 2. [Composant 2]

[Répéter structure similaire pour chaque composant de la story]

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé: AAA (Arrange/Act/Assert)**

### [Composant 1] (X tests)

**Format tableau descriptif** (6 colonnes) :

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_composant_valid_input` | Composant avec input valide | `{"key": "value"}` | `result.success == True` | Vérifie comportement nominal |
| 2 | `test_composant_edge_case` | Input avec string vide | `{"key": ""}` | Lève `ValidationError` | Vérifie validation edge case |
| 3 | `test_composant_async` | Appel fonction async | `await composant.call()` | `result` not None | Vérifie fonction async retourne valeur |

**Colonnes** :
- **#** : Numéro test (ordre logique)
- **Nom test** : Nom fonction test à écrire en Phase 5 (format `test_[composant]_[scenario]`)
- **Scénario** : Description comportement testé (1 phrase courte)
- **Input** : Données entrée (format compact, ex: `{"key": "value"}`)
- **Output attendu** : Résultat attendu (assertion principale)
- **Vérification** : Explication vérification (POURQUOI ce test est important)

### [Composant 2] (Y tests)

[Répéter tableau tests + exemple pour chaque composant]

**Total tests unitaires**: X + Y = Z tests

---

## Tests intégration

**Format recommandé: Given/When/Then (BDD)**

**Format tableau descriptif** (5 colonnes pour tests intégration) :

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_happy_path` | App running, client TestClient | POST /endpoint avec data valide | Status 200 + JSON conforme schéma |
| 2 | `test_integration_validation_error` | App running | POST /endpoint avec data invalide | Status 400 + error message clair |
| 3 | `test_integration_edge_case` | State X configuré | Action Y exécutée | Result Z vérifié |

**Colonnes** :
- **#** : Numéro test
- **Nom test** : Nom fonction test à écrire en Phase 5
- **Prérequis (Given)** : État initial et préconditions
- **Action (When)** : Action exécutée (ex: requête HTTP, appel fonction)
- **Résultat attendu (Then)** : Résultat vérifié (status code, données retournées, side-effects)

**Total tests intégration**: N tests

---

## Exemples JSON

**Exemple 1: Request valide**:
```json
{
  "field1": "value1",
  "field2": 123
}
```

**Exemple 2: Response succès**:
```json
{
  "status": "success",
  "data": {
    "result": "value"
  }
}
```

**Exemple 3: Error response**:
```json
{
  "status": "error",
  "detail": "Validation error message"
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels
1. **[Critère fonctionnel 1]** : Description vérifiable (ex: endpoint retourne status code 200)
2. **[Critère fonctionnel 2]** : Description quantifiable (ex: response time < 100ms au 99th percentile)
3. **[Critère fonctionnel 3]** : Description testable (ex: format JSON conforme au schéma Pydantic)
4. **[Critère N...]** : Ajouter autant de critères fonctionnels que nécessaire pour couvrir tous les comportements

## Critères techniques
5. **[Critère technique 1]** : Contrainte technique (ex: type safety strict avec Literal types)
6. **[Critère technique 2]** : Architecture (ex: endpoint synchrone `def` pas `async def`)
7. **[Critère technique 3]** : Dépendances (ex: sans appel DB/API externe)
8. **[Critère N...]** : Ajouter selon besoins de la story

## Critères qualité
9. **[Critère qualité 1]** : Coverage minimum (ex: ≥95% sur composants critiques)
10. **[Critère qualité 2]** : Tests passent (ex: X tests unitaires + Y tests intégration tous verts)
11. **[Critère qualité 3]** : Standards projet (ex: Ruff + Mypy + Type hints PEP 695)
12. **[Critère N...]** : Documentation, conventions nommage, etc.

## Critères production (si applicable)
13. **[Critère production 1]** : Déploiement (ex: HEALTHCHECK Dockerfile configuré)
14. **[Critère production 2]** : Monitoring (ex: intégration plateforme observabilité)
15. **[Critère N...]** : Scaling, error handling, logging structuré, etc.

---

**💡 Note importante** : Le nombre de critères varie selon la complexité de la story :
- Story simple (2 story points) : 8-12 critères typiquement
- Story moyenne (5 story points) : 12-18 critères
- Story complexe (8 story points) : 18-25+ critères

**Principe SMART** : Chaque critère doit être **S**pécifique, **M**esurable, **A**tteignable, **R**elevant, **T**emporel.
