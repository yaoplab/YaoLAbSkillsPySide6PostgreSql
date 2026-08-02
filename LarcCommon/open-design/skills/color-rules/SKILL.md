---
skill: color-rules
version: "1.0"
priority: P0
category: design
depends_on: [design-tokens]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [lint_d1_color_checker.py]
reviewers: [design-reviewer]
subsystems: [D, D1, D2, D3, D4, D5, D6, D7, P]
lines_target: 350
---

# Skill: Color Rules

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Hub, Design)
**Module** : Palette `ds.p.*` (`larccommon/design_system.py`) + `larccommon/theme.py` (PROGRAM_STYLES)
**Utilisateurs** : Tous les développeurs Larc — **P0 : s'applique à CHAQUE vue**
**Dépendances** : skill `design-tokens` (tokens numériques)
**Linter** : `scripts/lint_d1_color_checker.py` (D-linter — hook pre-commit `lint-dlinter`)
**Revue** : `design-reviewer` — les tokens `ds.p.*` sont résolus dynamiquement depuis la palette du thème actif.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Code PySide6 avec hex en dur, HTML/QSS sans `color:`, contrastes insuffisants, widgets non réactifs au thème
**Sortie** : Code 100 % conforme — tokens `ds.p.*` partout, couleur EXPLICITE sur tout texte, contraste light/dark garanti
**Traitement** : D1 (explicite) → D3 (zéro hex) → D4/D5 (contrastes) → D6/D7 (restyle) → P (programmes)

## 2. Contraintes Fondamentales

| # | Contrainte | Gravité |
|---|---|---|
| C1 | **TOUT texte a sa couleur explicitement définie** (token palette) — jamais d'héritage Qt (D1) | 🔴 Bloquant |
| C2 | **ZÉRO hex** `#RRGGBB`/`#RGB` dans `setStyleSheet()` (D3) | 🔴 Bloquant |
| C3 | **Contraste garanti** : petit texte et gris-sur-gris interdits en dark (D4/D5) | 🔴 Bloquant |
| C4 | **Réactivité au thème** : `theme_changed` connecté + `_restyle()` complet (D6/D7) | 🔴 Bloquant |
| C5 | **Couleurs des programmes** centralisées dans `PROGRAM_STYLES` (P) | 🔴 Bloquant |

### Sous-système D — Color Palette (22 tokens)

```python
ds.p.primary              # Couleur primaire
ds.p.on_primary           # Texte sur primaire
ds.p.primary_container    # Conteneur primaire
ds.p.secondary            # Couleur secondaire
ds.p.on_secondary
ds.p.secondary_container
ds.p.tertiary
ds.p.on_tertiary
ds.p.tertiary_container
ds.p.error                # Erreur
ds.p.on_error
ds.p.error_container
ds.p.surface              # Surface
ds.p.surface_variant      # Surface alternative
ds.p.background           # Fond application
ds.p.outline              # Contour
ds.p.outline_variant      # Contour léger
ds.p.text_strong          # Texte principal
ds.p.text_soft            # Texte secondaire
ds.p.text_disabled        # Texte désactivé
ds.p.success              # Succès
ds.p.border               # Bordure
```

**RÈGLE** : Ne JAMAIS écrire `color: #1565C0` ou `background: #c0392b`.
**✅ Bon** : `color: {p.primary}` ou `background: {p.error}` — avec `p = theme_manager.palette`.

**Guide rapide** : `text_strong` = défaut pour tout texte ; `text_soft` = secondaire (réservé
au QSS `_STYLE`, ≥ 12px) ; `text_disabled` = metadata ; `outline`/`outline_variant` = contours ;
`border` = séparateurs ; `success` = feedback positif ; `error`/`error_container` = erreurs.

### Sous-système D1 — Règle EXPLICITE des couleurs de texte (LA RÈGLE LA PLUS IMPORTANTE)

**Principe fondateur** : Tout texte affiché dans l'interface DOIT avoir sa couleur
EXPLICITEMENT définie via un token `{p.text_strong}` ou `{p.text_soft}`. **Ne JAMAIS
compter sur l'héritage** de la palette Qt, du QSS parent, ou du thème phibuilder.

**Pourquoi ?**

