---
tags:
  - skill
  - pyside6-wrapper
  - fonction
  - systeme-ferme
---

# Fonction Principale

Type: **système-ferme**

**Entrée** : Slot Qt non protégé
**Sortie** : Slot protégé contre les crashes silencieux
**Traitement** : Appliquer `@safe_slot(label)` sur tous les slots Qt
