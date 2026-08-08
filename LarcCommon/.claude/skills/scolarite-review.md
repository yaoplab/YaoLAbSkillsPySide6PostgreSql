---
name: scolarite-review
description: Construction des pages LarcScolarité — règles métier + design system M3 Fibonacci
category: build
trigger: construit LarcScolarité, crée page compta, vérifie scolarité, audit compta, build dashboard scolarité
---

# Scolarité Review — Construction LarcScolarité

Agent spécialisé pour construire les pages de LarcScolarité. Vérifie les règles métier (scolarite-finance) et les 6 skills design avec le skeleton M3 Fibonacci.

## Procédure

1. Lire la skill métier :
```bash
cat LarcCommon/open-design/skills/scolarite-finance/SKILL.md
```

2. Construire la page avec le skeleton M3 :
```python
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot

class MaPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setObjectName("ma_page")
        ds.theme_changed.connect(self._restyle)
        self._restyle()
        # ...
```

3. Vérifier les règles :
   - SF1-SF6 : modèle de données
   - S1a-S1g : calcul du statut
   - S2a-S2e : dashboard & projection
   - S3a-S3d : vignettes élèves
   - S4a-S4e : dossier parent
   - S5a-S5c : recouvrement

4. Lancer les linters :
```bash
python C:/projets/scripts/lint_qss_hardcoding.py --dir LarcCompta
python C:/projets/scripts/lint_d1_color_checker.py --dir LarcCompta
```

## Règles absolues
- **Zéro hardcoding** — tout passe par ds.*, s(), theme_manager.image.*
- **Zéro hex** — ds.p.* pour toutes les couleurs
- **WA_StyledBackground** sur tout QFrame avec background QSS
- **@safe_slot** sur tous les handlers
- **theme_changed.connect** sur toute classe avec QSS palette

## Skills de référence
- scolarite-finance, design-tokens, color-rules, zero-hardcoding
- theme-reactivity, ergonomics, dashboard-pattern, card-grid-pattern
