---
title: "Story 8: Filtres & Tri"
epic: "Epic 3: Production Ready"
story_points: 3
dependencies: ["epic-2/story-6"]
date: "2025-21-11"
keywords: ["filters", "sort", "max-price", "max-duration", "max-stops", "sort-by", "enum", "google-flights"]
scope: ["specs"]
technologies: ["Python", "Pydantic v2", "FastAPI", "Enum"]
---

# TODO - À compléter

## Résumé fonctionnel

Ajouter filtres et tri aux recherches de vols :

**Filtres (paramètres optionnels request)** :
- `max_price: float | None` - Prix max total itinéraire
- `max_duration_hours: int | None` - Durée max totale (heures)
- `max_stops: int | None` - Escales max par vol (0 = direct uniquement)

**Tri (enum SortBy)** :
- `price` - Prix total croissant
- `duration` - Durée totale croissante
- `stops` - Nombre escales croissant
- `score` - Score pondéré 70/20/10 (défaut actuel)

**Enums à créer** :
```python
class SortBy(str, Enum):
    PRICE = "price"
    DURATION = "duration"
    STOPS = "stops"
    SCORE = "score"  # défaut
```

**Note** : Pas d'enum pour filtres - ce sont des valeurs seuils numériques, pas des choix.

---

# À rédiger selon TEMPLATE_SPECS.md

- [ ] Contexte Business
- [ ] Spécifications Techniques
- [ ] Tests (unitaires + intégration)
- [ ] Exemples JSON
- [ ] Critères d'acceptation
