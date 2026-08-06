---
skill: theme-reactivity
version: "1.0"
priority: P1
category: design
depends_on: [design-tokens, color-rules]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [audit_theme_reactive.py]
reviewers: [design-reviewer]
subsystems: [J, G, N]
lines_target: 350
---

# Theme Reactivity — Réactivité des widgets aux changements de thème

## 0. Contexte

Skill de référence pour la **réactivité au thème** dans le projet Larc ERP. Il couvre la
manière dont les widgets réagissent au changement de thème (clair / sombre / égyptien)
à l'exécution.

Le backbone du système est le pattern **`_STYLE` + `_restyle_all()`** :
une propriété `_STYLE` qui génère le QSS du composant à partir des jetons dynamiques du
thème, et une méthode `_restyle_all()` qui réapplique ce QSS (puis le style inline de
chaque widget) à chaque signal `ds.theme_changed`.

Trois sous-systèmes :
- **J — Theme Reactivity Pattern** (règles J1-J7). Module de référence : `LarcSuperviseur`.
- **G — phibuilder Widget Theme Reactivity** (règles G1-G5). Source : `pyside6-wrapper`.
- **N — Gabarit de nouveau composant** (template complet et opérationnel).

## 1. Fonction Principale

### Type : Système Fermé

### 1.1 `theme=phi` gèle le thème à la construction

