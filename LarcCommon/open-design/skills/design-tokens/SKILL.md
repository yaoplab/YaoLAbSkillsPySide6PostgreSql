---
skill: design-tokens
version: "1.0"
priority: P0
category: design
depends_on: []
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [A, B, C, E, G, R14, R17]
---

# Skill: Design Tokens

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Design, Hub)
**Module** : `LarcCommon/larccommon/design_system.py`
**Utilisateurs** : Tous les développeurs Larc
**Dépendances** : `PySide6>=6.5`

Ce skill est la **fondation** de tout le design system. Tous les autres skills design en dépendent.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Valeur numérique en pixels (4, 8, 12, 16, 20, 32, 52...)
**Sortie** : Token `ds.space_*`, `ds.radius_*`, `s(*)` ou `theme_manager.image.*` correspondant
**Traitement** : Remplacer toute valeur littérale par le token unique correct

## 2. Contraintes Fondamentales

### Sous-système A — Espacements (Fibonacci ×4 + M3 ×8)

**Principe** : Grille hybride. Fibonacci ×4 pour la hiérarchie visuelle. M3 ×8 pour les standards. Compatibles car 4 et 8 sont sur la même grille de base 4px.

| Token | px | Système | Usage |
|---|---|---|---|
| `ds.space_xxs` | 4 | Fibo | Gap icône-texte, inner padding |
| `ds.space_xs` | 8 | Fibo ∩ M3 | Gap standard entre composants |
| `ds.space_sm` | 12 | Fibo | Espacement entre sections proches |
| `ds.space_m3` | 16 | M3 | Card padding, dialog padding, champ padding |
| `ds.space_md` | 20 | Fibo | Espacement de section moyen |
| `ds.space_lg` | 32 | Fibo ∩ M3 | Marges de page, padding zone |
| `ds.space_xl` | 52 | Fibo | Hauteur bouton, header |
| `ds.space_xxl` | 84 | Fibo | Marges de page larges |
| `ds.space_xxxl` | 136 | Fibo | Hero sections |

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `setSpacing(6)` — 6px n'appartient à AUCUN système | `setSpacing(ds.space_xs)` (8px M3) ou `setSpacing(ds.space_sm)` (12px Fibo) |
| `setContentsMargins(10,10,10,10)` | `setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)` |

### Sous-système B — Hauteurs et Largeurs

| Token | px | Usage |
|---|---|---|
| `ds.field_height` | 32 | Champs de saisie (QLineEdit, M3TextField) |
| `ds.button_height` | 52 | Boutons et en-têtes |
| `ds.header_height` | 52 | Barres d'en-tête |
| `ds.table_row_min` | 21 | Lignes de tableau (font_size(13) × φ ≈ 21) |
| `ds.sidebar_width` | 233 | Largeur de la barre latérale |

**⚠️** `ds.field_height` = 32px pour les CHAMPS. Ne PAS utiliser pour une hauteur de bouton (52px = `ds.button_height`).

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `setFixedHeight(52)` | `setFixedHeight(ds.button_height)` |
| `setFixedWidth(233)` | `setFixedWidth(ds.sidebar_width)` |

### Sous-système C — Bordures (Shapes M3)

| Token | px | Composant |
|---|---|---|
| `ds.radius_none` | 0 | DataTable, ListItem |
| `ds.radius_xs` | 4 | TextField, SearchBar |
| `ds.radius_sm` | 8 | Card (Elevated/Filled/Outlined) |
| `ds.radius_md` | 12 | Dialog, BottomSheet, NavigationDrawer |
| `ds.radius_lg` | 16 | Filled Button, Tonal Button |
| `ds.radius_xl` | 28 | FAB, Chip, BottomNavigation |

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `border-radius: 6px` | `border-radius: {ds.radius_sm}px` |
| `border-radius: 20px` sur un bouton | `border-radius: {ds.radius_lg}px` (16px standard Larc) |

### Sous-système E — Icônes

```python
from larccommon.icons import icon as md3_icon
md3_icon('refresh', color=ds.p.primary, size=theme_manager.image.icon_btn)
```

| Token | px | Usage |
|---|---|---|
| `theme_manager.image.icon_btn` | 18 | Icônes dans les boutons |
| `theme_manager.image.icon_menu` | 18 | Icônes dans les menus |
| `ds.icon_sm` | 20 | Petite icône |
| `ds.icon_md` | 32 | Icône moyenne (items de liste) |
| `theme_manager.image.icon_large` | 32 | Grande icône |
| `theme_manager.image.theme_btn` | 34 | Boutons de thème |
| `theme_manager.image.profile_btn` | 34 | Avatar |
| `ds.icon_lg` | 52 | Grande icône (headers, cards) |
| `theme_manager.image.avatar` | 150 | Photo profil |
| `theme_manager.image.photo` | 150 | Photo élève |
| `theme_manager.image.logo` | 89 | Logo sidebar |
| `theme_manager.image.logo_small` | 55 | Logo réduit |

