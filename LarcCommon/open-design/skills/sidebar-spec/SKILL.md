---
skill: sidebar-spec
version: "1.0"
priority: P1
category: design
depends_on: [design-tokens, color-rules, theme-reactivity]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcHub]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [K]
---

# Skill: Sidebar Specification

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Hub)
**Module** : `LarcCommon/larccommon/widgets/sidebar.py` (SidebarWidget), `LarcCommon/larccommon/theme.py` (QssHelper)
**Utilisateurs** : Développeurs modifiant le sidebar
**Dépendances** : `design-tokens`, `color-rules` (PROGRAM_STYLES), `theme-reactivity` (_STYLE pattern)

Ce skill garantit un **rendu identique** du sidebar dans toutes les apps Larc, quel que soit le thème actif.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Sidebar avec QSS inline, couleurs en dur, tailles arbitraires
**Sortie** : Sidebar utilisant exclusivement `QssHelper.sidebar_*()` et les tokens
**Traitement** : Appliquer les 25 règles K1-K25

## 2. Contraintes Fondamentales — Les 25 Règles K

### Structure

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K1 | **Conteneur** | `M3Frame()` ou `QWidget()` | `M3ScrollArea` avec `setWidgetResizable(True)` + `setFrameShape(M3Frame.NoFrame)` |
| K2 | **Largeur** | `setFixedWidth(233)` | `setFixedWidth(ds.sidebar_width)` |
| K3 | **Marges layout** | `setContentsMargins(8,8,8,8)` | `setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)` |
| K4 | **Spacing layout** | `setSpacing(6)` ou `setSpacing(ds.space_xxs)` | `setSpacing(theme_manager.design.spacing)` |
| K5 | **Fond sidebar** | Inline QSS avec `background:` | `QssHelper.sidebar_container(p)` dans `_STYLE()` |

### En-têtes de section

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K6 | **Style en-tête section** | `M3Button(text)` sans style | `btn.setObjectName("sidebar_sec_hdr")` + `QssHelper.sidebar_section_header(p,d,s)` dans `_STYLE()` |
| K7 | **Hauteur en-tête section** | `setFixedHeight(34)` | Hauteur automatique via padding QSS |
| K21 | **Hover en-tête section** | Aucun hover | `QPushButton#sidebar_sec_hdr:hover { color: {p.primary}; border-bottom: 2px solid {p.primary}; }` |

### En-têtes de programme

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K8 | **Style en-tête programme** | Fond `surface_variant` | `QssHelper.sidebar_program_header(p,d,s, fg, bg, on_fg)` — couleur PLEINE du programme |
| K9 | **Taille en-tête prog** | Pas de fixedSize | `setFixedSize(89, 21)` — 89px=`tm.image.logo`, 21px=`font_size(10)×φ` |
| K16 | **Police section** | `s(13)` ou défaut | `s(12)`px, bold |
| K17 | **Police programme** | `s(13)` ou défaut | `s(10)`px, bold |

### Boutons de classe

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K10 | **Style bouton classe** | `surface_variant` | `QssHelper.sidebar_class_button(p,d,s, bg, fg)` — fond CONTAINER programme |
| K11 | **Taille bouton classe** | Pas de fixedSize | `setFixedSize(89, 34)` — 89px=`tm.image.logo`, 34px=`tm.image.theme_btn` |
| K12 | **Checkable** | Pas de checkable | `btn.setCheckable(True)` |
| K18 | **Police classe** | `s(13)` ou défaut | `s(10)`px |
| K22 | **Hover classe** | `background: {p.primary_container}` | **Inversion fg↔bg** : `background: {fg}; color: {bg};` |
| K23 | **Checked classe** | Style différent ou absent | `background: {fg}; color: {bg}; border: 2px solid {fg};` |

### Bouton Toutes classes

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K13 | **Style Toutes classes** | Bouton TONAL ou absent | `QssHelper.sidebar_all_button(p,d,s)` — fond primaire |
| K14 | **Hauteur Toutes classes** | Pas de fixedHeight | `setFixedHeight(55)` — SpacingToken.HUGE |
| K19 | **Police Toutes classes** | `s(10)` ou défaut | `s(11)`px, bold |

