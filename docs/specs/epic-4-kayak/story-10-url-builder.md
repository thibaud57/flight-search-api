---
title: "Story 10: KayakUrlBuilder + Consent Handler"
epic: "Epic 4: Kayak Integration"
story_points: 5
dependencies: ["epic-3/story-9"]
date: "2025-25-11"
keywords: ["kayak", "url", "builder", "consent", "cookies", "rgpd", "playwright", "validation", "iata"]
scope: ["specs"]
technologies: ["kayak", "pydantic", "playwright", "crawl4ai"]
---

# 🎯 Contexte Business

## Besoin utilisateur

- Construire des URLs Kayak valides à partir de paramètres de recherche multi-city
- Gérer automatiquement le popup de consentement cookies (RGPD) pour débloquer le chargement des résultats
- Valider les codes aéroports IATA avant construction d'URL (éviter erreurs 404)

## Contraintes métier

- **Codes IATA stricts** : Kayak rejette codes non valides (3 lettres uppercase uniquement)
- **Format dates ISO** : `YYYY-MM-DD` obligatoire dans le path URL
- **Multi-city 8 segments max** : Kayak limite à 8 segments par recherche
- **Popup RGPD variable** : Peut apparaître ou non selon état cookies navigateur
- **Timeout consent 5s** : Popup doit être détecté rapidement pour ne pas ralentir scraping

## Valeur business

