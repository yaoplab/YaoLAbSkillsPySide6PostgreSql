---
skill: zero-hardcoding
version: "1.0"
priority: P0
category: design
depends_on: [design-tokens, color-rules]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [R, I, L]
lines_target: 350
---

# Skill — Zero Hardcoding (Règle Absolue)

> **Règle ABSOLUE du projet Larc ERP.** Aucune valeur pixel littérale dans le code
> Python. Toute valeur visuelle DOIT utiliser un token (`ds.*`, `theme_manager.image.*`,
> `s()`). Le seul code toléré : `0` et `1` (R12). Tout le reste passe par le linter R.

## 0. Contexte

| Champ | Valeur |
|---|---|
| Priorité | 🔴 P0 — bloquant en revue, bloquant en CI |
| Périmètre | LarcProf, LarcSuperviseur, LarcFacture, LarcStock, LarcCompta, LarcCommon |
| Vérification | `lint_qss_hardcoding.py` (pre-commit + revue manuelle) |
| Reviewers | `design-reviewer` |
| Dépendances | `design-tokens` (valeurs de remplacement), `color-rules` (couleurs), `theme-reactivity` (J7/ThemedWidget) |
| Sous-systèmes | R (règles linter), I (anti-patterns visuels), L (philosophie M3+Fibonacci) |

## 1. Fonction Principale

### Type : Système Fermé

**Objectif.** Garantir une UI réactive au thème et aux proportions Fibonacci. Un
hardcoding qui s'infiltre reste figé quand le thème, la langue ou l'échelle change :
couleurs désynchronisées, hauteurs cassées, espacements incohérents. Le linter R
dissuade ; les tokens sont la solution.

**Quand appliquer.** Tout code touchant l'UI : vues (`LarcProf/views/`), widgets
(LarcCommon), QSS, layouts, icônes, tailles d'images.

**Quand NE PAS appliquer.** Logique métier sans dimension visuelle (calculs, I/O).
Les exceptions R12 (`0`, `1`, `17` sur M3ProfileButton) restent autorisées.

## 2. Contraintes Fondamentales

### 2.1 Sous-système R — Zero Hardcoding Rule (R1-R16)

| # | Règle | ❌ Interdit | ✅ Requis | Sévérité |
|---|---|---|---|---|
| R1 | Pas de `border-radius: Npx` | `border-radius: 6px` | `border-radius: {ds.radius_sm}px` | 🔴 P0 |
| R2 | Pas de `padding: Npx` | `padding: 8px 12px` | `padding: {ds.space_xs}px {ds.space_sm}px` | 🔴 P0 |
| R3 | Pas de `margin: Npx` | `margin: 20px` | `margin: {ds.space_md}px` | 🔴 P0 |
| R4 | Pas de `font-size: Npx` | `font-size: 14px` | `font-size: {s(14)}px` | 🟡 P1 |
| R5 | Pas de `setFixedHeight(N)` | `setFixedHeight(52)` | `setFixedHeight(ds.button_height)` | 🟡 P1 |
| R6 | Pas de `setFixedWidth(N)` | `setFixedWidth(233)` | `setFixedWidth(ds.sidebar_width)` | 🟡 P1 |
| R6b | Pas de min/max-width/height en QSS | `min-width: 180px` | `min-width: {ds.space_xl}px` | 🟡 P1 |
| R7 | Pas de `setContentsMargins(N,N,N,N)` | `setContentsMargins(6,6,6,6)` | `setContentsMargins(ds.space_sm, ...)` | 🟡 P1 |
| R8 | Pas de `setSpacing(N)` | `setSpacing(6)` | `setSpacing(ds.space_xs)` | 🟡 P1 |
| R9 | Pas de `setMinimumHeight > 40` | `setMinimumHeight(48)` | `setMinimumHeight(ds.space_xl)` | 🟢 P2 |
| R9b | Pas de `setMinimumSize`/`setMaximumSize` | `setMinimumSize(987, 610)` | `setMinimumSize(ds.space_*, ds.space_*)` | 🟡 P1 |
| R10 | Pas de couleurs alternées | `setAlternatingRowColors(True)` | `setAlternatingRowColors(False)` sur TOUTES les tables | 🔴 P0 |
| R11 | Pas d'arithmétique token + littéral | `ds.sp(XXL) + 34` | `ds.sp(XXL) + ds.sp(LG)` — jamais `+ 34` | 🟡 P1 |

