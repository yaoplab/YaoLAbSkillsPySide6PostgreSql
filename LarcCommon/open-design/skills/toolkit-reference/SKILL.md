---
skill: toolkit-reference
version: "1.0"
priority: P1
category: catalog
depends_on: [design-tokens]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcCommon]
linters: [lint_qss_hardcoding.py]
reviewers: []
subsystems: [A, B, C]
---

# Skill: Toolkit Reference — Widgets + Architecture

## 0. Contexte

**Projet** : LarcCommon
**Modules** : `phibuilder/` (toolkit UI), `larccommon/widgets/` (widgets métier), `larccommon/icons.py` (40 icônes MD3)
**Utilisateurs** : Développeurs cherchant le bon widget ou comprenant l'architecture du toolkit

Ce skill est la **référence unifiée** : catalogue des widgets + architecture du moteur de thème.

## 1. Fonction Principale — Architecture phibuilder

```
seed_color (#1565C0)
    │
    ▼
M3ColorScheme(hex_color, is_dark)  ← materialyoucolor
    │ .get_hex("primary"), .get_hex("surface")...
    ▼
ThemeConfig → Theme (colors + typo + spacing + shape + elevation)
    │
    ▼
StyleBuilder(theme)
    │ .build() → QSS string (16 types de widgets)
    ▼
QApplication.setStyleSheet(qss) + 12 widgets M3
```

```
phibuilder/
├── phi/                 ← Fondations mathématiques
│   ├── constants.py     ← φ, √5, φ²
│   ├── sequence.py      ← fibonacci(n)
│   ├── scale.py         ← SpacingToken (XXS→COLOSSAL), PhiScale
│   └── grid.py          ← PhiGrid, golden_split
├── theme/               ← Moteur M3
│   ├── color.py         ← M3ColorScheme (9 variants, ~50 couleurs)
│   ├── typo.py          ← M3Typography (15 styles display→label)
│   ├── elevation.py     ← M3Elevation (niveaux 0-5)
│   └── shape.py         ← M3Shape (radius none→full)
├── style/builder.py     ← StyleBuilder (QSS pour 16 widgets Qt)
├── widgets/             ← 12 widgets M3
└── builder.py           ← PhiBuilder facade
```

### SpacingToken (phibuilder autonome)

```python
from phibuilder.phi.scale import PhiScale, SpacingToken
_SCALE = PhiScale()  # base_spacing=4

class M3MonWidget(QWidget):
    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(_SCALE.spacing(SpacingToken.MD) * 2)  # 40px
        if theme is None: return
        c, s, t = theme.colors, theme.spacing, theme.typo
        self.setStyleSheet(
            f"M3MonWidget {{ background: {c.surface_variant}; "
            f"padding: {s.spacing(SpacingToken.XS)}px; "        # 8px
            f"border-radius: {s.spacing(SpacingToken.SM)}px; "  # 12px
            f"font-size: {t.label_medium.size}px; }}"            # 12px
        )
```

### Tokens typographiques phibuilder

| Token M3 | px | Usage |
|---|---|---|
| `t.label_small.size` | 11 | Badges |
| `t.label_medium.size` | 12 | Labels |
| `t.body_medium.size` | 14 | Texte standard |
| `t.title_medium.size` | 16 | Titres |
| `t.title_large.size` | 22 | Titres page |

### Règles phibuilder

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| R17a | `setMinimumHeight(40)` | `_SCALE.spacing(SpacingToken.MD) * 2` |
| R17b | `padding: 8px` dans QSS | `{s.spacing(SpacingToken.XS)}px` |
| R17c | `font-size: 12px` | `{t.label_medium.size}px` |
| R17d | Arithmétique avec littéral (ex: `+ 8`) | Uniquement entre tokens (ex: `spacing(XL) + spacing(XS)`) |
| R0 | `from larccommon.design_system import ds` | **JAMAIS** — phibuilder est autonome |

## 2. Contraintes — Catalogue widgets M3 (12 — phibuilder/widgets/)

| Widget | Usage | Signature |
|---|---|---|
| **M3Button** | Action principale (FILLED), secondaire (OUTLINED), discrète (TEXT) | `M3Button(text, variant=ButtonVariant.FILLED)` |
| **M3Card** | Conteneur avec ombre/fond/contour | `M3Card(variant=CardVariant.ELEVATED)` → `.content_layout()` |
| **M3TextField** | Champ saisie | `M3TextField(placeholder="...", variant=FieldVariant.OUTLINED)` |
| **M3TextEdit** | Zone texte multiligne | `M3TextEdit()` |
| **M3ComboBox** | Liste déroulante | `M3ComboBox(items=["A","B"])` |
| **M3TableWidget** | Tableau données | `M3TableWidget()` → `.set_headers()`, `.add_row()` |
| **M3ListWidget** | Liste items | `M3ListWidget()` → `.add_item(text, subtitle=)` |
| **M3Dialog** | Dialogue modal | `M3Dialog(title="...", message="...")` → `.confirmed()`/`.cancelled()` |
| **M3Snackbar** | Notification temporaire | `M3Snackbar.show(parent, message, theme)` |
| **M3TabWidget** | Onglets | `M3TabWidget()` → `.addTab(widget, "Nom")` |
| **M3NavigationBar** | Navigation horizontale | `M3NavigationBar(items=[{"label":"X","icon":"..."}])` |
| **M3ChipBar** | Filtres chips | `M3ChipBar(items=["Tous","A","B"])` → `.current_changed` |
| **M3ProgressBar** | Progression | `M3ProgressBar()` |
| **M3ScrollArea** | Zone scrollable | `M3ScrollArea()` → `.setWidget()` → `.viewport().setStyleSheet("background: transparent;")` |
| **M3Label** | Label typographique | `M3Label("Texte", style="body_medium")` |
| **M3Frame** | Conteneur fond surface | `M3Frame()` |

