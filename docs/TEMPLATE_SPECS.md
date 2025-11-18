---
title: "Story X: [Nom story]"
scope: "specs"
category: "user-story"
epic: "Epic X: [Nom epic]"
story_points: 0
priority: "medium"  # low, medium, high, critical
status: "planned"   # planned, in_progress, completed, blocked
dependencies: []
date: YYYY-MM-DD
keywords: []
technologies: []
business_value: "[Valeur business 1-2 phrases]"
acceptance_criteria:
  - "[Critère 1]"
  - "[Critère 2]"
---

# Story X: [Nom story]

## 🎯 Contexte Business

**Besoin utilisateur**:
- [Décrire le besoin métier concret]
- [Qui utilise cette feature ?]
- [Quel problème résout-elle ?]

**Contraintes métier**:
- [Contrainte 1: limites techniques, budgets, SLA]
- [Contrainte 2]
- [Contrainte 3]

**Valeur business**:
- ✅ [Valeur 1: qu'apporte cette story au client final ?]
- ✅ [Valeur 2: feedback rapide, validation early, dérisquage]
- ✅ [Valeur 3: foundation pour stories futures]
- ✅ [Valeur 4: métriques observables]

**Métriques succès**:
- [Métrique 1: temps de réponse, taux d'erreur, etc.]
- [Métrique 2: adoption client, feedback qualitatif]
- [Métrique 3: coverage tests, qualité code]

---

## 📋 Spécifications Techniques

### 1. [Composant 1]

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

**Exemple**:
```python
# Exemple utilisation
exemple = ComposantExemple(param="value")
resultat = exemple.methode_principale(input_data)
```

### 2. [Composant 2]

[Répéter structure similaire pour chaque composant de la story]

---

## 🧪 Tests

### Tests unitaires (TDD)

**Format recommandé: AAA (Arrange/Act/Assert)**

#### [Composant 1] (X tests)

| # | Nom test | Input | Output attendu | Vérification |
|---|----------|-------|----------------|--------------|
| 1 | `test_composant_valid_input` | `{"key": "value"}` | `result.success == True` | Vérifie comportement nominal |
| 2 | `test_composant_edge_case` | `{"key": ""}` | `ValidationError` | Vérifie validation edge case |
| 3 | `test_composant_async` | `await call()` | `result` not None | Vérifie fonction async |

**Exemple code test AAA**:
```python
def test_composant_valid_input():
    # Arrange: Setup initial state
    input_data = {"key": "value"}

    # Act: Execute function under test
    result = composant_fonction(input_data)

    # Assert: Verify expected outcome
    assert result.success is True
    assert result.data == expected_data
```

#### [Composant 2] (Y tests)

[Répéter tableau tests + exemple pour chaque composant]

**Total tests unitaires**: X + Y = Z tests

---

### Tests intégration

**Format recommandé: Given/When/Then (BDD)**

**End-to-end** (N tests):

| # | Scénario | Prérequis | Action | Résultat attendu |
|---|----------|-----------|--------|-------------------|
| 1 | `test_integration_happy_path` | App running | POST /endpoint | 200 + JSON valide |
| 2 | `test_integration_validation_error` | App running | POST data invalide | 400 + error message |
| 3 | `test_integration_edge_case` | State X | Action Y | Result Z |

**Exemple code test Given/When/Then**:
```python
def test_integration_happy_path():
    # Given: Initial state and preconditions
    client = TestClient(app)
    request_data = {
        "field": "value"
    }

    # When: Execute action
    response = client.post("/endpoint", json=request_data)

    # Then: Verify expected outcome
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
    assert data["expected_field"] == expected_value
```

**Total tests intégration**: N tests

---

### Exemples JSON

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

## ✅ Critères d'acceptation

**Phase 4 (Specs)**:
- [ ] Spécifications techniques complètes (tous composants)
- [ ] Tests unitaires listés (tous scénarios couverts)
- [ ] Tests intégration listés
- [ ] Exemples JSON fournis

**Phase 5 (Implémentation TDD)**:
- [ ] **TDD Phase 1**: Tests unitaires [Composant 1] écrits
- [ ] **TDD Phase 1**: [Composant 1] implémenté → tests passent ✅
- [ ] **TDD Phase 2**: Tests unitaires [Composant 2] écrits
- [ ] **TDD Phase 2**: [Composant 2] implémenté → tests passent ✅
- [ ] **Tests intégration**: N tests end-to-end écrits
- [ ] **Tests intégration**: Tous tests intégration passent ✅
- [ ] **Validation manuelle**: Test curl/Postman fonctionne
- [ ] **Quality checks**: Ruff lint + format: 0 erreurs
- [ ] **Quality checks**: Mypy strict: 0 erreurs
- [ ] **Coverage**: ≥ 80% sur composants de cette story

**Documentation**:
- [ ] Docstrings 1 ligne (90% des fonctions)
- [ ] OpenAPI docs auto-générées (si route API)
- [ ] Logs structurés ajoutés (si applicable)

---

## 📝 Notes d'implémentation

**Dépendances**:
- [Story X]: [Pourquoi dépendance, quel composant nécessaire]
- [Story Y]: [Idem]

**Ordre TDD recommandé**:
1. [Composant 1]: Foundation, pas de dépendances
2. [Composant 2]: Dépend Composant 1
3. [Composant 3]: Dépend Composants 1 + 2
4. Tests intégration: Valide assemblage

**Fichiers créés/modifiés**:
- `app/[module]/[composant1].py`: [Rôle]
- `app/[module]/[composant2].py`: [Rôle]
- `tests/unit/test_[composant1].py`: X tests
- `tests/unit/test_[composant2].py`: Y tests
- `tests/integration/test_[feature].py`: N tests

**Commandes développement**:
```bash
# Lancer tests unitaires story
pytest tests/unit/test_[composant1].py tests/unit/test_[composant2].py -v

# Lancer tests intégration story
pytest tests/integration/test_[feature].py -v

# Quality checks
ruff check . --fix && ruff format . && mypy app/

# Coverage story
pytest --cov=app/[module] --cov-report=term-missing
```

**Commit message** (après implémentation complète):
```bash
git commit -m "feat([scope]): [description courte feature]

- Implement [Composant 1] with [détail important]
- Implement [Composant 2] with [détail important]
- Add X unit tests + N integration tests
- Coverage: Z% on [module]

Closes #[issue-number] (si applicable)"
```

**Temps estimé**:
- Specs (Phase 4): [X] heures
- Implémentation TDD (Phase 5): [Y] heures
- Total: [X+Y] heures (~[story_points] story points)

---

**Template version**: 1.0
**Last updated**: 2025-01-18