### 2.2 R12 — Valeurs autorisées (exceptions)

| Valeur | Justification |
|---|---|
| `0` ou `0px` | Le zéro est universel : aucun espacement, aucun décalage |
| `1` ou `1px` | Séparateurs fins (bordures 1px, hairlines) |
| `17` | Rayon de `M3ProfileButton` 34×34 : cercle parfait, `34 / 2` |

Toute autre valeur littérale est un défaut R, sans discussion.

### 2.3 R13 — Référence du linter

```bash
python scripts/lint_qss_hardcoding.py                              # Audit des 5 projets
python scripts/lint_qss_hardcoding.py --dir .\LarcSuperviseur       # Projet unique
python scripts/lint_qss_hardcoding.py --fix                         # Auto-correction des valeurs triviales
python scripts/lint_qss_hardcoding.py --threshold P0                # Seulement les P0
python scripts/lint_qss_hardcoding.py --json                        # Sortie JSON (CI)
```

### 2.4 R14 — Table de correspondance Valeur → Token (canonique, 24 valeurs)

Utilisée par `--fix` et par les développeurs. Quand vous hésitez : cherchez le px ici.

| px | Token espacement | Token forme | Token image | Token police |
|---|---|---|---|---|
| 4 | `ds.space_xxs` | `ds.radius_xs` | — | — |
| 6 | ❌ INTERDIT | ❌ INTERDIT | — | — |
| 8 | `ds.space_xs` | `ds.radius_sm` | — | — |
| 10 | — | — | — | `s(10)` |
| 12 | `ds.space_sm` | `ds.radius_md` | — | `s(12)` |
| 14 | — | — | — | `s(14)` |
| 16 | `ds.space_m3` | `ds.radius_lg` | — | — |
| 18 | — | — | `theme_manager.image.icon_btn` | `s(18)` |
| 20 | `ds.space_md` | — | — | — |
| 21 | — | — | — | `s(21)` / `ds.table_row_min` |
| 24 | — | — | — | `s(24)` |
| 28 | — | `ds.radius_xl` | — | `s(28)` |
| 32 | `ds.space_lg` | — | — | `s(32)` |
| 34 | — | — | `theme_manager.image.theme_btn` | — |
| 36 | — | — | — | `s(36)` |
| 40 | — | — | hauteur bouton M3 | — |
| 52 | `ds.space_xl` | — | `ds.button_height` | — |
| 55 | — | — | `theme_manager.image.logo_small` | — |
| 84 | `ds.space_xxl` | — | — | — |
| 89 | — | — | `theme_manager.image.logo` | — |
| 100 | — | — | `theme_manager.image.add_btn` | — |
| 136 | `ds.space_xxxl` | — | — | — |
| 150 | — | — | `theme_manager.image.avatar` | — |
| 233 | — | — | `ds.sidebar_width` | — |

**IMPORTANT :** `ds.field_height` = 32px, `ds.button_height` / `ds.header_height` = 52px,
`ds.table_row_min` = 21px.

### 2.5 R15 — Sortie attendue du linter ("conforme")

```bash
$ python scripts/lint_qss_hardcoding.py --dir .\LarcSuperviseur
RÉSULTAT : 0 hardcodings sur 24 fichiers — FÉLICITATIONS ✅
```

Toute autre sortie (hardcodings listés, seuil non atteint) = CI rouge.

### 2.6 R16 — Règle du viewport transparent (QScrollArea)

Tout `QScrollArea` / `M3ScrollArea` DOIT avoir un viewport transparent, sinon le
fond QSS du parent n'est pas peint (fond gris Qt par défaut).

**Cas héritage**

```python
class NotesScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().setStyleSheet("background: transparent;")
```

**Cas composition**

```python
self.scroll = M3ScrollArea(self)
self.scroll.viewport().setStyleSheet("background: transparent;")
```