### Couleurs et thème

| # | Règle | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| K15 | **Couleurs programme** | `surface_variant` pour tout | `PROGRAM_STYLES` avec les 4 rôles M3 |
| K20 | **Border-radius** | `sp(SpacingToken.XXS)` ou `ds.radius_xs` | `d.radius`px via `QssHelper` |
| K24 | **QSS inline** | `setStyleSheet(f"M3Button {{...}}")` | **Toujours** `QssHelper.sidebar_*()` |
| K25 | **Boutons icônes** (Dashboard, Recherche...) | M3Button(variant=TONAL) | M3Button(variant=TONAL) avec icône MD3 — ce sont des actions, pas des classes |

## 3. Code complet — Patron obligatoire

```python
from larccommon.design_system import ds
from larccommon.theme import theme_manager, QssHelper, PROGRAM_STYLES
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot
from larccommon.widgets.themed_widget import ThemedWidget
from phibuilder.widgets import M3Button, M3ScrollArea, M3Frame
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout

class Sidebar(M3ScrollArea):
    class_selected = Signal(int, str)
    all_selected = Signal()
    group_selected = Signal(str)

    COL_W = 89       # theme_manager.image.logo
    H_PROG = 34      # theme_manager.image.theme_btn
    H_CLASS = 34     # theme_manager.image.theme_btn
    H_ALL = 55       # SpacingToken.HUGE

    def __init__(self, sections, prog_style=None, parent=None):
        super().__init__(parent)
        self._sections = sections
        self._prog_style = prog_style or PROGRAM_STYLES
        self._classes = []
        self._selected_btn = None

        # K1: M3ScrollArea
        self._container = ThemedWidget(object_name="sidebar")
        self.setWidget(self._container)
        self.setWidgetResizable(True)
        self.setFrameShape(M3Frame.NoFrame)
        self.setFixedWidth(ds.sidebar_width)    # K2
        self.viewport().setStyleSheet("background: transparent;")

        # K3, K4
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
        self._layout.setSpacing(theme_manager.design.spacing)

        ds.theme_changed.connect(self._rebuild)

    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            {QssHelper.sidebar_container(p)}
            {QssHelper.sidebar_section_header(p, d, s)}
            {QssHelper.sidebar_program_header(p, d, s, p.primary, p.on_primary)}
            {QssHelper.sidebar_class_button(p, d, s, p.primary_container, p.primary)}
            {QssHelper.sidebar_all_button(p, d, s)}
        """

    def _resolve_colors(self, fg_role, bg_role, on_fg_role):
        p = theme_manager.palette
        return (getattr(p, fg_role), getattr(p, bg_role), getattr(p, on_fg_role))

    def _rebuild(self):
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size

        # K5: fond container
        self._container.setStyleSheet(
            f"background: {p.surface}; border: none; "
            f"border-right: 1px solid {p.outline_variant};"
        )

        # Nettoyage
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        for sec_name, columns in self._sections:
            # K6: en-tête section
            sec_hdr = M3Button(sec_name)
            sec_hdr.setObjectName("sidebar_sec_hdr")
            sec_hdr.setCursor(Qt.PointingHandCursor)
            sec_hdr.clicked.connect(lambda checked, sn=sec_name: self.group_selected.emit(sn))
            self._layout.addWidget(sec_hdr)

            grd = QGridLayout()
            grd.setSpacing(ds.space_xxs)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                if prog_key not in self._prog_style:
                    continue
                fg_role, bg_role, on_fg_role = self._prog_style[prog_key]
                fg, bg, on_fg = self._resolve_colors(fg_role, bg_role, on_fg_role)

                # K8, K9: en-tête programme
                col_hdr = M3Button(hdr_text)
                col_hdr.setObjectName("sidebar_prog_hdr")
                col_hdr.setFixedSize(self.COL_W, self.H_PROG)
                col_hdr.setCursor(Qt.PointingHandCursor)
                grd.addWidget(col_hdr, 0, col_idx)

                # K10, K11, K12: boutons de classe
                for i, (cid, label) in enumerate(self._get_classes(prog_key)):
                    btn = M3Button(label)
                    btn.setObjectName("sidebar_class_btn")
                    btn.setFixedSize(self.COL_W, self.H_CLASS)
                    btn.setCheckable(True)
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.clicked.connect(lambda checked, c=cid, l=label, b=btn: self._on_class(c, l, b))
                    grd.addWidget(btn, i + 1, col_idx)

            self._layout.addLayout(grd)
            self._layout.addSpacing(ds.space_xs)

        # K13, K14: Toutes classes
        self._all_btn = M3Button("Toutes les classes")
        self._all_btn.setObjectName("sidebar_all_btn")
        self._all_btn.setFixedHeight(self.H_ALL)
        self._all_btn.setCursor(Qt.PointingHandCursor)
        self._all_btn.clicked.connect(self.all_selected.emit)
        self._layout.addWidget(self._all_btn)
        self._layout.addStretch()

    @safe_slot("Sidebar.on_class")
    def _on_class(self, class_id, label, btn):
        if self._selected_btn:
            self._selected_btn.setChecked(False)
        btn.setChecked(True)
        self._selected_btn = btn
        self.class_selected.emit(class_id, label)
```

