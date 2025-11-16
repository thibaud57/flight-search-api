# Pydantic v2 - Référence Technique

**Date de dernière mise à jour** : 16 novembre 2025

---

## 1. BaseSettings & Configuration d'Environnement

**Description**
`BaseSettings` hérite de `BaseModel` et ajoute le chargement automatique des variables d'environnement, fichiers `.env`, et secrets. Les variables d'environnement prennent toujours priorité sur les valeurs du fichier `.env`.

**Exemple minimal**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug_mode: bool = False

    class Config:
        env_file = '.env'
        env_prefix = 'APP_'

# Chargera APP_API_KEY et APP_DEBUG_MODE depuis l'environnement
settings = Settings()
```

**Source** : https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

## 2. Field Validator & Model Validator

**field_validator**

**Description**
Valide des champs individuels après (ou avant) le parsing Pydantic. Supporte 4 modes : `after` (défaut), `before`, `plain`, `wrap`.

**Exemple minimal**
```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    age: int

    @field_validator('age', mode='after')
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('age must be positive')
        return v
```

**model_validator**

**Description**
Valide l'ensemble du modèle après instantiation. Permet des validations cross-champs ou des transformations globales.

**Exemple minimal**
```python
from pydantic import BaseModel, model_validator

class Person(BaseModel):
    first_name: str
    last_name: str

    @model_validator(mode='after')
    def validate_names(self) -> 'Person':
        if self.first_name == self.last_name:
            raise ValueError('Names must be different')
        return self
```

**Source** : https://docs.pydantic.dev/latest/concepts/validators/

---

## 3. Configuration avec model_config

**Description**
Remplace la classe `Config` de v1. Utilise un dictionnaire `model_config` ou `ConfigDict` pour contrôler le comportement du modèle (extra fields, frozen, validation, etc.).

**Exemple minimal**
```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,           # Immutable
        validate_assignment=True,  # Valide les modifications
        extra='forbid',        # Rejette les champs supplémentaires
        str_strip_whitespace=True
    )

    name: str
    age: int
```

**Options clés**
- `extra` : `'ignore'` | `'forbid'` | `'allow'`
- `frozen` : Rend le modèle immutable
- `validate_default` : Valide les valeurs par défaut
- `validate_assignment` : Valide lors de modifications
- `strict` : Mode stricte (pas de coercion de types)

**Source** : https://docs.pydantic.dev/latest/api/config/

---

## 4. Migration v1 → v2 - Changements Importants

**Méthodes renommées**
| v1 | v2 |
|----|-----|
| `model.dict()` | `model.model_dump()` |
| `model.json()` | `model.model_dump_json()` |
| `Model.parse_obj(data)` | `Model.model_validate(data)` |
| `Model.parse_raw(json)` | `Model.model_validate_json(json)` |

**Décorateurs de validation remplacés**
| v1 | v2 |
|----|-----|
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |

**Champs optionnels**
```python
# v1
optional_field: Optional[str]  # ✓ Accepte None par défaut

# v2
optional_field: Optional[str] = None  # ✓ Doit spécifier le défaut
optional_field: str | None = None     # ✓ Syntaxe moderne
```

**Source** : https://docs.pydantic.dev/latest/migration/