**Cas factorisé (LarcCommon)** — l'encapsuler dans le widget de base :

```python
class LarcScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewport().setStyleSheet("background: transparent;")
```

### 2.7 Sous-système I — Anti-patterns visuels (I1-I9)

| # | Anti-pattern | ❌ Interdit | ✅ Requis |
|---|---|---|---|
| I1 | PNG/JPG comme icônes | `QPixmap("icon.png")` | `md3_icon("home")` (SVG MD3) |
| I2 | Hex en dur dans `setStyleSheet` | `background: #6750A4` | helper `ds` ou token palette |
| I3 | `setFixedHeight(32)` | `setFixedHeight(32)` | `setFixedHeight(ds.field_height)` |
| I4 | `setSpacing(6)` | `setSpacing(6)` | `setSpacing(ds.space_sm)` |
| I5 | `setContentsMargins(6,6,6,6)` | `setContentsMargins(6,6,6,6)` | `setContentsMargins(ds.space_sm, ...)` |
| I6 | `setFixedWidth(233)` | `setFixedWidth(233)` | `setFixedWidth(ds.sidebar_width)` |
| I7 | Changement de couleur au hover | `color: red` sur `:hover` | State layer overlay M3 (L1) |
| I8 | Bordure pour séparer les surfaces | `border: 1px solid` partout | Élévation M3 (L2) |
| I9 | `QWidget()` nu qui ne peint pas le fond QSS | `QWidget()` dans une vue Larc | `ThemedWidget()` |

### 2.8 Sous-système L — Philosophie de design (Hybride M3 + Fibonacci)

| Domaine | Source | Détail |
|---|---|---|
| Couleurs | M3 | Schéma tonal complet (Material You) |
| Typographie | M3 | Échelle type `s()` : 10-14-16-18-21-24-28-32-36 |
| State layers | M3 | Overlays de transparence (L1) |
| Formes | M3 | Rayons : 4-8-12-16-28 |
| Espacements | Fibonacci×4 + M3×8 | `ds.space_*` : 4-8-12-20-32-52-84-136 |
| Proportions | Nombre d'or | φ pour tailles, ratios, vignettes |
| Élévation | M3 | Niveaux 0-5 (L2) |
| Séparation des surfaces | **Bordure (choix Larc)** | Décision volontaire : lisibilité sur écrans pro |
| Forme des boutons | Compromis | Rayon 16px (ni plein cercle M3, ni carré) |

**L1 — State layers M3** (overlays de transparence, jamais de changement de couleur) :
hover 8 %, focus 10 %, pressed 12 %, drag 16 %. Le widget superpose le calque sur la
couleur de surface existante — c'est la solution à I7.

**L2 — Élévation M3** (niveaux 0-5) :
- **Quand utiliser l'élévation** : surfaces flottantes (menus, popups, dialogs, snackbar,
  cartes empilées) — `elevation` 1-3, FAB et menus 4-5.