Tout widget phibuilder instancié avec `theme=phi` capture le thème **au moment de sa
construction** : couleurs et styles deviennent des valeurs figées, plus aucun signal de
changement de thème ne le touche. Après un changement de thème, ces widgets restent en
clair dans une UI sombre (ou l'inverse) — c'est le bug du « thème figé ».

Les widgets créés **sans** `theme=` héritent du **QSS global** → ils réagissent aux
changements de thème.

### 1.2 Le bug `WA_StyledBackground` de Qt

`QWidget` / `QDialog` n'activent pas `WA_StyledBackground` par défaut : un `background`
posé en QSS sur un `QWidget` nu est **invisible** (le fond n'est jamais peint). Il faut
utiliser `ThemedWidget` / `ThemedDialog` de `larccommon.widgets.themed_widget`, qui posent
ce flag correctement.

### 1.3 Le QSS ne cible que les widgets nommés

Un sélecteur QSS (`M3Label#panel_title`, `M3Frame#panel`…) ne matche que si le widget a un
`setObjectName()`. Sans nom d'objet, le style global ne peut pas cibler le widget.

## 2. Contraintes Fondamentales

### Sous-système J — Theme Reactivity Pattern

Règles J1-J7. Module de référence : **LarcSuperviseur** (implémentation correcte du pattern).

### J1 — Ne jamais passer `theme=` aux widgets phibuilder

| ❌ | ✅ |
|---|---|
| `M3Button("Action", theme=phi)` | `M3Button("Action")` — hérite du QSS global |

### J2 — Ne jamais capturer `phi_theme` en variable locale

| ❌ | ✅ |
|---|---|
| `phi = theme_manager.phi_theme` puis usage local | `ds.phi` si un accès est réellement nécessaire, sinon rien |

### J3 — `setStyleSheet` avec des jetons de palette dynamiques

| ❌ | ✅ |
|---|---|
| `setStyleSheet("color: #333333;")` | `setStyleSheet(f"color: {ds.p.text_strong};")` |

### J4 — Toujours `setObjectName()` sur chaque widget

| ❌ | ✅ |
|---|---|
| `self._title = M3Label("Titre")` — sélecteur QSS jamais matché | `self._title = M3Label("Titre"); self._title.setObjectName("panel_title")` |

### J5 — `_restyle_all()` doit couvrir TOUS les widgets

| ❌ | ✅ |
|---|---|
| `_restyle_all()` ne réapplique que le QSS global | QSS global **+** chaque widget un par un (styles inline réappliqués) |

### J6 — Connexion `ds.theme_changed` obligatoire dans `__init__`

| ❌ | ✅ |
|---|---|
| Aucune connexion → le composant ne réagit jamais | `ds.theme_changed.connect(self._restyle_all)` dans `__init__` |

### J7 — `QWidget()`/`QDialog()` → `ThemedWidget()`/`ThemedDialog()`

| ❌ | ✅ |
|---|---|
| `class MaVue(QWidget)` + QSS `background` invisible (bug `WA_StyledBackground`) | `ThemedWidget` / `ThemedDialog` de `larccommon.widgets.themed_widget` |

### 2.1 Pattern de référence — LarcSuperviseur

```python
class MaVue(QWidget):
    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle_all)
        self._init_ui()

    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            QWidget#root {{ background: {p.background}; }}
            M3Label#panel_title {{ font-size: {s(14)}px; font-weight: bold; color: {p.text_strong}; }}
            M3Frame#panel {{ background: {p.surface}; border: 1px solid {p.outline_variant}; border-radius: {d.radius_lg}px; }}
        """

    def _init_ui(self):
        self.setObjectName("root")
        self.setStyleSheet(self._STYLE())
        self._title = M3Label("Titre")
        self._title.setObjectName("panel_title")
        self._panel = M3Frame()
        self._panel.setObjectName("panel")

    def _restyle_all(self):
        self.setStyleSheet(self._STYLE())
        p = theme_manager.palette
        s = theme_manager.font_size
        self._widget_inline.setStyleSheet(f"color: {p.text_strong}; font-size: {s(12)}px;")
        self._theme_btn.setIcon(self._theme_icon())
```

### Sous-système G — phibuilder Widget Reactivity

Règles G1-G5. Source : **pyside6-wrapper** (contrôle des vues phibuilder).

### G1 — Jamais `M3Label(..., theme=phi)` avec un `phi` capturé

| ❌ | ✅ |
|---|---|
| `M3Label("Titre", theme=phi)` — phi capturé en amont | `M3Label("Titre")` sans `theme=` |

### G2 — Jamais `phi = theme_manager.phi_theme` dans `_init_ui()`

| ❌ | ✅ |
|---|---|
| `phi = theme_manager.phi_theme` dans `_init_ui()` | `ds.phi` si nécessaire, sinon rien |

### G3 — Widgets sans `setObjectName()` : toujours en poser un

| ❌ | ✅ |
|---|---|
| Widget créé sans nom → QSS global sans effet | `setObjectName()` posé dès la création |

### G4 — `setStyleSheet` avec des valeurs en dur

| ❌ | ✅ |
|---|---|
| `setStyleSheet("background: #ffffff;")` | `setStyleSheet(f"background: {ds.p.surface};")` |

### G5 — Ordre : widgets créés APRÈS la capture de `phi`

| ❌ | ✅ |
|---|---|
| Widgets créés après une capture de `phi` (risque de `theme=`) | Widgets créés avant la connexion `theme_changed` |

**Pourquoi :** `theme=phi` **gèle** le thème au moment de la construction. Les widgets
créés sans `theme=` héritent du QSS global → ils réagissent aux changements de thème.

## 3. Code complet

### Gabarit de nouveau composant (Sous-système N)

Template complet et opérationnel pour créer **toute nouvelle vue / panneau / widget**.
Copier-coller, puis remplacer le préfixe `mon_*` par un préfixe propre au composant.

```python
from PySide6.QtWidgets import QVBoxLayout
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot
from larccommon.widgets.themed_widget import ThemedWidget
from phibuilder.widgets import M3Button, M3Label, M3Frame

class MonNouveauComposant(ThemedWidget):
    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            QWidget#mon_root {{ background: {p.surface}; color: {p.text_strong}; border: 1px solid {p.outline_variant}; border-radius: {ds.radius_sm}px; }}
            M3Label#mon_titre {{ font-size: {s(14)}px; font-weight: bold; color: {p.text_strong}; }}
            M3Button#mon_bouton {{ background: {p.primary}; color: {p.on_primary}; border: none; border-radius: {ds.radius_lg}px; padding: {d.btn_pad_v}px {d.btn_pad_h}px; font-size: {s(13)}px; }}
        """

    def __init__(self, parent=None):
        super().__init__(parent)
        ds.theme_changed.connect(self._restyle_all)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName("mon_root")
        self.setStyleSheet(self._STYLE())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
        layout.setSpacing(ds.space_xs)
        self._title = M3Label("Titre")
        self._title.setObjectName("mon_titre")
        layout.addWidget(self._title)
        self._button = M3Button("Action")
        self._button.setObjectName("mon_bouton")
        layout.addWidget(self._button)
        # Icon MD3 (never PNG/JPG)
        self._icon = md3_icon("refresh", color=theme_manager.palette.text_strong, size=theme_manager.image.icon_btn)

    def _restyle_all(self):
        self.setStyleSheet(self._STYLE())
```

Notes d'utilisation :
- **Héritage** : `ThemedWidget` (J7) — jamais de `QWidget` nu avec fond QSS.
- **Slots** : tout slot décoré `@safe_slot("MonNouveauComposant.action")` → voir `pyside6-wrapper`.
- **Icônes** : toujours `md3_icon(...)` (SVG MD3) — jamais de PNG/JPG.
- **Jetons** : uniquement `ds.space_*`, `ds.radius_*`, `ds.p.*` — zéro px/hex en dur → voir
  `zero-hardcoding` et `color-rules`.
- **Widgets à style inline** : si un widget a besoin d'un style réactif non couvert par le
  QSS global, l'ajouter dans `_restyle_all()` (J5).

## 4. Exemples

### Exemples avant / après

### 5.1 Thème figé à la construction (J1/J2)

**Avant** — le titre et le bouton gèlent le thème à la construction :

```python
def _init_ui(self):
    phi = theme_manager.phi_theme              # J2 ❌ capture locale
    self._title = M3Label("Titre", theme=phi)  # J1 ❌ theme=phi
    self._btn = M3Button("Action", theme=phi)  # J1 ❌ theme=phi
```

Résultat : après un changement de thème, le titre et le bouton restent aux couleurs de
l'ancien thème — le QSS global ne les touche pas, `_restyle_all()` est sans effet.

**Après** — les widgets héritent du QSS global :

```python
def _init_ui(self):
    self._title = M3Label("Titre")             # J1 ✅ sans theme=
    self._title.setObjectName("panel_title")   # J4 ✅
    self._btn = M3Button("Action")             # J1 ✅ sans theme=
    self._btn.setObjectName("panel_btn")       # J4 ✅
```

Résultat : le QSS global (régénéré par `_restyle_all()`) les re-style à chaque changement
de thème.

### 5.2 Couleurs en dur + widget sans nom (J3/J4)

**Avant** :

```python
def _init_ui(self):
    self.setStyleSheet("M3Frame#panel { background: #f5f5f5; border-radius: 8px; }")
    self._panel = M3Frame()  # J4 ❌ jamais de setObjectName
```

Résultat : le sélecteur `M3Frame#panel` ne matche **rien** (pas de nom d'objet), et la
couleur `#f5f5f5` est figée — le panneau ne réagit pas au thème.

**Après** :

```python
def _init_ui(self):
    self._panel = M3Frame()
    self._panel.setObjectName("panel")   # J4 ✅
    self.setStyleSheet(self._STYLE())    # J3 ✅ jetons dynamiques
```

Avec dans `_STYLE()` : `M3Frame#panel { background: {p.surface}; border-radius: {d.radius_lg}px; }`.
Résultat : le sélecteur matche, et `p.surface` est réévalué à chaque `_restyle_all()`.

### 5.3 QWidget nu au fond invisible (J7)

**Avant** :

```python
class MonPanel(QWidget):   # J7 ❌ QWidget nu
    def _init_ui(self):
        self.setObjectName("mon_root")
        self.setStyleSheet("QWidget#mon_root { background: #ffffff; }")
```

Résultat : le fond n'est pas peint (bug Qt `WA_StyledBackground` non posé) — panneau
transparent au lancement.

**Après** :

```python
from larccommon.widgets.themed_widget import ThemedWidget

class MonPanel(ThemedWidget):   # J7 ✅
    def _init_ui(self):
        self.setObjectName("mon_root")
        self.setStyleSheet(self._STYLE())
```

Résultat : `ThemedWidget` pose `WA_StyledBackground` → fond peint immédiatement et suivi
du thème.

## 5. Step by Step

## 6. Checklist + Références

### 6.1 Checklist (linter `audit_theme_reactive.py`)

- [ ] 0 `theme=` passé aux widgets phibuilder — `grep -rn "theme=phi"` (hors tests) → 0 résultat
- [ ] 0 capture locale de `phi_theme` — `grep -rn "phi_theme"` → seulement dans `larccommon/theme.py`
- [ ] 0 hex en dur dans les QSS — `grep -rnE "#[0-9A-Fa-f]{3,8}"` → 0 dans les vues
- [ ] 0 px en dur hors `_STYLE` — `grep -rn "[0-9]px"` → 0 dans les vues
- [ ] `ds.theme_changed.connect` présent dans `__init__` de chaque classe de vue
- [ ] `_STYLE` et `_restyle_all` définis pour chaque classe de vue
- [ ] Chaque widget a un `setObjectName()` (dans les 3 lignes après création)
- [ ] Toute `setStyleSheet` inline réapparaît dans `_restyle_all()`
- [ ] 0 `QWidget`/`QDialog` nu avec `background:` QSS → toujours `ThemedWidget`/`ThemedDialog`

Règle de passage en revue : **échec si un seul contrôle échoue**. Le reviewer
`design-reviewer` applique cette checklist sur chaque nouvelle vue.

### 6.2 Références croisées

| Skill | Lien |
|---|---|
| `color-rules` | noms et sémantique des jetons palette (`p.primary`, `p.surface`, `p.text_strong`…) |
| `design-tokens` | jetons `ds.space_*`, `ds.radius_*`, `ds.p.*` — dépendance déclarée |
| `zero-hardcoding` | interdiction des `px` et couleurs en dur dans les vues |
| `pyside6-wrapper` | `@safe_slot` pour tous les slots Qt ; source des règles G |
| `design-reviewer` | reviewer en charge de la checklist 6.1 |