**RÈGLE** : Icônes SVG Material Design 3 UNIQUEMENT. INTERDICTION des PNG/JPG comme icônes.

### Sous-système G — Typographie M3

```python
s = theme_manager.font_size  # Prend en compte le multiplicateur du thème actif
```

| Token M3 | Taille | Usage |
|---|---|---|
| `s(11)` | label-small | Badges, timestamps, metadata |
| `s(12)` | body-small | Légendes, hints, infobulles |
| `s(13)` | label-large | **BOUTONS**, items de liste |
| `s(14)` | body-medium | **TEXTE STANDARD**, labels |
| `s(16)` | title-medium | Titres de section, cards |
| `s(18)` | title-large | Titres de page |
| `s(22)` | headline-small | Héros, page d'accueil |
| `s(28)` | headline-medium | KPIs, chiffres clés |
| `s(36)` | headline-large | Très grands chiffres |
| `s(45)` | display-small | Compteurs géants |
| `s(57)` | display-large | Hero (rare) |

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `font-size: 20px` | `font-size: {s(14)}px` |
| `font-size: 14px; font-weight: bold` | `font-size: {s(16)}px; font-weight: bold` (title-medium pour titres) |

### Sous-système R14 — Table de Mapping Valeurs → Tokens

Table canonique pour `--fix` automatique et référence développeur :

| px | Spacing | Shape | Image | Police |
|---|---|---|---|---|
| 4 | `ds.space_xxs` | `ds.radius_xs` | — | — |
| 6 | ❌ INTERDIT | ❌ INTERDIT | — | — |
| 8 | `ds.space_xs` | `ds.radius_sm` | — | — |
| 10 | — | — | — | `s(10)` |
| 11 | — | — | — | `s(11)` |
| 12 | `ds.space_sm` | `ds.radius_md` | — | `s(12)` |
| 13 | — | — | — | `s(13)` |
| 14 | — | — | — | `s(14)` |
| 16 | `ds.space_m3` | `ds.radius_lg` | — | — |
| 18 | — | — | `tm.image.icon_btn` | `s(18)` |
| 20 | `ds.space_md` | — | — | — |
| 21 | — | — | — | `s(21)` / `ds.table_row_min` |
| 24 | — | — | — | `s(24)` |
| 28 | — | `ds.radius_xl` | — | `s(28)` |
| 32 | `ds.space_lg` | — | `tm.image.icon_large` | `s(32)` |
| 34 | — | — | `tm.image.theme_btn` | — |
| 40 | — | — | Hauteur bouton M3 | — |
| 52 | `ds.space_xl` | — | `ds.button_height` | — |
| 55 | — | — | `tm.image.logo_small` | — |
| 84 | `ds.space_xxl` | — | — | — |
| 89 | — | — | `tm.image.logo` | — |
| 100 | — | — | `tm.image.add_btn` | — |
| 136 | `ds.space_xxxl` | — | — | — |
| 150 | — | — | `tm.image.avatar` | — |
| 233 | — | — | `ds.sidebar_width` | — |

> `tm` = `theme_manager` dans le code.

### Sous-système R17 — Tokens phibuilder

**Principe** : `phibuilder` est autonome — il n'importe **JAMAIS** `ds`. Il utilise ses propres tokens.

**SpacingToken** (IntEnum, base 4) :

| Token | px | | Token | px |
|---|---|---|---|---|
| `XXS` | 4 | | `XL` | 52 |
| `XS` | 8 | | `XXL` | 84 |
| `SM` | 12 | | `XXXL` | 136 |
| `MD` | 20 | | `HUGE` | 220 |
| `LG` | 32 | | `GIANT` | 356 |
| — | — | | `COLOSSAL` | 576 |

**Typographie** (`theme.typo.<nom>.size`) : `label_small`=11, `label_medium`=12, `body_small`=12, `label_large`=14, `body_medium`=14, `title_small`=14, `body_large`=16, `title_medium`=16, `title_large`=22, `headline_small`=24

**Pattern obligatoire dans phibuilder/widgets** :

