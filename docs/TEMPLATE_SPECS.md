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

# 🎯 Contexte Business

## Besoin utilisateur
- [Décrire le besoin métier concret]
- [Qui utilise cette feature ?]
- [Quel problème résout-elle ?]

## Contraintes métier
- [Contrainte 1: limites techniques, budgets, SLA]
- [Contrainte 2]
- [Contrainte 3]

## Valeur business
- ✅ [Valeur 1: qu'apporte cette story au client final ?]
- ✅ [Valeur 2: feedback rapide, validation early, dérisquage]
- ✅ [Valeur 3: foundation pour stories futures]
- ✅ [Valeur 4: métriques observables]

## Métriques succès
- [Métrique 1: temps de réponse, taux d'erreur, etc.]
- [Métrique 2: adoption client, feedback qualitatif]
- [Métrique 3: coverage tests, qualité code]

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

**Exemple**:
```python
# Exemple utilisation
exemple = ComposantExemple(param="value")
resultat = exemple.methode_principale(input_data)
```

## 2. [Composant 2]

[Répéter structure similaire pour chaque composant de la story]

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé: AAA (Arrange/Act/Assert)**

### [Composant 1] (X tests)

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

### [Composant 2] (Y tests)

[Répéter tableau tests + exemple pour chaque composant]

**Total tests unitaires**: X + Y = Z tests

---

## Tests intégration

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

_À remplir_