| Mécanisme d'héritage | Problème constaté |
|---|---|
| Héritage QPalette::WindowText | Qt utilise **NOIR** par défaut — illisible en mode dark |
| Héritage du QSS parent | `color:` n'est PAS cascadé aux widgets enfants comme `QLabel` |
| HTML sans `color:` (`<b>Nom</b>`) | Qt RichText utilise la couleur par défaut (NOIR) |
| phibuilder.setStyleSheet() | La palette Qt complète n'est pas définie — WindowText reste NOIR |

**Sanction** : Si un texte est noir en mode dark, il manque une couleur explicite —
appliquer D1a, D1b ou D1c selon le cas.

#### Cas D1a — QLabel RichText/HTML

Toute balise HTML passée à `setText()` DOIT contenir `color:`.

| ❌ Erreur | ✅ Correction |
|---|---|
| `setText("<b>Nom</b>")` | `setText("<b style='color:{p.text_strong}'>Nom</b>")` |
| `<b style='font-size:{s(12)}px'>Nom</b>` | `<b style='font-size:{s(12)}px; color:{p.text_strong}'>Nom</b>` |
| `<span>Prénom</span>` (pas de color) | `<span style='color:{p.text_soft}'>Prénom</span>` |

**Pattern obligatoire** : voir section 3, pattern 1.

#### Cas D1b — QSS de widgets conteneurs

Chaque bloc QSS de widget conteneur (QFrame, StudentCard, M3Frame...) DOIT contenir
`color:` en plus de `background:` — c'est lui qui donne la couleur aux labels enfants.

| ❌ Erreur | ✅ Correction |
|---|---|
| `StudentCard { background: {p.surface}; }` | `StudentCard { background: {p.surface}; color: {p.text_strong}; }` |
| `M3Frame#panel { background: {p.surface}; }` | `M3Frame#panel { background: {p.surface}; color: {p.text_strong}; }` |
| Bloc `:hover` sans `color:` | `:hover { background: {p.surface_variant}; color: {p.text_strong}; }` |

**Pattern obligatoire** : voir section 3, pattern 2.

#### Cas D1c — setStyleSheet() inline

Tout style inline utilise des **tokens de palette**, jamais de hex.

| ❌ Erreur | ✅ Correction |
|---|---|
| `setStyleSheet("color: #1565C0;")` | `setStyleSheet(f"color: {p.primary};")` |
| `setStyleSheet("background: white; color: black;")` | `setStyleSheet(f"background: {p.surface}; color: {p.text_strong};")` |

**RÈGLE ABSOLUE D1** : Tout `QLabel.setText()` avec HTML, tout `setStyleSheet()` sur un widget
conteneur, et tout QSS inline DOIT inclure `color:` avec un token de la palette.

### Sous-système D2 — Référence linter (D-linter)

```bash
python scripts/lint_d1_color_checker.py --rule D1      # setText() HTML sans color:
python scripts/lint_d1_color_checker.py --rule J7      # Widgets sans WA_StyledBackground
python scripts/lint_d1_color_checker.py --rule D3      # Hex hardcodés
python scripts/lint_d1_color_checker.py --rule D4      # Contrastes insuffisants
python scripts/lint_d1_color_checker.py --rule D5      # text_soft inline
python scripts/lint_d1_color_checker.py --rule D6      # Palette sans theme_changed
python scripts/lint_d1_color_checker.py --rule D7      # _restyle() incomplet
python scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7  # Tout
```

Options : `--dir .\LarcSuperviseur` (un module), `--json` (sortie parsable),
`--fix-only` (mode compact — utilisé par le hook pre-commit `lint-dlinter`, config centrale
`C:\projets\.pre-commit-config.yaml`, entry `--rule D1+J7+D3+D4+D5+D6+D7 --fix-only`).

### Sous-système D3 — ZÉRO hex dans setStyleSheet()

Tout `#RRGGBB` ou `#RGB` (ex. `#fff`, `#3498db`) dans un `setStyleSheet()` est une violation D3.

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `setStyleSheet("background: #3498db; color: white;")` | `setStyleSheet(f"background: {p.primary}; color: {p.on_primary};")` |
| `setStyleSheet("border: 1px solid #BDBDBD;")` | `setStyleSheet(f"border: 1px solid {p.outline_variant};")` |
| `QColor("#c0392b")` | `QColor(p.error)` |

Les hex sont tolérés UNIQUEMENT dans `larccommon/theme.py` et `phibuilder/` (définition des thèmes) — jamais dans les vues.

### Sous-système D4 — Règles de contraste