- ✅ **Foundation Epic 4** : Première story, bloque toutes les suivantes (dépendance critique)
- ✅ **Validation précoce** : Évite crawls inutiles avec URLs invalides (économie bandwidth Decodo)
- ✅ **Dérisquage RGPD** : Gestion consent dès Story 4.1 = pas de surprise en intégration
- ✅ **URL lisibles** : Format Kayak simple `/PAR-TYO/date` (vs Google base64) = debug facile
- ✅ **Testabilité** : Composants purs (pas d'async ni dépendances externes) = TDD simple

## Métriques succès

- **Temps construction URL** : <1ms pour URLs 8 segments (fonction pure)
- **Taux validation IATA** : 100% codes valides acceptés, 100% codes invalides rejetés
- **Timeout consent** : 5s max pour détection popup (non bloquant si absent)
- **Coverage tests** : ≥95% (composants critiques pour Epic 4)
- **Taux erreur 404 Kayak** : 0% après validation (mesuré en Story 4.2)

---

# 📋 Spécifications Techniques

## 1. KayakSegment (Dataclass)

**Rôle** : Représente un segment de vol avec validation IATA stricte

**Interface** :
```python
class KayakSegment:
    """Segment de vol Kayak avec validation IATA."""

    origin: str
    destination: str
    date: str
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `origin` | `str` | Code IATA aéroport départ | 3 lettres, uppercase (ex: `PAR`) |
| `destination` | `str` | Code IATA aéroport arrivée | 3 lettres, uppercase (ex: `TYO`) |
| `date` | `str` | Date vol au format ISO | `YYYY-MM-DD` (ex: `2026-01-14`) |

**Comportement** :

- **Dataclass ou Pydantic BaseModel** : Implémenté avec `@dataclass` ou Pydantic BaseModel selon choix design
- Valide format IATA à la construction (3 lettres uppercase)
- Rejette codes mixedcase (`Par`) ou trop longs (`PARIS`)
- Valide format date ISO-8601 (pattern `^\d{4}-\d{2}-\d{2}$`)
- Lève `ValidationError` si contraintes non respectées

**Validations Pydantic** :

```python
@field_validator("origin", "destination")
@classmethod
def validate_iata_code(cls, v: str) -> str:
    """Valide code IATA 3 lettres uppercase."""

@field_validator("date")
@classmethod
def validate_date_format(cls, v: str) -> str:
    """Valide format date YYYY-MM-DD."""
```

**Erreurs levées** :

- `ValidationError` si origin/destination non conformes (longueur ≠ 3, lowercase)
- `ValidationError` si date non ISO format

---

## 2. KayakUrlBuilder

**Rôle** : Construit URLs Kayak valides à partir de segments validés

**Interface** :
```python
class KayakUrlBuilder:
    """Constructeur d'URLs Kayak multi-city."""

    def __init__(self, base_url: str = "https://www.kayak.fr") -> None:
        """Initialise builder avec URL de base."""

    def build_url(self, segments: list[KayakSegment]) -> str:
        """Construit URL Kayak complète depuis segments."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `base_url` | `str` | URL de base Kayak | Default `"https://www.kayak.fr"` |
| `segments` | `list[KayakSegment]` | Liste segments validés | 1 ≤ len ≤ 8 |

**Comportement** :

- Concatène segments au format `/origin-destination/date/origin-destination/date/...`
- Ajoute query param `?sort=bestflight_a` (tri par pertinence Kayak)
- Rejette listes vides (`len(segments) == 0`)
- Rejette listes >8 segments (limite Kayak)
- Retourne URL complète prête à crawler

**Exemples sorties** :

```python
# 1 segment (aller simple)
"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"

# 2 segments (aller-retour)
"https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"

# 3 segments (multi-city)
"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"
```

**Erreurs levées** :

- `ValueError` si `len(segments) == 0`
- `ValueError` si `len(segments) > 8`

---

## 3. ConsentHandler

**Rôle** : Détecte et ferme le popup de consentement cookies Kayak

**Interface** :
```python
from playwright.async_api import Page

class ConsentHandler:
    """Gère le popup de consentement cookies Kayak."""

    def __init__(self, consent_selectors: list[str]) -> None:
        """Initialise handler avec sélecteurs popup."""

    async def handle_consent(self, page: Page) -> None:
        """Détecte et ferme popup consent si présent."""
```

**Champs/Paramètres** :

| Champ | Type | Description | Contraintes |
|-------|------|-------------|-------------|
| `consent_selectors` | `list[str]` | Sélecteurs CSS bouton consent | Ex: `["button[id*='accept']"]` |
| `page` | `Page` | Page Playwright active | Instance Playwright Page |

**Comportement** :

- Itère sur sélecteurs fournis dans l'ordre
- Attend popup max 5s (`timeout=5000`)
- Si popup détecté : click + sleep 1s (laisser popup se fermer)
- Si timeout : passe à sélecteur suivant
- Si aucun sélecteur trouve popup : retourne silencieusement (non bloquant)

**Sélecteurs recommandés** :

| Priorité | Sélecteur CSS | Description |
|----------|---------------|-------------|
| 1 | `button[id*='accept']` | Bouton avec ID contenant "accept" |
| 2 | `button[class*='consent']` | Bouton avec classe contenant "consent" |
| 3 | `div[class*='cookie'] button` | Bouton dans div cookie générique |

**Erreurs levées** :

- Aucune (méthode non bloquante, timeout géré en interne)

---

# 🧪 Tests

## Tests unitaires (TDD)

**Format recommandé : AAA (Arrange/Act/Assert)**

### KayakSegment (8 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_segment_valid` | Segment valide avec codes uppercase | `origin="PAR"`, `destination="TYO"`, `date="2026-01-14"` | `segment.origin == "PAR"` | Vérifie création segment nominal |
| 2 | `test_segment_invalid_origin_lowercase` | Code origine lowercase | `origin="par"`, `destination="TYO"`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie validation IATA stricte |
| 3 | `test_segment_invalid_origin_length` | Code origine trop long | `origin="PARIS"`, `destination="TYO"`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie longueur 3 lettres |
| 4 | `test_segment_invalid_destination_empty` | Code destination vide | `origin="PAR"`, `destination=""`, `date="2026-01-14"` | Lève `ValidationError` | Vérifie non-empty destination |
| 5 | `test_segment_invalid_date_format` | Date non ISO | `origin="PAR"`, `destination="TYO"`, `date="14/01/2026"` | Lève `ValidationError` | Vérifie format YYYY-MM-DD |
| 6 | `test_segment_invalid_date_partial` | Date incomplète | `origin="PAR"`, `destination="TYO"`, `date="2026-01"` | Lève `ValidationError` | Vérifie date complète |
| 7 | `test_segment_valid_mixedcase_normalized` | Codes mixedcase normalisés uppercase | `origin="Par"`, `destination="tyo"`, `date="2026-01-14"` | `segment.origin == "PAR"` ou Lève `ValidationError` | Vérifie normalisation ou rejet strict (décision design) |
| 8 | `test_segment_valid_future_date` | Date future lointaine | `origin="PAR"`, `destination="TYO"`, `date="2030-12-31"` | `segment.date == "2030-12-31"` | Vérifie pas de limite date future |

### KayakUrlBuilder (10 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_build_url_single_segment` | URL aller simple | `[KayakSegment("PAR", "SLZ", "2026-01-14")]` | `"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"` | Vérifie format URL 1 segment |
| 2 | `test_build_url_two_segments` | URL aller-retour | `[segment1, segment2]` avec dates différentes | `"https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"` | Vérifie format URL 2 segments |
| 3 | `test_build_url_three_segments_multicity` | URL multi-city 3 segments | `[segment1, segment2, segment3]` | `"https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"` | Vérifie format URL multi-city |
| 4 | `test_build_url_eight_segments_max` | URL 8 segments (limite max) | Liste 8 segments | URL valide avec 8 segments concaténés | Vérifie limite supérieure Kayak |
| 5 | `test_build_url_empty_segments` | Liste segments vide | `[]` | Lève `ValueError` | Vérifie validation liste non vide |
| 6 | `test_build_url_nine_segments_exceeds_limit` | Liste >8 segments | Liste 9 segments | Lève `ValueError` | Vérifie limite max 8 segments |
| 7 | `test_build_url_custom_base_url` | Base URL personnalisée | `base_url="https://www.kayak.com"`, 1 segment | URL commence par `"https://www.kayak.com/flights/..."` | Vérifie flexibilité domaine |
| 8 | `test_build_url_sort_param_present` | Query param sort présent | 1 segment | URL finit par `"?sort=bestflight_a"` | Vérifie ajout tri automatique |
| 9 | `test_build_url_segment_separator` | Séparateurs corrects | 2 segments | URL contient `-` entre codes et `/` entre segments | Vérifie séparateurs conformes |
| 10 | `test_build_url_no_trailing_slash` | Pas de slash final | 1 segment | URL ne finit pas par `/` (avant `?sort`) | Vérifie format propre |

### ConsentHandler (6 tests)

| # | Nom test | Scénario | Input | Output attendu | Vérification |
|---|----------|----------|-------|----------------|--------------|
| 1 | `test_handle_consent_popup_found` | Popup présent et cliqué | Mock page avec `wait_for_selector` retournant mock button | Appel `button.click()` effectué | Vérifie détection + click |
| 2 | `test_handle_consent_popup_not_found` | Popup absent (timeout) | Mock page avec `wait_for_selector` levant `TimeoutError` | Méthode retourne sans erreur | Vérifie non-bloquant si pas popup |
| 3 | `test_handle_consent_multiple_selectors_first_match` | Plusieurs sélecteurs, premier matche | Mock page avec premier sélecteur trouvé | Click sur premier sélecteur uniquement | Vérifie ordre sélecteurs |
| 4 | `test_handle_consent_multiple_selectors_second_match` | Plusieurs sélecteurs, deuxième matche | Mock page avec premier timeout, deuxième trouvé | Click sur deuxième sélecteur | Vérifie fallback sélecteurs |
| 5 | `test_handle_consent_timeout_5s` | Timeout configuré 5s | Mock page avec `wait_for_selector(timeout=5000)` | Timeout passé à Playwright = 5000ms | Vérifie timeout non bloquant |
| 6 | `test_handle_consent_sleep_after_click` | Sleep 1s après click | Mock page avec button trouvé | `asyncio.sleep(1)` appelé après `click()` | Vérifie attente fermeture popup |

**Total tests unitaires** : 8 + 10 + 6 = **24 tests**

---

## Tests intégration

**Format recommandé : Given/When/Then (BDD)**

| # | Nom test | Prérequis (Given) | Action (When) | Résultat attendu (Then) |
|---|----------|-------------------|---------------|-------------------------|
| 1 | `test_integration_url_builder_with_valid_segments` | 3 segments KayakSegment valides | Appel `builder.build_url(segments)` | URL Kayak complète retournée, format conforme |
| 2 | `test_integration_consent_handler_with_mock_page` | Mock Playwright Page, ConsentHandler initialisé | Appel `handler.handle_consent(page)` | Méthode retourne sans erreur, popup mocké cliqué |

**Total tests intégration** : **2 tests**

---

## Exemples JSON

**Exemple 1 : KayakSegment valide** :
```json
{
  "origin": "PAR",
  "destination": "TYO",
  "date": "2026-03-15"
}
```

**Exemple 2 : Liste segments multi-city** :
```json
[
  {
    "origin": "PAR",
    "destination": "SLZ",
    "date": "2026-01-14"
  },
  {
    "origin": "SLZ",
    "destination": "LIM",
    "date": "2026-03-28"
  },
  {
    "origin": "LIM",
    "destination": "PAR",
    "date": "2026-04-10"
  }
]
```

**Exemple 3 : URL Kayak construite** :
```json
{
  "url": "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a",
  "segments_count": 3,
  "base_url": "https://www.kayak.fr"
}
```

**Exemple 4 : Validation error (code IATA invalide)** :
```json
{
  "error": "ValidationError",
  "detail": [
    {
      "loc": ["origin"],
      "msg": "Code IATA must be 3 uppercase letters",
      "input": "paris"
    }
  ]
}
```

---

# ✅ Critères d'acceptation

## Critères fonctionnels

1. **Validation IATA stricte** : KayakSegment rejette codes non conformes (longueur ≠ 3, lowercase, vide)
2. **Validation dates ISO** : KayakSegment rejette dates non ISO-8601 (`DD/MM/YYYY`, dates partielles)
3. **Construction URL 1 segment** : `builder.build_url([segment])` retourne URL aller simple valide
4. **Construction URL multi-city** : `builder.build_url([s1, s2, s3])` retourne URL multi-city avec segments concaténés
5. **Limite 8 segments** : `builder.build_url([s1...s9])` lève `ValueError`
6. **Query param sort** : Toutes URLs finissent par `?sort=bestflight_a`
7. **Détection popup consent** : `handler.handle_consent(page)` détecte et clique popup si présent
8. **Timeout consent 5s** : `wait_for_selector(timeout=5000)` utilisé pour ne pas bloquer
9. **Fallback sélecteurs** : Si premier sélecteur timeout, tente suivants dans liste
10. **Non-bloquant si pas popup** : Méthode retourne sans erreur si aucun sélecteur matche

## Critères techniques

11. **Type safety strict** : Utiliser Literal types pour `base_url`, annotations complètes PEP 695
12. **Pydantic validators** : `@field_validator` pour validation IATA et dates
13. **Fonction pure builder** : Pas d'effets de bord, déterministe (mêmes inputs → même output)
14. **Async handler** : ConsentHandler utilise `async def` pour Playwright
15. **Mock Playwright** : Tests unitaires ConsentHandler avec `AsyncMock` pour Page
16. **Dataclass ou Pydantic** : KayakSegment implémenté avec Pydantic BaseModel pour validations
17. **Pas de dépendance DB/API** : Composants purs (seulement Playwright pour ConsentHandler)

## Critères qualité

18. **Coverage ≥95%** : Tests unitaires couvrent tous chemins (nominal + edge cases)
19. **24 tests unitaires + 2 intégration** : Tous verts avant merge
20. **Ruff + Mypy** : Code conforme standards projet (PEP 8, type hints)
21. **Docstrings 1 ligne** : Toutes classes/méthodes publiques documentées
22. **Pas de commentaires inline** : Code self-explanatory (sauf justification explicite)
23. **Fixtures réutilisables** : Fixtures `kayak_segment_factory`, `mock_playwright_page` dans `conftest.py`

## Critères production

24. **Logs structurés** : Logger détection popup consent (`extra={"popup_found": bool}`)
25. **Timeout configurables** : `consent_timeout` paramétrable via Settings (Phase 5)
26. **Error handling consent** : Pas d'exception propagée si popup non trouvé (non critique)

---

**💡 Note** : Cette story contient **26 critères** pour 5 story points (story complexité moyenne avec composants critiques pour Epic 4).

**Principe SMART** : Tous critères vérifiables via tests automatisés (pas de validation manuelle nécessaire).