- **Quand utiliser la bordure (choix Larc)** : séparation de surfaces dans une même
  zone statique (tables, panneaux d'édition) — une bordure 1px + élévation 0.
- Interdit : élévation ET bordure sur la même surface.

## 3. Code complet

*(Voir les tables de règles R1-R16 et R14 dans la section 2 pour le code de référence.)*

## 4. Exemples (code LarcProf réel)

### 3.1 Bouton de connexion — `LarcProf/views/login.py`

```python
# ❌ AVANT
self.btn_login.setFixedHeight(52)
self.btn_login.setStyleSheet("border-radius: 26px; background: #6750A4;")

# ✅ APRÈS
self.btn_login.setFixedHeight(ds.button_height)
self.btn_login.setStyleSheet(
    f"border-radius: {ds.radius_xl}px; background: {palette.primary};"
)
```

### 3.2 Tableau des salariés — `LarcProf/views/employees.py`

```python
# ❌ AVANT
self.table = M3TableWidget(self)
self.table.setAlternatingRowColors(True)   # R10 : P0

# ✅ APRÈS
self.table = M3TableWidget(self)
self.table.setAlternatingRowColors(False)  # séparation par bordure L2
```

### 3.3 Page des congés — `LarcProf/views/leave.py`

```python
# ❌ AVANT
layout.setContentsMargins(8, 8, 8, 8)
layout.setSpacing(6)
self.scroll.setFixedWidth(233)

# ✅ APRÈS
layout.setContentsMargins(ds.space_xs, ds.space_xs, ds.space_xs, ds.space_xs)
layout.setSpacing(ds.space_xs)
self.scroll.setFixedWidth(ds.sidebar_width)
self.scroll.viewport().setStyleSheet("background: transparent;")  # R16
```

### 3.4 Icône du menu — `LarcProf/views/menu.py`

```python
# ❌ AVANT
self.btn.setIcon(QIcon("assets/parametres.png"))   # I1

# ✅ APRÈS
self.btn.setIcon(md3_icon("settings"))
```

## 5. Step by Step — Outillage

### 4.1 Intégration pre-commit

```yaml
- id: lint-rlinter
  name: 🔬 Linter QSS Larc (R + Q1+Q3 + Q2)
  entry: python C:/projets/scripts/lint_qss_hardcoding.py --fix-only
  language: system
  files: \.py$
  stages: [pre-commit]
  verbose: true
  pass_filenames: false
```

### 4.2 Flux recommandé

1. Écrire avec les tokens dès le départ (design-tokens pour les valeurs).
2. `python scripts/lint_qss_hardcoding.py --dir .` avant tout commit.
3. `--fix` pour les valeurs triviales, correction manuelle sinon.
4. En CI : `--threshold P0 --json` → la sortie R15 doit être conforme.

## 6. Checklist

- [ ] `python scripts/lint_qss_hardcoding.py --dir .\LarcProf` → `RÉSULTAT : 0 hardcodings`
- [ ] `python scripts/lint_qss_hardcoding.py --dir .\LarcSuperviseur` → `0 hardcodings`
- [ ] `python scripts/lint_qss_hardcoding.py --dir .\LarcFacture` → `0 hardcodings`
- [ ] `python scripts/lint_qss_hardcoding.py --dir .\LarcStock` → `0 hardcodings`
- [ ] `python scripts/lint_qss_hardcoding.py --dir .\LarcCompta` → `0 hardcodings`
- [ ] `grep -rn "setAlternatingRowColors(True)" LarcProf LarcCommon` → aucune sortie
- [ ] `grep -rnE "#[0-9A-Fa-f]{6}" LarcProf --include=*.py` → aucune sortie hors helpers
- [ ] `grep -rn "setFixedHeight(\d)" LarcProf` → aucune sortie (R5)
- [ ] `grep -rn "setFixedWidth(\d)" LarcProf` → aucune sortie (R6)
- [ ] `grep -rn "setSpacing(\d)" LarcProf` → aucune sortie (R8)
- [ ] `grep -rn "QScrollArea\|M3ScrollArea" LarcProf` → chaque occurrence a un
      `viewport().setStyleSheet("background: transparent;")` associé (R16)
- [ ] `grep -rn "setMinimumSize\|setMaximumSize" LarcProf` → aucune sortie (R9b)
- [ ] Tout `QWidget()` nu remplacé par `ThemedWidget()` (I9)
- [ ] Aucune couleur hex en dur dans les `setStyleSheet` des vues (I2)
- [ ] Aucune icône PNG/JPG référencée dans les vues (I1)
- [ ] Aucune arithmétique `ds.* + <littéral>` (R11)
- [ ] Les seules valeurs littérales présentes : `0`, `1`, `17` sur M3ProfileButton (R12)

## Références croisées

| Skill | Lien |
|---|---|
| `design-tokens` | Valeurs de remplacement canoniques de tous les tokens `ds.*` / `s()` / `theme_manager.image.*` |
| `color-rules` | Tokens de couleur : jamais d'hex, palette M3 uniquement |
| `theme-reactivity` | J7 / ThemedWidget : widgets réactifs au changement de thème (complément du R16 et de I9) |

---

*Version 1.0 — Règle absolue du projet Larc ERP. Aucune exception hors R12.*