| # | Détection | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| D4a | `font-size < 12px` AVEC `color: text_soft` | `font-size: {s(10)}px; color: {p.text_soft}` | `font-size: {s(10)}px; color: {p.text_strong}` |
| D4b | `background: surface_variant` AVEC `color: text_soft` | `background: {p.surface_variant}; color: {p.text_soft}` | `background: {p.surface_variant}; color: {p.text_strong}` |

**Justification** : en dark, `text_soft` est gris moyen ; sous 12px ou sur `surface_variant`, le contraste devient insuffisant — forcer `text_strong`.

### Sous-système D5 — text_soft interdit en setStyleSheet() inline

`color: {p.text_soft}` dans `widget.setStyleSheet()` **inline** (appel direct sur un widget,
hors property `_STYLE`) = gris sur gris en dark.

| Context | ✅ Autorisé |
|---|---|
| `_STYLE` property (QSS global de la vue) | `text_soft` autorisé (fond clair, taille ≥ 12px) |
| `setStyleSheet()` inline sur un widget | `text_soft` INTERDIT → utiliser `text_strong` |

**✅ Bon** : `self._hint.setStyleSheet(f"color: {p.text_strong}; font-size: {s(12)}px;")`
**❌ Mauvais** : `self._hint.setStyleSheet(f"color: {p.text_soft}; font-size: {s(12)}px;")`

### Sous-système D6 — Connexion theme_changed OBLIGATOIRE

Toute classe utilisant des tokens palette dans `setStyleSheet()` DOIT se connecter à
`ds.theme_changed` (sinon le widget reste aux couleurs du thème de sa création).

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| D6 | Tokens `{p.xxx}` dans `setStyleSheet()` sans `theme_changed.connect` | `ds.theme_changed.connect(self._restyle)` dans `__init__` |

**Exemptions documentées (ne PAS corriger) :**
- `ThemeManager` — génère les thèmes, n'affiche pas de widgets
- `QssHelper` — génère du QSS, pas de widgets
- `M3Dialog` / `QDialog` (et `QStyledItemDelegate`) — éphémères, palette lue à la construction, recréés à chaque ouverture
- `LoginWindow` — thème figé avant l'affichage, pas de bascule

**Rappel** : une classe avec un hook de restyle (`def _restyle`, `restyle`, `_restyle_all`,
`_update_style`, `refresh_theme`) piloté par son parent est considérée couverte. ⚠️ Les
properties `_STYLE_ACTIF`/`_STYLE_INACTIF` seules ne comptent PAS comme hook.

**Cross-référence** : pattern complet `_STYLE` + `_restyle_all` → skill **`theme-reactivity`**.

### Sous-système D7 — Complétude de _restyle()

`_restyle()` DOIT mettre à jour TOUS les widgets stylés avec des tokens palette (QSS global
+ chaque widget inline + icônes). Un widget oublié reste aux couleurs de l'ancien thème.

**Détection d'alias** : `_rebuild`, `_restyle_all`, `restyle`, `_update_style`,
`refresh_theme` comptent comme `_restyle()` — si `_restyle()` délègue à l'un d'eux, le corps
de la méthode appelée est aussi scanné par le D-linter.

**Cas gérés** : appels multi-lignes ; variables avec dot (`self._var`) ; indirection côté
`_restyle` (`qss = f"...{p.x}..."; setStyleSheet(qss)` compte comme couvert). ⚠️ **Limite
connue** : l'indirection côté builder (`qss = f"..."; self._x.setStyleSheet(qss)` AVANT
`_restyle`) n'est pas traquée — vérifier manuellement.

**Cross-référence** : pattern de restyle complet → skill **`theme-reactivity`**.

### Sous-système P — Couleurs des programmes (PEI, MYP, DPFr, DPEn)

**Principe** : les couleurs des 4 programmes sont **centralisées** dans
`larccommon.theme.PROGRAM_STYLES` et utilisent des **noms de rôles** M3 (pas des hex).
Tous les modules Larc utilisent exactement les mêmes couleurs, quel que soit le thème actif.

#### P1 — Matrice PROGRAM_STYLES

| Programme | Rôle fg (solide) | Rôle bg (container) | Rôle on_fg (texte) | Sens |
|---|---|---|---|---|
| **PEI** | `primary` | `primary_container` | `on_primary` | Premier cycle, prioritaire |
| **MYP** | `secondary` | `secondary_container` | `on_secondary` | Deuxième cycle, complémentaire |
| **DPFr** | `error` | `error_container` | `on_error` | Attention, distingué (rouge) |
| **DPEn** | `tertiary` | `tertiary_container` | `on_tertiary` | Bilingue, tertiaire (orange) |

