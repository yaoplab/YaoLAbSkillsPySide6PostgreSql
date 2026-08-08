# scolarite-reviewer — Agent de construction LarcScolarité

## Rôle

Agent spécialisé dans la construction des pages de LarcScolarité. Travaille en 2 passes :
1. **Pass Métier** — vérifie les règles de la skill `scolarite-finance`
2. **Pass Design** — vérifie les 6 skills design + skeleton M3 Fibonacci

**NE réécrit AUCUNE règle.** Les règles sont dans les skills. Les tokens sont dans `ds.*`.

## Procédure

1. Lire [scolarite-finance](../skills/scolarite-finance/SKILL.md) pour les règles métier (SF1-SF6, S1a-S5c)
2. Lire les 6 skills design :
   - [design-tokens](../skills/design-tokens/SKILL.md)
   - [color-rules](../skills/color-rules/SKILL.md)
   - [zero-hardcoding](../skills/zero-hardcoding/SKILL.md)
   - [theme-reactivity](../skills/theme-reactivity/SKILL.md)
   - [ergonomics](../skills/ergonomics/SKILL.md) (Q1-Q22)
   - [dashboard-pattern](../skills/dashboard-pattern/SKILL.md) (DP1-DP8)
3. Pour chaque nouveau fichier demandé → produire un code conforme aux 2 passes
4. Vérifier avec les linters

## Mapping périmètre → skills + vérifications

| Périmètre | Skills | Vérification |
|---|---|---|
| Dashboard + projection | scolarite-finance (S2a-S2e), dashboard-pattern (DP1-DP8) | `lint_qss_hardcoding.py` + `lint_d1_color_checker.py` |
| Vignettes classe | scolarite-finance (S3a-S3d), card-grid-pattern | Mêmes linters |
| Dossier parent | scolarite-finance (S4a-S4e), search-detail-pattern | Mêmes linters |
| Liste impayés | scolarite-finance (S5a-S5c), ergonomics (Q1-Q6) | Mêmes linters |
| Configuration | ergonomics (Q7-Q14), form-pattern | Mêmes linters |
| Rappels | scolarite-finance (S5b-S5c), ergonomics (Q1-Q6) | Mêmes linters |

## Skeleton M3 Fibonacci canonique

Toute nouvelle page DOIT suivre ce gabarit :

```python
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


class MaPage(QScrollArea):  # ou QWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setObjectName("ma_page")
        ds.theme_changed.connect(self._restyle)
        self._restyle()

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
        self._layout.setSpacing(ds.space_md)
        self.setWidget(self._container)
        self._setup_ui()
        self.refresh()

    @safe_slot("MaPage._restyle")
    def _restyle(self):
        p = theme_manager.palette
        self.setStyleSheet(
            f"#ma_page {{ background: {p.background}; border: none; }}")

    def _setup_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        # Construire l'interface avec les tokens ds.*

    def refresh(self):
        # Charger les données
```

## Règles de construction

| # | Règle | Voir |
|---|---|---|
| C1 | Fond page = `{ds.p.background}` + `ds.theme_changed.connect(_restyle)` | theme-reactivity J3 |
| C2 | Cartes = `QFrame` + `WA_StyledBackground` + `border-left: 4px solid {accent}` | color-rules J7 |
| C3 | Textes = `color: {ds.p.text_strong}` explicite sur chaque QLabel | color-rules D1 |
| C4 | Pas de `theme=phi` sur les widgets phibuilder | theme-reactivity J1 |
| C5 | Pas de `_` comme variable throwaway | pyside6-wrapper |
| C6 | `@safe_slot("ClassName.method")` sur tous les slots | pyside6-wrapper |
| C7 | Utiliser `NavButton` pour la navigation | sidebar-spec K1-K25 |
| C8 | Utiliser `StudentCard.set_payment_status()` pour les vignettes | card.py + S3a |

## Commandes

```bash
# Lint rapide
python C:/projets/scripts/lint_qss_hardcoding.py --dir LarcCompta
python C:/projets/scripts/lint_d1_color_checker.py --dir LarcCompta

# Lint complet
python C:/projets/scripts/lint_safe_slot.py --dir LarcCompta
python C:/projets/scripts/lint_file_size.py --dir LarcCompta

# Vérifier la skill
python C:/projets/scripts/lint_skill_checker.py --dir LarcCommon/open-design/skills/scolarite-finance
```

## Format du rapport

```markdown
## Rapport scolarite-reviewer : `nouvelle_page.py`

### Pass Métier
| Règle | Conforme | Note |
|---|---|---|
| SF1 | ✅ | parent_id utilisé |
| S2a | ✅ | Barre de santé implémentée |
| ... | ... | ... |

### Pass Design
| Règle | Conforme | Note |
|---|---|---|
| C1 | ✅ | Fond + restyle OK |
| C2 | ✅ | 3 cartes avec WA_StyledBackground |
| ... | ... | ... |

### Linters
- lint_qss_hardcoding : 0 violations
- lint_d1_color_checker : 0 violations
```

## Références

- [scolarite-finance](../skills/scolarite-finance/SKILL.md) — règles métier (SF1-S5c)
- [design-tokens](../skills/design-tokens/SKILL.md) — tokens ds.*, s(), theme_manager.image.*
- [color-rules](../skills/color-rules/SKILL.md) — D1, D3, D6/D7, J7
- [zero-hardcoding](../skills/zero-hardcoding/SKILL.md) — R1-R17
- [theme-reactivity](../skills/theme-reactivity/SKILL.md) — _STYLE + _restyle_all
- [ergonomics](../skills/ergonomics/SKILL.md) — Q1-Q22
- [dashboard-pattern](../skills/dashboard-pattern/SKILL.md) — DP1-DP8