```python
from phibuilder.phi.scale import PhiScale, SpacingToken

_SCALE = PhiScale()  # tailles indépendantes du thème

class M3MonWidget(QWidget):
    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(_SCALE.spacing(SpacingToken.MD) * 2)  # 40px
        if theme is None:
            return
        c, s, t = theme.colors, theme.spacing, theme.typo
        self.setStyleSheet(
            f"M3MonWidget {{ background: {c.surface_variant}; "
            f"padding: {s.spacing(SpacingToken.XS)}px; "
            f"border-radius: {s.spacing(SpacingToken.SM)}px; "
            f"font-size: {t.label_medium.size}px; }}"
        )
```

**Règles R17** :

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| R17a | `setMinimumHeight(40)` | `self.setMinimumHeight(_SCALE.spacing(SpacingToken.MD) * 2)` |
| R17b | `padding: 8px` dans QSS | `padding: {s.spacing(SpacingToken.XS)}px` |
| R17c | `font-size: 12px` | `font-size: {t.label_medium.size}px` |
| R17d | `setFixedWidth(280)` | `setFixedWidth(_SCALE.spacing(SpacingToken.XXXL) * 2 + _SCALE.spacing(SpacingToken.XS))` |

## 3. Code complet

```python
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon

class MonWidget(QWidget):
    def __init__(self):
        super().__init__()
        s = theme_manager.font_size
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_sm)

        field = QLineEdit()
        field.setFixedHeight(ds.field_height)  # 32px — champs
        field.setStyleSheet(ds.flat_input_qss())

        btn = M3Button("OK")
        btn.setFixedHeight(ds.button_height)   # 52px — boutons

        self.setStyleSheet(f"""
            QWidget#panel {{
                background: {ds.p.surface};
                border: {ds.border_width}px solid {ds.p.outline_variant};
                border-radius: {ds.radius_sm}px;
                padding: {ds.space_m3}px;
            }}
        """)
```

## 4. Exemples

### Exemple 1 — Correction LarcProf (pire cas)

```python
# ❌ AVANT
layout.setContentsMargins(6, 6, 6, 6)
layout.setSpacing(6)
field.setFixedHeight(32)
field.setStyleSheet("border: 1px solid #BDBDBD; border-radius: 4px; padding: 8px;")

# ✅ APRÈS
layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
layout.setSpacing(ds.space_xs)
field.setFixedHeight(ds.field_height)
field.setStyleSheet(ds.flat_input_qss())
```

### Exemple 2 — Correction LarcSuperviseur

```python
# ❌ AVANT
self._sidebar.setFixedWidth(233)
sidebar_layout.setContentsMargins(6, 6, 6, 6)

# ✅ APRÈS
self._sidebar.setFixedWidth(ds.sidebar_width)
sidebar_layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
```

### Exemple 3 — Police de bouton

```python
# ❌ AVANT
btn.setStyleSheet("font-size: 13px; font-weight: bold;")

# ✅ APRÈS
btn.setStyleSheet(f"font-size: {theme_manager.font_size(13)}px; font-weight: bold;")
```

## 5. Step by Step — Audit d'un fichier

| Ordre | Action | Résultat |
|---|---|---|
| 1 | Scanner les `setContentsMargins`, `setSpacing`, `setFixedHeight/Width` | Liste des hardcodings |
| 2 | Pour chaque valeur, chercher dans la table R14 | Token correspondant |
| 3 | Remplacer par le token | 0 hardcoded |
| 4 | Lancer `lint_qss_hardcoding.py --dir .\MonProjet` | Vérification automatique |
| 5 | Corriger les erreurs restantes | Conforme |

## 6. Checklist

- [ ] `ds` importé dans tous les fichiers de vues
- [ ] 0 `setContentsMargins(a,b,c,d)` avec valeurs > 0 littérales
- [ ] 0 `setSpacing(n)` avec n ∉ {0} et n ∉ {ds.space_*}
- [ ] 0 `setFixedWidth(n)` ou `setFixedHeight(n)` avec n littéral
- [ ] 0 `border-radius: Npx` en dur (utiliser `ds.radius_*`)
- [ ] 0 `font-size: Npx` en dur (utiliser `s(N)`)
- [ ] 0 image PNG/JPG comme icône (utiliser `md3_icon()`)
- [ ] `python scripts/lint_qss_hardcoding.py --dir .\MonProjet` retourne 0 violations
- [ ] Chaque valeur de la table R14 est comprise

## Références croisées

- **[color-rules](../color-rules/SKILL.md)** — Palette de couleurs et règle D1 (couleur explicite)
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — Règles R1-R16 et anti-patterns visuels
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + _restyle_all
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — Spécification visuelle du sidebar (utilise ces tokens)