#### P2 — Code centralisé (larccommon/theme.py)

```python
# Ne JAMAIS redéfinir ce dict dans les apps — toujours importer PROGRAM_STYLES
PROGRAM_STYLES: dict[str, tuple[str, str, str]] = {
    "PEI":  ("primary",   "primary_container",   "on_primary"),
    "MYP":  ("secondary", "secondary_container",  "on_secondary"),
    "DPFr": ("error",     "error_container",      "on_error"),
    "DPEn": ("tertiary",  "tertiary_container",   "on_tertiary"),
}
```

Les noms de rôles sont résolus dynamiquement : `getattr(p, role_name)` avec
`p = theme_manager.palette` → `"primary"` vaut `#1565C0` en light, `#64B5F6` en dark.

#### P4 — Règles absolues

| # | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|
| P4a | Définir `prog_style` en dur dans chaque app | Importer `PROGRAM_STYLES` depuis `larccommon.theme` | 🔴 Bloquant |
| P4b | Couleurs hex dans `prog_style` | Utiliser des **noms de rôles** (primary, secondary...) | 🔴 Bloquant |
| P4c | Modifier PROGRAM_STYLES dans une app | Le modifier UNIQUEMENT dans `larccommon/theme.py` | 🔴 Bloquant |
| P4d | Nouveau programme sans l'ajouter à PROGRAM_STYLES | Ajouter le programme + documenter dans ce skill | 🟡 Important |

**Cross-référence** : application dans le sidebar (résolution `_resolve_colors`, hover par
inversion fg↔bg, checked) → skill **`sidebar-spec`** (règles K15, K22-K23).

## 3. Code complet — Patterns canoniques

```python
from larccommon.design_system import ds
from larccommon.theme import theme_manager, PROGRAM_STYLES

p = theme_manager.palette
s = theme_manager.font_size

# 1) QLabel RichText — D1a : color: dans CHAQUE balise
self._name.setText(
    f"<b style='font-size:{s(14)}px; color:{p.text_strong}'>{last_name}</b><br>"
    f"<span style='font-size:{s(12)}px; color:{p.text_soft}'>{first_name}</span>"
)

# 2) Widget conteneur — D1b : color: dans CHAQUE bloc (normal + hover)
self.setStyleSheet(f"""
    StudentCard {{
        background: {p.surface}; color: {p.text_strong};  /* ← OBLIGATOIRE */
        border: 1px solid {p.outline_variant};
    }}
    StudentCard:hover {{
        background: {p.surface_variant}; color: {p.text_strong};  /* ← OBLIGATOIRE aussi */
    }}
""")

# 3) Style inline — D1c : tokens uniquement, jamais hex ; D5 : text_strong, pas text_soft
self._status.setStyleSheet(f"color: {p.text_strong}; font-size: {s(12)}px;")

# 4) Réactivité au thème — D6 + D7
class MaVue(ThemedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        ds.theme_changed.connect(self._restyle)          # D6
        self._init_ui()

    def _style(self) -> str:
        return f"color: {theme_manager.palette.text_strong};"   # D7 : source unique

    def _restyle(self):
        self._lbl.setStyleSheet(self._style())           # D7 : TOUT restyler ici

# 5) Programmes — P : import centralisé, jamais de dict local
fg_role, bg_role, on_fg_role = PROGRAM_STYLES["PEI"]
fg, bg, on_fg = getattr(p, fg_role), getattr(p, bg_role), getattr(p, on_fg_role)
```

## 4. Exemples

### Exemple 1 — QLabel RichText (D1a)

```python
# ❌ AVANT — texte NOIR en mode dark (héritage Qt RichText)
self._name.setText(f"<b>{last_name}</b><br><span>{first_name}</span>")

# ✅ APRÈS — color: explicite dans chaque balise
self._name.setText(
    f"<b style='color:{p.text_strong}'>{last_name}</b><br>"
    f"<span style='color:{p.text_soft}'>{first_name}</span>"
)
```

### Exemple 2 — Widget conteneur (D1b)

```python
# ❌ AVANT — fond correct, labels enfants NOIRS (color: absent)
self.setStyleSheet(f"StudentCard {{ background: {p.surface}; border: 1px solid {p.outline_variant}; }}")

# ✅ APRÈS — color: dans chaque bloc, normal ET hover
self.setStyleSheet(f"""
    StudentCard {{
        background: {p.surface}; color: {p.text_strong};
        border: 1px solid {p.outline_variant};
    }}
    StudentCard:hover {{
        background: {p.surface_variant}; color: {p.text_strong};
    }}
""")
```