## 4. Exemples

### Sidebar complet (LarcSuperviseur)

```python
from larccommon.theme import PROGRAM_STYLES

SECTIONS = [
    ("Collège", [("PEI", "PEI"), ("MYP", "MYP")]),
    ("Lycée",  [("DPFr", "DPFr"), ("DPEn", "DPEn")]),
]

sidebar = Sidebar(SECTIONS, PROGRAM_STYLES)
sidebar.class_selected.connect(self._on_class)
sidebar.all_selected.connect(self._on_all)
sidebar.group_selected.connect(self._on_group)
```

## 5. Step by Step — Construction d'un sidebar

| Ordre | Action | Règle |
|---|---|---|
| 1 | Hériter de M3ScrollArea | K1 |
| 2 | setFixedWidth(ds.sidebar_width) | K2 |
| 3 | setContentsMargins(ds.space_sm, ...) | K3 |
| 4 | setSpacing(theme_manager.design.spacing) | K4 |
| 5 | Container avec QssHelper.sidebar_container(p) dans _STYLE() | K5 |
| 6 | Section headers: setObjectName("sidebar_sec_hdr") + QssHelper | K6, K7, K16, K21 |
| 7 | Program headers: setFixedSize(89, 21), couleur PLEINE via QssHelper | K8, K9, K17 |
| 8 | Class buttons: setFixedSize(89, 34), setCheckable(True), QssHelper | K10-K12, K18, K22, K23 |
| 9 | All button: setFixedHeight(55), QssHelper, primary | K13, K14, K19 |
| 10 | Utiliser PROGRAM_STYLES pour les couleurs | K15 |
| 11 | 0 setStyleSheet inline — tout via QssHelper | K24 |

## 6. Checklist

- [ ] Largeur = `ds.sidebar_width` (233px)
- [ ] Conteneur = `M3ScrollArea` avec `setObjectName("sidebar")`
- [ ] Sections : transparent + souligné 2px outline_variant, hover → primary
- [ ] Programmes : fond **couleur pleine** (primary/secondary/error/tertiary)
- [ ] Classes : fond **container** (primary_container/etc.)
- [ ] En-têtes programme : `setFixedSize(89, 21)`, police `s(10)` bold
- [ ] Boutons classe : `setFixedSize(89, 34)`, police `s(10)`, `setCheckable(True)`
- [ ] Border-radius : `d.radius`px via `QssHelper`
- [ ] Hover classes : inversion fg↔bg
- [ ] Checked : fond=fg, texte=bg, bordure 2px fg
- [ ] Toutes classes : fond primary, hauteur 55px
- [ ] 0 `setStyleSheet` inline — TOUT via `QssHelper.sidebar_*()`
- [ ] Le `_STYLE` property contient TOUS les `QssHelper.sidebar_*`

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.space_*, ds.sidebar_width, theme_manager.image.*
- **[color-rules](../color-rules/SKILL.md)** — PROGRAM_STYLES, résolution dynamique des couleurs
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + connexion theme_changed