### Widgets métier (13 — larccommon/widgets/)

| Widget | Usage |
|---|---|
| **SidebarWidget** | Barre latérale avec sections, groupes, navigation |
| **NavButton** | Bouton navigation avec icône standardisée |
| **ThemedWidget** | QWidget avec fond QSS (contourne bug Qt `WA_StyledBackground`) |
| **ThemedDialog** | QDialog avec fond QSS |
| **StudentCard** | Carte élève cliquable (Fibonacci : compact/medium/large) |
| **CardConfig** | Config Fibonacci : PHI_COMPACT (144×89), PHI_MEDIUM (233×144), PHI_LARGE (377×233) |
| **fill_cards_grid** | Grille responsive auto-calculée |
| **make_avatar** | Avatar avec initiales colorées |
| **FilePanel** | Liste fichiers + ajout + aperçu |
| **FileViewer** | Aperçu image/texte |
| **FileResolver** | Résolution chemin local vs cloud |
| **TableSettings** | Persistance largeurs colonnes QSettings |
| **SignCard** | Carte hiéroglyphe (Medou Neter) |

### Icônes MD3 (40)

```python
from larccommon.icons import icon as md3_icon
md3_icon('search', color=p.text_strong, size=18)
```

| Catégorie | Icônes |
|---|---|
| Actions | refresh, add, arrow_back, close, check, save, delete, edit, search |
| Navigation | person, settings, menu, home, school, dashboard, logout |
| Événements | event, timer, calendar_today, schedule |
| Réseau | cloud, wifi, wifi_off |
| Statut | warning, lock, check_circle, cancel, sync, info, error, filter_list |
| Divers | visibility, location_on, bolt, subject, description |
| Thèmes | light_mode, dark_mode, contrast, tonality |

## 3. Code — Guide de choix

| Besoin | Widget |
|---|---|
| **Action principale** | `M3Button(FILLED)` |
| **Action secondaire** | `M3Button(OUTLINED)` |
| **Carte conteneur** | `M3Card(ELEVATED)` |
| **Champ formulaire** | `M3TextField(OUTLINED)` |
| **Tableau données** | `M3TableWidget` |
| **Navigation verticale** | `SidebarWidget` |
| **Navigation horizontale** | `M3NavigationBar` |
| **Onglets** | `M3TabWidget` |
| **Dialogue modal** | `M3Dialog` |
| **Notification** | `M3Snackbar.show(parent, msg, theme)` |
| **Filtres chips** | `M3ChipBar` |
| **Titre section** | `QLabel` + `s(16)` bold |
| **Fond QSS** | `ThemedWidget` (PAS `QWidget`) |

### Migration Qt → M3

| ❌ Qt brut | ✅ M3 |
|---|---|
| `QPushButton` | `M3Button` |
| `QLineEdit` | `M3TextField` |
| `QComboBox` | `M3ComboBox` |
| `QTableWidget` | `M3TableWidget` |
| `QScrollArea` | `M3ScrollArea` |
| `QFrame` (carte) | `M3Card` |
| `QTabWidget` | `M3TabWidget` |
| `QDialog` | `M3Dialog` |

## 4. Exemples

*(Voir les extraits de code dans les sections 2 et 3.)*

## 5. Step by Step

*(Ce skill est un catalogue de référence. Pour créer un widget : voir [theme-reactivity](../theme-reactivity/SKILL.md) section N.)*

## 6. Checklist

- [ ] Widget choisi dans le catalogue M3 ou métier
- [ ] Pas de `QPushButton`/`QLineEdit`/`QComboBox` brut
- [ ] Icônes via `md3_icon()`, pas PNG/JPG
- [ ] `ThemedWidget` pour tout `QWidget` avec QSS background
- [ ] `M3Dialog` pour tout dialogue modal
- [ ] `SidebarWidget` pour la navigation latérale
- [ ] `phibuilder` n'importe JAMAIS `ds` (autonome)
- [ ] `_SCALE = PhiScale()` défini au niveau module dans phibuilder
- [ ] `c, s, t = theme.colors, theme.spacing, theme.typo` pour aliasing
- [ ] `lint_qss_hardcoding.py --dir .\LarcCommon` → 0 hardcoding dans phibuilder/

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — Sous-système R17 (détail tokens phibuilder)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Règle "pas de theme=phi"
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — SidebarWidget en détail
- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — ThemedWidget obligatoire (C7)