### Exemple 3 — Hex + petit texte (D3 + D4a)

```python
# ❌ AVANT — hex hardcodé + text_soft sur petit texte : illisible en dark
self._status.setStyleSheet("color: #757575; font-size: 10px;")

# ✅ APRÈS — token + text_strong (D4a : font-size < 12px → text_strong)
self._status.setStyleSheet(f"color: {p.text_strong}; font-size: {s(11)}px;")
```

### Exemple 4 — Réactivité au thème (D6 + D7)

```python
# ❌ AVANT — tokens, mais figés au thème de la création
class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self._lbl.setStyleSheet(f"color: {p.text_strong};")   # jamais restylé

# ✅ APRÈS — theme_changed connecté + _restyle() complet
class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle)               # D6
        self._lbl.setStyleSheet(f"color: {theme_manager.palette.text_strong};")

    def _restyle(self):                                       # D7
        self._lbl.setStyleSheet(f"color: {theme_manager.palette.text_strong};")
```

## 5. Step by Step — Mise en conformité d'une vue

| # | Action | Règle | Vérification |
|---|---|---|---|
| 1 | Lancer le D-linter complet sur la vue | D2 | `--rule D1+J7+D3+D4+D5+D6+D7` → liste des violations |
| 2 | Remplacer tous les hex par des tokens | D3 | Plus aucun `#RRGGBB` dans `setStyleSheet()` |
| 3 | Ajouter `color:` aux balises HTML des `setText()` | D1a | D-linter D1 = 0 |
| 4 | Ajouter `color:` aux blocs QSS conteneurs (normal + hover) | D1b | D-linter D1 = 0 |
| 5 | `text_soft` → `text_strong` si < 12px ou sur surface_variant | D4/D5 | D-linter D4 + D5 = 0 |
| 6 | Connecter `ds.theme_changed` si absent | D6 | D-linter D6 = 0 |
| 7 | Compléter `_restyle()` (QSS global + widgets inline + icônes) | D7 | D-linter D7 = 0 |
| 8 | Vérifier `PROGRAM_STYLES` importé, jamais redéfini | P | Grep : 1 seule définition dans `larccommon/theme.py` |
| 9 | Test manuel dark mode : aucun texte noir, aucune zone gris sur gris | D1/D4 | Bascule du thème, inspection visuelle |

## 6. Checklist (mécaniquement vérifiable)

- [ ] D-linter complet à 0 : `python scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7` → aucun finding
- [ ] **D1** : 0 `setText()` avec HTML sans `color:` (vérifié par D-linter)
- [ ] **D1b** : 0 bloc QSS conteneur sans `color:` (normal ET hover)
- [ ] **D1c** : 0 `color:` avec valeur hex dans un style inline
- [ ] **D3** : 0 `#RRGGBB` / `#RGB` dans `setStyleSheet()` (grep `#([0-9a-fA-F]{3}){1,2}\b`)
- [ ] **D4a** : 0 `font-size < 12px` associé à `text_soft`
- [ ] **D4b** : 0 `background: surface_variant` associé à `text_soft`
- [ ] **D5** : 0 `text_soft` dans un `setStyleSheet()` inline (hors `_STYLE`)
- [ ] **D6** : toute classe avec tokens palette a `ds.theme_changed.connect(...)` (sauf exemptions : ThemeManager, QssHelper, M3Dialog/QDialog, LoginWindow)
- [ ] **D7** : `_restyle()` couvre TOUS les widgets stylés en inline (aucun oubli après bascule de thème)
- [ ] **J7** : 0 widget conteneur avec `background:` QSS sans `WA_StyledBackground` (via ThemedWidget/ThemedDialog)
- [ ] **P** : `PROGRAM_STYLES` importé depuis `larccommon.theme`, jamais redéfini, 0 hex (P4a-P4c)
- [ ] Test manuel : bascule light ↔ dark → aucun texte noir, aucune zone gris sur gris, couleurs programmes identiques aux autres modules

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — Tokens numériques (espacements, hauteurs, polices)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + _restyle_all (D6/D7)
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — Utilise PROGRAM_STYLES pour les couleurs programme
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — Règle zéro hardcoding (inclut les couleurs)
