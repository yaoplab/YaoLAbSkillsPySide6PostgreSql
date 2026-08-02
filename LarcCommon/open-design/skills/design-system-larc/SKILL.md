# ⚠️ DEPRECATED — Skill Design System Larc

**Ce skill a été divisé en 6 skills spécialisés le 2026-08-02.**
Voir **[INDEX.md](../INDEX.md)** pour l'architecture complète.

Nouveaux skills :
- **[design-tokens](../design-tokens/SKILL.md)** — Sous-systèmes A, B, C, E, G, R14, R17
- **[color-rules](../color-rules/SKILL.md)** — Sous-systèmes D, D1-D7, P
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Sous-systèmes J, N
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — Sous-systèmes R, I, L
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — Sous-système K
- **[ergonomics](../ergonomics/SKILL.md)** — Sous-système Q

Le contenu ci-dessous est conservé pour référence historique.

---

# Skill: Design System Larc (DÉPRÉCIÉ)

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Design, Docs, Hub)
**Module** : `LarcCommon/larccommon/design_system.py`
**Utilisateurs** : Tous les développeurs Larc
**Dépendances** : `PySide6>=6.5`, `LarcCommon/larccommon/theme.py`, `LarcCommon/larccommon/icons.py`

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Code PySide6 avec des valeurs de padding, spacing, margin, hauteurs, couleurs en dur
**Sortie** : Code utilisant uniquement les tokens du Design System (`ds.space_*`, `ds.p.*`, `ds.*`)
**Traitement** : Remplacer toute valeur littérale par le token correspondant

## 2. Contraintes Fondamentales

| # | Contrainte | Gravité |
|---|---|---|
| C1 | **ZÉRO hardcoding** de padding, margin, spacing — toujours `ds.space_*` | 🔴 Bloquant |
| C2 | **ZÉRO hardcoding** de couleurs — toujours `ds.p.*` (palette) | 🔴 Bloquant |
| C3 | **ZÉRO hardcoding** de hauteurs/largeurs — toujours `ds.field_height`, `ds.button_height`, etc. | 🟡 Important |
| C4 | **ZÉRO `border-radius` en dur** — toujours `ds.radius_*` | 🟡 Important |
| C5 | **ZÉRO `font-size` en dur** — utiliser les tokens typo | 🟡 Important |
| C6 | **ZÉRO image PNG/JPG comme icône** — utiliser `md3_icon()` avec icônes MD3 vectorielles | 🔴 Bloquant |

### Sous-système A — Tokens d'espacement (Fibonacci × 4 + M3 × 8)

**Principe** : Grille hybride. Fibonacci ×4 pour la hiérarchie visuelle (échelle exponentielle ×φ ≈ 1.618).
M3 ×8 pour les valeurs standard (compatibilité M3). Les deux systèmes sont compatibles car 4 et 8
sont sur la même grille de base 4px.

```python
ds.space_xxs   # 4px   — Fibo (gap minimum : icône-texte, inner padding)
ds.space_xs    # 8px   — Fibo ∩ M3 (gap standard : entre composants alignés)
ds.space_sm    # 12px  — Fibo (espacement entre sections proches)
ds.space_m3    # 16px  — M3 uniquement (card padding, dialog padding, champ padding)
ds.space_md    # 20px  — Fibo (espacement de section moyen)
ds.space_lg    # 32px  — Fibo ∩ M3 (espacement large : sections éloignées)
ds.space_xl    # 52px  — Fibo (très large : groupes de sections)
ds.space_xxl   # 84px  — Fibo (énorme : marges de page)
ds.space_xxxl  # 136px — Fibo (géant : hero sections)
```

**RÈGLE ABSOLUE** : `d.spacing = 6` est INTERDIT car n'appartient à AUCUN système.
**✅ Bon** : `setSpacing(ds.space_xs)` (= 8px, M3 standard) ou `setSpacing(ds.space_sm)` (= 12px, Fibo)
**✅ Bon** : `setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)`

**Guide de choix** :
| Usage | Token | Valeur | Justification |
|---|---|---|---|
| Gap icône-texte dans un bouton | `ds.space_xxs` | 4px | Fibo min, M3 dense |
| Gap entre champs d'un formulaire | `ds.space_xs` | 8px | M3 standard |
| Gap composants dans une section | `ds.space_sm` | 12px | Fibo, plus aéré que 8px |
| Padding d'une Card M3 | `ds.space_m3` | 16px | M3 card padding officiel |
| Gap entre sections | `ds.space_md` | 20px | Fibo, nettement distinct |
| Margin de page | `ds.space_lg` | 32px | Les deux systèmes |

### Sous-système B — Tokens de hauteurs

```python
ds.field_height    # 32px (hauteur des champs de saisie) — = ds.space_lg
                   # ⚠️ PAS 52px (52 = button_height / header_height)
ds.button_height   # 52px (hauteur des boutons) — = ds.space_xl
ds.header_height   # 52px (hauteur des en-têtes) — = ds.space_xl
ds.table_row_min   # 21px (hauteur minimale des lignes tableau) — = font_size(13) × φ ≈ 21
                   # ⚠️ PAS 32px
ds.sidebar_width   # 233px (largeur de la barre latérale)
```

**RÈGLE** : Ne JAMAIS écrire `setFixedHeight(52)` ou `setFixedWidth(233)`.
**✅ Bon** : `setFixedHeight(ds.button_height)` (52px = boutons/en-têtes) ou `setFixedWidth(ds.sidebar_width)` (233px)
**⚠️ Attention** : `ds.field_height` = **32px** (champs) — ne PAS l'utiliser pour une hauteur de 52px.

### Sous-système C — Tokens de bordures (Shapes M3 complets)

```python
ds.border_width       # 1px (épaisseur de bordure standard)
ds.radius_none        # 0px (pas d'arrondi — tableaux, DataTable)
ds.radius_xs          # 4px  (M3 shape-extra-small — TextField, SearchBar)
ds.radius_sm          # 8px  (M3 shape-small — Cards, Dialogs)
ds.radius_md          # 12px (M3 shape-medium — NavigationDrawer, Sheets)
ds.radius_lg          # 16px (M3 shape-large — Boutons Filled/Tonal, FAB)
ds.radius_xl          # 28px (M3 shape-extra-large — BottomNavigation, Pill)
```

**Guide d'affectation des shapes par composant :**

| Composant | Shape | Token |
|---|---|---|
| TextField, SearchBar | shape-extra-small | `ds.radius_xs` (4px) |
| Card (Elevated/Filled/Outlined) | shape-small | `ds.radius_sm` (8px) |
| Dialog, BottomSheet, NavigationDrawer | shape-medium | `ds.radius_md` (12px) |
| **Filled Button** | shape-large | `ds.radius_lg` (16px) — **pas pill** (20-28px) |
| FAB, Chip | shape-extra-large | `ds.radius_xl` (28px) |
| DataTable, ListItem | shape-none | `ds.radius_none` (0px) |

> **Note sur les boutons** : M3 utilise shape-extra-large (20-28px) pour les boutons, donnant un aspect
> "pill" arrondi. Larc utilise `ds.radius_lg` (16px) qui est un compromis entre M3 et un rendu plus
> compact adapté aux applications de gestion dense.

### Sous-système D — Tokens de couleurs (palette)

```python
ds.p.primary              # Couleur primaire
ds.p.on_primary           # Texte sur primaire
ds.p.primary_container    # Conteneur primaire
ds.p.secondary            # Couleur secondaire
ds.p.surface              # Surface
ds.p.background           # Fond
ds.p.error                # Erreur
ds.p.success              # Succès
ds.p.text_strong          # Texte principal
ds.p.text_soft            # Texte secondaire
ds.p.text_disabled        # Texte désactivé
ds.p.outline              # Bordure
ds.p.outline_variant      # Bordure variante
```

**RÈGLE** : Ne JAMAIS écrire `color: #1565C0` ou `background: #c0392b`.
**✅ Bon** : `color: {ds.p.primary}` ou `background: {ds.p.error}`

#### D1 — Règle d'attribution EXPLICITE des couleurs de texte

**Principe fondateur** : Tout texte affiché dans l'interface DOIT avoir sa couleur
EXPLICITEMENT définie via un token `{p.text_strong}` ou `{p.text_soft}`. **Ne JAMAIS
compter sur l'héritage** de la palette Qt, du QSS parent, ou du thème phibuilder.

**Pourquoi ?**

| Mécanisme | Problème constaté |
|---|---|
| Héritage QPalette::WindowText | Qt utilise **NOIR** par défaut — en mode dark, le texte devient illisible sur fond sombre |
| Héritage du QSS parent | La propriété `color:` n'est pas cascadée aux widgets enfants comme `QLabel` |
| HTML sans `color:` (`<b>Nom</b>`) | Qt RichText utilise la couleur par défaut (NOIR), pas `p.text_strong` |
| phibuilder.setStyleSheet() | phibuilder ne définit pas la palette Qt complète — `WindowText` reste NOIR |

**Les 3 cas où la couleur DOIT être explicite :**

| # | Cas | ❌ Erreur | ✅ Correction |
|---|---|---|---|
| D1a | **QLabel RichText/HTML** | `<b style='font-size: 12px'>Nom</b>` | `<b style='font-size: 12px; color: {p.text_strong}'>Nom</b>` |
| D1b | **QSS de widget conteneur** (QFrame, StudentCard, etc.) | `StudentCard { background: {p.surface}; }` | `StudentCard { background: {p.surface}; color: {p.text_strong}; }` |
| D1c | **setStyleSheet inline** sur bouton/label | `color: #1565C0` | `color: {p.primary}` |

**Pattern QSS obligatoire pour tout widget conteneur :**

```python
# ✅ TOUJOURS inclure color: dans le QSS du widget parent
self.setStyleSheet(f"""
    StudentCard {{
        background: {p.surface};
        color: {p.text_strong};           /* ← OBLIGATOIRE : héritage pour les labels enfants */
        border: 1px solid {p.outline_variant};
    }}
    StudentCard:hover {{
        background: {p.surface_variant};
        color: {p.text_strong};           /* ← OBLIGATOIRE aussi au hover */
    }}
""")
```

**Pattern HTML obligatoire pour tout QLabel avec RichText :**

```python
# ✅ TOUJOURS inclure color: dans les balises HTML
self._name_label.setText(f"""
    <b style='font-size:{s(14)}px; color:{p.text_strong}'>{last_name}</b><br>
    <span style='font-size:{s(14)}px; color:{p.text_soft}'>{first_name}</span>
""")
```

**RÈGLE ABSOLUE** : Tout `QLabel.setText()` avec HTML, tout `setStyleSheet()` sur un widget
conteneur, et tout QSS inline DOIT inclure `color:` avec un token de la palette.

**Sanction** : Si un texte est noir en mode dark, c'est qu'il manque une couleur explicite
quelque part — appliquer D1a, D1b ou D1c selon le cas.

#### D2 — Script de vérification automatique D1 + J7 + D3 + D4

Un linter dédié vérifie automatiquement les règles D1, J7, D3 ET D4 :

```bash
# Audit complet (D1 + J7 + D3 + D4) — tous les projets Larc
python scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4

# Audit D1+J7 par défaut (défaut)
python scripts/lint_d1_color_checker.py

# Un seul projet
python scripts/lint_d1_color_checker.py --dir .\LarcSuperviseur

# Audit complet (TOUTES les règles) — CI / pre-commit
python scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7

# Règles individuelles
python scripts/lint_d1_color_checker.py --rule D1      # setText() HTML sans color:
python scripts/lint_d1_color_checker.py --rule J7      # Widgets sans WA_StyledBackground
python scripts/lint_d1_color_checker.py --rule D3      # Hex hardcodés dans setStyleSheet()
python scripts/lint_d1_color_checker.py --rule D4      # Contrastes insuffisants (D4a/D4b)
python scripts/lint_d1_color_checker.py --rule D5      # text_soft dans setStyleSheet() inline
python scripts/lint_d1_color_checker.py --rule D6      # Palette sans theme_changed ni restyle-hook
python scripts/lint_d1_color_checker.py --rule D7      # _restyle() incomplet vs builder

# Mode compact (seulement les fichiers et lignes)
python scripts/lint_d1_color_checker.py --fix-only

# Sortie JSON
python scripts/lint_d1_color_checker.py --json
```

**Ce que détecte le script :**

| Règle | Détection | Exemple de violation |
|---|---|---|
| **D1** | `setText()` HTML sans `color:` explicite | `<b>Nom</b>` (manque `color:{p.text_strong}`) |
| **D1** | Certaines balises ont `color:` mais d'autres non | `<b style='color:...'>OK</b><span>PAS OK</span>` |
| **J7** | `M3Frame` / `QWidget` / `QFrame` avec `background:` QSS mais sans `setAttribute(Qt.WA_StyledBackground, True)` | `card = M3Frame()` + `card.setStyleSheet("background:...")` sans `card.setAttribute(Qt.WA_StyledBackground, True)` |
| **D3** | Couleurs hex hardcodées (`#RRGGBB`, `#RGB`) dans `setStyleSheet()` | `setStyleSheet("background: #3498db; color: white;")` au lieu de `f"background: {p.primary};"` |
| **D4a** | `font-size < 12px` AVEC `color: text_soft` → contraste insuffisant en dark | `font-size: {s(10)}px; color: {p.text_soft}` → utiliser `text_strong` |
| **D4b** | `background: surface_variant` AVEC `color: text_soft` → gris sur gris en dark | `background: {p.surface_variant}; color: {p.text_soft}` → utiliser `text_strong` |
| **D5** | `color: {p.text_soft}` dans `setStyleSheet()` **inline** (hors `_STYLE` property) — gris sur gris en dark | `lbl.setStyleSheet(f"...color: {p.text_soft}...")` → `text_strong` |
| **D6** | Classe utilisant des tokens palette dans `setStyleSheet()` sans `theme_changed.connect` NI hook de restyle → ne réagit pas au changement de thème | classe avec `setStyleSheet(f"...{p.primary}...")` mais ni `theme_changed.connect(self._restyle)` ni `def _restyle/restyle/refresh_theme/_update_style` |
| **D7** | `_restyle()` ne met pas à jour tous les widgets stylés avec palette (détecte les oublis) | widgets avec `self._x.setStyleSheet(f"...{p.xxx}...")` dans le builder mais absents du `_restyle()` |

**D6 — exemptions architecturales (documentées) :**
- **Infrastructure de thème** : `ThemeManager`, `QssHelper`, `ThemeManagerWrapper` — ils *génèrent* le QSS, pas des widgets.
- **Objets éphémères** : classes héritant de `M3Dialog`/`QDialog`/`QStyledItemDelegate` — palette lue à la construction, recréées à chaque ouverture.
- **Écrans de login** (`LoginWindow`) — thème figé avant l'affichage, pas de bascule.
- **Hook de restyle présent** : `def _restyle`, `def restyle`, `def _restyle_all`, `def refresh_theme`, `def _update_style`, `def _apply_style`, `def _STYLE` — pattern « restyle piloté par le parent ». ⚠️ Les **properties** `_STYLE_ACTIF`/`_STYLE_INACTIF` ne comptent PAS comme hook : un widget qui ne fait que définir des properties `_STYLE_*` sans `restyle()`/`_restyle()` doit quand même être restylé par son parent.

**D7 — gestion des cas :**
- **Alias** : si `_restyle()` délègue à `_rebuild`/`_restyle_all`/`restyle`/`_update_style`/`refresh_theme`, le corps de la méthode appelée est aussi scanné.
- **Indirection de variable** : `qss = f"...{p.x}..."` puis `setStyleSheet(qss)` compte comme couvert (côté `_restyle`). ⚠️ Limite connue : l'indirection côté **builder** (`qss = f"...{p.x}..."; self._x.setStyleSheet(qss)` avant `_restyle`) n'est pas traquée — le widget ne sera pas signalé s'il manque au `_restyle`. Le garde-fou couvre le pattern le plus fréquent (f-strings inline) ; pour les builders par indirection, vérifier manuellement.
- **Variables locales** (sans `self.`) ignorées — uniquement les membres de classe doivent être restylés.

Le script gère :
- Les appels multi-lignes (f-strings sur plusieurs lignes)
- Les variables avec dot ( `self._var`, `obj.attr` )
- Les `setStyleSheet` multi-lignes avec `background:`
- Les tokens f-string `{p.xxx}` nettoyés avant analyse (évite les faux positifs)
- Le comptage précis des parenthèses depuis la position exacte de `setStyleSheet(` (pas le premier `(` de la ligne)
- Les regex D4 sans mode `(?x)` problématique pour une correspondance fiable

**Fichier** : `scripts/lint_d1_color_checker.py`

**RÉFÉRENCE** : Script conforme aux règles D1, J7, D3 et D4 du skill design-system-larc.

### Sous-système E — Tokens d'icônes

```python
# Icônes MD3 vectorielles via larccommon.icons
ds.icon_sm    # 20px (petite icône — boutons, menus)
ds.icon_md    # 32px (icône moyenne — items de liste)
ds.icon_lg    # 52px (grande icône — headers, cards)

# Usage
from larccommon.icons import icon as md3_icon
md3_icon('refresh', color=ds.p.primary, size=ds.icon_sm)  # → QIcon

# Tailles via theme_manager (alternative recommandée)
theme_manager.image.icon_btn      # 18px (boutons)
theme_manager.image.icon_menu     # 18px (menus)
theme_manager.image.icon_large    # 32px (grands boutons)
theme_manager.image.theme_btn     # 34px (boutons de thème)
theme_manager.image.profile_btn   # 34px (avatar)
theme_manager.image.avatar        # 150px (photo profil)
theme_manager.image.photo         # 150px (photo élève)
```

**RÈGLE** : Icônes SVG Material Design 3 uniquement — **INTERDICTION** des images PNG/JPG comme icônes.
**✅ Bon** : `md3_icon('refresh', color=ds.p.primary, size=theme_manager.image.icon_btn)`
**✅ Bon** : `theme_manager.image.avatar` pour les photos

### Sous-système F — QSS Helpers

```python
ds.flat_input_qss()    # QSS complet pour QLineEdit
ds.table_qss()         # QSS complet pour M3TableWidget
ds.panel_qss()         # QSS complet pour QFrame (panels)
ds.label_qss()         # QSS complet pour QLabel
```

**RÈGLE** : Privilégier les helpers QSS plutôt que du QSS inline.

### Sous-système G — Typographie (Échelle M3 complète)

**Principe** : Échelle typographique M3 complète, de `label-small` (11px) à `display-large` (57px).
Utiliser `theme_manager.font_size(N)` pour mettre à l'échelle avec le multiplicateur du thème actif.

```python
# Échelle M3 complète (tailles de base × multiplicateur du thème)
theme_manager.font_size(11)  # label-small   — badges, timestamps, metadata
theme_manager.font_size(12)  # body-small    — texte secondaire, légendes
theme_manager.font_size(13)  # label-large   — boutons, list items, étiquettes
theme_manager.font_size(14)  # body-medium   — corps de texte standard (DEFAULT)
theme_manager.font_size(16)  # title-medium  — titres de section, cards
theme_manager.font_size(18)  # title-large   — titres de page, headlines
theme_manager.font_size(22)  # headline-small — héros, pages d'accueil
theme_manager.font_size(28)  # headline-medium — grands titres
theme_manager.font_size(36)  # headline-large — KPIs, chiffres clés
theme_manager.font_size(45)  # display-small  — très grands chiffres
theme_manager.font_size(57)  # display-large — hero (rare)
```

**Guide d'usage par composant :**

| Composant | Token M3 | Taille | Usage |
|---|---|---|---|
| Badge, tag, metadata | `label-small` | `s(11)` | Badge statut, timestamps |
| Légende, aide, note | `body-small` | `s(12)` | Infobulles, hints |
| **Bouton, item de liste** | **`label-large`** | **`s(13)`** | **Tous les boutons, cellules** |
| **Corps de texte** | **`body-medium`** | **`s(14)`** | **Texte standard, labels de champ** |
| Titre de section | `title-medium` | `s(16)` | En-têtes de panel, titres de card |
| Titre de page | `title-large` | `s(18)` | Titre de fenêtre, dashboard |
| Héro secondaire | `headline-small` | `s(22)` | Grand titre, page d'accueil |
| KPI, chiffre clé | `headline-medium` | `s(28)` | Chiffres du dashboard |
| Très grand chiffre | `headline-large` | `s(36)` | KPIs principaux |

**RÈGLE** : Ne JAMAIS écrire `font-size: 20px` ou `font-size: 14px` en dur.
**✅ Bon** : `font-size: {theme_manager.font_size(14)}px` ou `s(14)` si importé

**Rappel** : Les polices actuelles (10-13px) sont en cours de migration vers l'échelle M3 (11-57px).
Les tailles 10px et 11px sont acceptées temporairement pour le sidebar dense.

### Sous-système H — Audit padding/margin

| Projet | Hardcodings | Priorité |
|---|---|---|
| LarcProf | ~57 hardcodings QSS, 30 margins, 43 spacing | 🔴 Urgent |
| LarcSuperviseur | ~25 hardcodings | 🟡 À corriger |
| LarcSecretaire | ~11 hardcodings QSS, 10 margins, 18 spacing | 🟡 À corriger |
| LarcHub | ~5 hardcodings | 🟢 Faible |
| LarcDesign | ~3 hardcodings | 🟢 Faible |

**Fichier de référence** : `LarcSecretaire/views/parent_manager.py` — **0 hardcoded** ✅

### Sous-système P — Couleurs des programmes (PEI, MYP, DP, DPEn)

**Principe** : Les couleurs affectées aux 4 programmes (PEI, MYP, DPFr, DPEn) sont
**centralisées** dans `larccommon.theme.PROGRAM_STYLES` et utilisent des **noms de rôles**
M3 (pas des couleurs hex). Cela garantit que tous les modules Larc (Superviseur, Secretaire,
Prof) utilisent exactement les mêmes couleurs, quel que soit le thème actif.

#### P1 — Table des couleurs par programme

| Programme | Rôle fg (solide) | Rôle bg (container) | Rôle on_fg (texte) | Sens |
|---|---|---|---|---|
| **PEI** | `primary` | `primary_container` | `on_primary` | Premier cycle, prioritaire |
| **MYP** | `secondary` | `secondary_container` | `on_secondary` | Deuxième cycle, complémentaire |
| **DPFr** | `error` | `error_container` | `on_error` | Attention, distingué (rouge) |
| **DPEn** | `tertiary` | `tertiary_container` | `on_tertiary` | Bilingue, tertiaire (orange) |

> **Pourquoi ces affectations ?**
> - PEI = `primary` car c'est le programme le plus représenté (collège)
> - MYP = `secondary` car c'est le second programme du collège
> - DPFr = `error` (rouge) pour attirer l'attention sur ce programme exigeant
> - DPEn = `tertiary` (orange) pour le programme bilingue, distinct mais pas critique

#### P2 — Code centralisé (larccommon.theme)

```python
# Ne JAMAIS redéfinir ce dict dans les apps — toujours importer PROGRAM_STYLES
PROGRAM_STYLES: dict[str, tuple[str, str, str]] = {
    "PEI":  ("primary",   "primary_container",   "on_primary"),
    "MYP":  ("secondary", "secondary_container",  "on_secondary"),
    "DPFr": ("error",     "error_container",      "on_error"),
    "DPEn": ("tertiary",  "tertiary_container",   "on_tertiary"),
}
```

Les **noms de rôles** sont résolus dynamiquement via `getattr(p, role_name)` où `p`
est la palette active. Par exemple, `"primary"` devient `p.primary` qui vaut `#1565C0`
en bleu, `#64B5F6` en dark, etc.

#### P3 — Utilisation standard

```python
from larccommon.theme import PROGRAM_STYLES

# Dans SidebarWidget
sidebar = SidebarWidget(sections, PROGRAM_STYLES)

# Dans _rebuild (SidebarWidget._resolve_colors)
fg_role, bg_role, on_fg_role = PROGRAM_STYLES["PEI"]
p = theme_manager.palette
fg = getattr(p, fg_role)     # → p.primary = "#1565C0" (bleu) ou "#64B5F6" (dark)
bg = getattr(p, bg_role)     # → p.primary_container
on_fg = getattr(p, on_fg_role)  # → p.on_primary
```

#### P4 — Règles absolues

| # | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|
| P4a | Définir `prog_style` en dur dans chaque app | Importer `PROGRAM_STYLES` depuis `larccommon.theme` | 🔴 Bloquant |
| P4b | Mettre des couleurs hex dans `prog_style` | Utiliser des **noms de rôles** (primary, secondary, etc.) | 🔴 Bloquant |
| P4c | Modifier PROGRAM_STYLES dans une app | Le modifier UNIQUEMENT dans `larccommon/theme.py` | 🔴 Bloquant |
| P4d | Ajouter un nouveau programme sans l'ajouter à PROGRAM_STYLES | Ajouter le programme dans PROGRAM_STYLES + documenter dans ce skill | 🟡 Important |

#### P5 — Comment sont résolues les couleurs dans SidebarWidget

Le SidebarWidget ne manipule JAMAIS de couleurs hex. Il stocke les noms de rôles et
les résout via `_resolve_colors()` :

```python
def _resolve_colors(self, fg_role: str, bg_role: str, on_fg_role: str) -> tuple[str, str, str]:
    """Résout les noms de rôles en couleurs actuelles depuis la palette active."""
    p = theme_manager.palette
    return (getattr(p, fg_role), getattr(p, bg_role), getattr(p, on_fg_role))
```

Cette méthode est appelée à chaque `_rebuild()`, donc les couleurs suivent
automatiquement le thème actif sans aucun effort supplémentaire.

### Sous-système I — Anti-patterns visuels

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| I1 | Images PNG/JPG comme icônes | Icônes MD3 vectorielles via `md3_icon()` |
| I2 | `setStyleSheet` avec valeurs hex en dur | `setStyleSheet(ds.flat_input_qss())` ou template avec `{ds.p.*}` |
| I3 | `setFixedHeight(32)` en dur | `setFixedHeight(ds.field_height)` |
| I4 | `setSpacing(6)` en dur | `setSpacing(ds.space_sm)` |
| I5 | `setContentsMargins(6,6,6,6)` | `setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)` |
| I6 | `setFixedWidth(233)` en dur | `setFixedWidth(ds.sidebar_width)` |
| I7 | **Hover : changement de couleur** (ex: `background: {p.primary_container}`) | **State layer** : overlay semi-transparent sur la couleur d'origine | Voir Sous-système L |
| I8 | **Bordure pour séparer les surfaces** (`border: 1px solid outline`) | **Élévation** : `ds.elevation(level)` avec niveau 0-5 | Voir Sous-système L |
| I9 | **`QWidget()` ou `QDialog()` ne peignant pas le fond QSS** | **`ThemedWidget()` / `ThemedDialog()`** de `larccommon.widgets.themed_widget` | Active `WA_StyledBackground` + `AutoFillBackground` automatiquement |

### Sous-système L — M3+Fibonacci : Philosophie du design hybride

**Principe fondateur** : Larc combine Material Design 3 (couleurs, typographie, états) avec
Fibonacci ×4 (espacements harmonieux) et le Ratio d'Or (proportions). C'est un choix délibéré :

| Domaine | Source | Pourquoi |
|---|---|---|
| 🎨 **Couleurs** | M3 (rôles, noms, dark/light) | Standard universel, accessibilité |
| 🔤 **Typographie** | M3 (échelle 11-57px) | Lisibilité prouvée |
| 🎭 **State layers** | M3 (hover/focus/pressed par overlay) | Préserve la couleur d'origine |
| 📐 **Shapes** | M3 (noms, affectations) | Cohérence des coins arrondis |
| 📏 **Espacements** | **Fibonacci ×4 + M3 ×8** (hybride) | Rythme harmonieux × hiérarchie claire |
| 🏛️ **Proportions** | Ratio d'Or (φ ≈ 1.618) | Découpage naturel œil humain |
| 🏔️ **Élévation** | M3 (niveaux 0-5) | Profondeur visuelle |
| 🔲 **Séparation surfaces** | **Bordures** (choix Larc) | UI plus propre pour data dense |
| 🔘 **Forme boutons** | **16px radius** (compromis M3+Fibo) | Pas pill (économise l'espace vertical) |

#### L1 — State Layers M3 (hover, focus, pressed)

M3 ne change PAS la couleur d'un composant au survol — il superpose un **calque semi-transparent**
(state layer) par-dessus la couleur d'origine.

```css
/* ❌ Mauvais : changement de couleur */
QPushButton:hover { background: #BBDEFB; }

/* ✅ M3 : state layer par dessus la couleur d'origine */
/* Le state layer est géré par QSS avec des pseudo-classes */
QPushButton:hover { background: rgba(255,255,255,0.08); }  /* hover = 8% white */
QPushButton:pressed { background: rgba(255,255,255,0.12); }  /* pressed = 12% */
```

**Opacités M3 des state layers :**

| État | Opacité | Code QSS |
|---|---|---|
| **Hover** | 8% | `rgba({couleur}, 0.08)` |
| **Focus** | 10% | `rgba({couleur}, 0.10)` |
| **Pressed** | 12% | `rgba({couleur}, 0.12)` |
| **Drag** | 16% | `rgba({couleur}, 0.16)` |

**💡 Règle pratique pour Larc** : Pour les boutons avec fond coloré, le state layer utilise
`on_primary` (blanc) en mode light, `on_primary` en mode dark. Pour les surfaces, utiliser `text_strong`.

```python
# ✅ State layer hover sur un bouton primaire
# Le fond reste p.primary, le state layer est un overlay blanc à 8%
f"QPushButton:hover {{ background: {p.primary}; }}"
# M3 pur utilisait : background: color-mix(in srgb, {p.primary} 92%, {p.on_primary} 8%)
```

> **Note pour l'implémentation** : Les state layers M3 purs nécessitent des `QGraphicsOpacityEffect`
> ou du `color-mix()` CSS (CSS Color Level 5). Dans QSS PySide6, on peut approximer avec des
> couleurs calculées. La priorité actuelle est sur l'harmonisation inter-apps — les state layers
> exacts seront implémentés dans une phase ultérieure.

#### L2 — Élévation M3 (niveaux 0-5)

`ds.elevation(level)` existe déjà dans `design_system.py`. Utilisation :

```python
# Appliquer une élévation sur un panel (remplace border)
panel = M3Frame()
panel.setObjectName("elevated_panel")
panel.setGraphicsEffect(ds.elevation(1))  # niveau 1 = ombre légère

# Niveaux d'élévation M3 :
# 0 = repos (aucune ombre)
# 1 = composants de surface (cards, panels)
# 2 = composants interactifs (boutons)
# 3 = composants temporaires (menus, tooltips)
# 4 = composants flottants (FAB, dialogs)
# 5 = composants modaux (bottom sheets, navigation drawers)
```

**Quand utiliser élévation vs bordure :**

| Contexte | Élévation | Bordure |
|---|---|---|
| Cards, panels interactifs | ✅ `ds.elevation(1)` | ❌ `border: 1px solid` |
| Dashboard, data display | ❌ (trop d'ombres = bruit) | ✅ `border: 1px solid outline_variant` |
| Dialog, menus, popups | ✅ `ds.elevation(3)` | ❌ |
| Sidebar, navigation | ❌ | ✅ `border-right` |
| Boutons, FAB | ✅ `ds.elevation(1-2)` | ❌ |
| Tableaux, listes denses | ❌ | ✅ (grille fine) |

### Sous-système K — Sidebar Visual Specification (PRÉCISE — rendu identique garanti)

| # | Règle | ❌ Interdit | ✅ Obligatoire | Raison |
|---|---|---|---|---|
| K1 | **Conteneur** | `M3Frame()` ou `QWidget()` | `M3ScrollArea` avec `setWidgetResizable(True)` + `setFrameShape(M3Frame.NoFrame)` | Le sidebar doit défiler si trop de classes |
| K2 | **Largeur** | `setFixedWidth(233)` ou largeur en pixels | `setFixedWidth(ds.sidebar_width)` | Token `ds.sidebar_width = 233` |
| K3 | **Marges layout** | `setContentsMargins(8,8,8,8)` | `setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)` | Espacement Fibonacci standard |
| K4 | **Spacing layout** | `setSpacing(6)` ou `setSpacing(ds.space_xxs)` | `setSpacing(theme_manager.design.spacing)` | `d.spacing = 6` (identique dans tous les thèmes) |
| K5 | **Fond du sidebar** | Inline QSS avec `background:` | `QssHelper.sidebar_container(p)` dans `_STYLE()` | Couleur surface + bordure droite |
| K6 | **En-tête section** (Collège/Lycée) | `M3Button(text)` SANS style ou avec `variant=TONAL` | `btn.setObjectName("sidebar_sec_hdr")` + `QssHelper.sidebar_section_header(p,d,s)` dans `_STYLE()` | Style flat divider : transparent + souligné 2px |
| K7 | **Hauteur en-tête section** | `setFixedHeight(34)` | **Pas de fixedHeight** — hauteur automatique via padding QSS | Le QSS `sidebar_section_header` gère le padding |
| K8 | **En-tête programme** (PEI/MYP/DP) | `M3Button(text)` avec fond `surface_variant` | `btn.setObjectName("sidebar_prog_hdr")` + `QssHelper.sidebar_program_header(p,d,s, fg, bg, on_fg)` | Couleur PLEINE du programme (primary/secondary/error/tertiary), hover = inversion vers `bg` |
| K9 | **Taille en-tête programme** | Pas de fixedSize | `setFixedSize(89, 21)` | **⚠️ EXCLUSIF au SidebarWidget** — 89px = `theme_manager.image.logo` — 21px = font_size(10) × φ ≈ 16 arrondi à 21. **HORS sidebar : interdits (utiliser `ds.table_row_min`/tokens)** |
| K10 | **Bouton classe** | Background `surface_variant` | `btn.setObjectName("sidebar_class_btn")` + `QssHelper.sidebar_class_button(p,d,s, bg, fg)` | Fond = container programme (primary_container/etc.) |
| K11 | **Taille bouton classe** | Pas de fixedSize | `setFixedSize(89, 34)` | **⚠️ EXCLUSIF au SidebarWidget** — 89px = `theme_manager.image.logo`, **34px = `theme_manager.image.theme_btn`**. **HORS sidebar : interdits (utiliser `ds.button_height`/tokens)** |
| K12 | **Checkable** | Pas de checkable | `btn.setCheckable(True)` | Le bouton classe doit pouvoir rester enfoncé |
| K13 | **Bouton Toutes classes** | Bouton TONAL ou absent | `btn.setObjectName("sidebar_all_btn")` + `QssHelper.sidebar_all_button(p,d,s)` | Fond primaire, hover → active, gras |
| K14 | **Hauteur Toutes classes** | Pas de fixedHeight | `setFixedHeight(55)` | 55px = SpacingToken.HUGE — visible et cliquable |
| K15 | **Couleurs programme** | `surface_variant` pour tout | DICT `prog_style = {"PEI": (p.primary, p.primary_container, p.on_primary), ...}` | Les 4 programmes ont leur propre couleur M3 |
| K16 | **Police en-tête section** | `s(13)`px ou défaut | `s(12)`px, bold | 12px gras standard pour titre de section |
| K17 | **Police en-tête programme** | `s(13)`px ou défaut | `s(10)`px, bold | 10px = petit, les en-têtes ne doivent pas dominer |
| K18 | **Police bouton classe** | `s(13)`px ou défaut | `s(10)`px | 10px = compact pour afficher toutes les classes |
| K19 | **Police Toutes classes** | `s(10)`px ou défaut | `s(11)`px, bold | 11px = légèrement plus grand, visible |
| K20 | **Border-radius** | `sp(SpacingToken.XXS)` ou `ds.radius_xs` | `d.radius`px (DesignToken.radius) | Les helpers `QssHelper.sidebar_*` utilisent `{d.radius}` |
| K21 | **Hover en-tête section** | Aucun hover | `QPushButton#sidebar_sec_hdr:hover { color: {p.primary}; border-bottom: 2px solid {p.primary}; }` | Souligné primaire au survol |
| K22 | **Hover bouton classe** | `background: {p.primary_container}` | **Inversion** fg↔bg : `background: {fg}; color: {bg};` | L'inversion fait ressortir la couleur programme |
| K23 | **Checked bouton classe** | Pas de checked ou style différent | `background: {fg}; color: {bg}; border: 2px solid {fg};` | Bouton enfoncé = plein + bordure |
| K24 | **QSS inline interdit** | `setStyleSheet(f"M3Button {{ background: {p.surface_variant}; ...}}")` | **Toujours** utiliser `QssHelper.sidebar_*()` | Les helpers sont la source unique de vérité |
| K25 | **Boutons icônes (Dashboard, Recherche, Parents)** | M3Button(variant=TONAL) | M3Button(variant=TONAL) avec icône MD3 | Ceux-ci peuvent rester TONAL — ce sont des actions, pas des classes |

**RÈGLE ABSOLUE** : Le sidebar doit être construit avec **EXACTEMENT** ce patron :

```python
# Le conteneur sidebar — hériter de M3ScrollArea OU utiliser un QScrollArea
class Sidebar(M3ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        self.setFrameShape(M3Frame.NoFrame)
        self.setFixedWidth(ds.sidebar_width)
        container.setObjectName("sidebar")  # ← QssHelper.sidebar_container()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
        self._layout.setSpacing(theme_manager.design.spacing)

    def _build_sections(self):
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size

        prog_style = {
            "PEI": (p.primary, p.primary_container, p.on_primary),
            "MYP": (p.secondary, p.secondary_container, p.on_secondary),
            "DPFr": (p.error, p.error_container, p.on_error),
            "DPEn": (p.tertiary, p.tertiary_container, p.on_tertiary),
        }

        for sec_name, columns in SECTIONS:
            # En-tête section — flat divider
            sec_hdr = M3Button(sec_name)
            sec_hdr.setObjectName("sidebar_sec_hdr")
            sec_hdr.setCursor(Qt.PointingHandCursor)
            sec_hdr.clicked.connect(...)
            layout.addWidget(sec_hdr)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                fg, bg, on_fg = prog_style[prog_key]

                # En-tête programme — couleur PLEINE
                col_hdr = M3Button(hdr_text)
                col_hdr.setObjectName("sidebar_prog_hdr")
                col_hdr.setFixedSize(89, 21)
                col_hdr.setCursor(Qt.PointingHandCursor)
                col_hdr.setStyleSheet(QssHelper.sidebar_program_header(p, d, s, fg, bg, on_fg))
                grd.addWidget(col_hdr, 0, col_idx)

                # Boutons de classe — couleur CONTAINER
                for i, (cid, label) in enumerate(items):
                    btn = M3Button(label)
                    btn.setObjectName("sidebar_class_btn")
                    btn.setFixedSize(89, 34)
                    btn.setCheckable(True)
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.setStyleSheet(QssHelper.sidebar_class_button(p, d, s, bg, fg))
                    btn.clicked.connect(...)
                    grd.addWidget(btn, i + 1, col_idx)

        # Bouton Toutes les classes
        self._all_btn = M3Button("Toutes les classes")
        self._all_btn.setObjectName("sidebar_all_btn")
        self._all_btn.setFixedHeight(55)
        self._all_btn.setCursor(Qt.PointingHandCursor)
        self._all_btn.setStyleSheet(QssHelper.sidebar_all_button(p, d, s))
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
```

**Prog_style — matrice des couleurs programme :**

| Programme | Token solide (fg) | Token container (bg) | Token texte (on_fg) |
|---|---|---|---|
| PEI | `p.primary` | `p.primary_container` | `p.on_primary` |
| MYP | `p.secondary` | `p.secondary_container` | `p.on_secondary` |
| DPFr | `p.error` | `p.error_container` | `p.on_error` |
| DPEn | `p.tertiary` | `p.tertiary_container` | `p.on_tertiary` |

**Checklist sidebar — rendu garanti identique :**

- [ ] Largeur = `ds.sidebar_width` (233px)
- [ ] Conteneur = `M3ScrollArea` avec `setObjectName("sidebar")`
- [ ] Sections : transparent + souligné 2px `outline_variant`, hover → `primary`
- [ ] Programmes : fond **couleur pleine** (primary/secondary/error/tertiary), pas `surface_variant`
- [ ] Classes : fond **container** (primary_container/etc.), pas `surface_variant`
- [ ] En-têtes programme : `setFixedSize(89, 21)`, police `s(10)`px bold
- [ ] Boutons classe : `setFixedSize(89, 34)`, police `s(10)`px, `setCheckable(True)`
- [ ] Border-radius : `d.radius`px via `QssHelper`
- [ ] Hover : inversion fg↔bg sur les classes, souligné primary sur les sections
- [ ] Checked : fond = fg, texte = bg, bordure 2px fg
- [ ] Bouton Toutes classes : fond `primary`, hover `active`, hauteur 55px
- [ ] 0 `setStyleSheet` inline — TOUT passe par `QssHelper.sidebar_*()`
- [ ] Le `_STYLE` property contient `QssHelper.sidebar_container(p)` ET tous les `QssHelper.sidebar_*`

### Sous-système J — Theme Reactivity (Pattern _STYLE + _restyle_all)

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| J1 | `theme=phi` sur les widgets phibuilder | Créer les widgets **sans** `theme=` (comme LarcSuperviseur) |
| J2 | `phi = theme_manager.phi_theme` capturé en locale | Utiliser `ds.phi` (property) si absolument nécessaire, ou **rien** |
| J3 | `setStyleSheet` avec hex en dur | `setStyleSheet(f"...{ds.p.primary}...")` — palette dynamique |
| J4 | Widget sans `setObjectName()` | **Toujours** `setObjectName("nom")` pour ciblage QSS global |
| J5 | `_restyle_all()` qui ne couvre pas tous les widgets | `_restyle_all()` complet : QSS global + chaque widget un par un |
| J6 | `theme_changed` non connecté | `ds.theme_changed.connect(self._restyle_all)` dans le `__init__` |
| J7 | **`QWidget()` / `QDialog()` sans `WA_StyledBackground`** | **`ThemedWidget(object_name=...)` / `ThemedDialog(object_name=...)`** de `larccommon.widgets.themed_widget` | Le QSS background ne s'affiche pas sans cet attribut dans Qt |

**Pattern de référence** (copié de LarcSuperviseur — le module correct) :

```python
class MaVue(QWidget):
    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle_all)
        self._init_ui()
    
    def _STYLE(self) -> str:
        """Property dynamique — évaluée à chaque appel avec la palette courante.
        Tous les widgets nommés via setObjectName() sont ciblés ici."""
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            QWidget#root {{ background: {p.background}; }}
            M3Label#panel_title {{
                font-size: {s(14)}px; font-weight: bold; color: {p.text_strong};
            }}
            M3Frame#panel {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: {d.radius_lg}px;
            }}
        """
    
    def _init_ui(self):
        self.setObjectName("root")
        self.setStyleSheet(self._STYLE())
        
        # Widgets SANS theme= — les styles viennent du QSS global
        self._title = M3Label("Titre")
        self._title.setObjectName("panel_title")  # ← ciblé par QSS
        
        self._panel = M3Frame()
        self._panel.setObjectName("panel")  # ← ciblé par QSS
    
    def _restyle_all(self):
        """Appelé quand ds.theme_changed est émis.
        Doit tout re-styler : QSS global + widgets individuels + icônes."""
        # 1. QSS global — couvre tous les widgets nommés
        self.setStyleSheet(self._STYLE())
        
        # 2. Widgets avec styles inline (non couverts par QSS)
        p = theme_manager.palette
        s = theme_manager.font_size
        self._widget_inline.setStyleSheet(
            f"color: {p.text_strong}; font-size: {s(12)}px;"
        )
        
        # 3. Icônes (couleur de la palette)
        self._theme_btn.setIcon(self._theme_icon())
```

## 3. Code complet

### Utilisation standard

```python
from larccommon.design_system import ds
from larccommon.icons import icon as md3_icon

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        p = ds.p
        layout = QVBoxLayout()
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_sm)
        
        field = QLineEdit()
        field.setFixedHeight(ds.field_height)
        field.setStyleSheet(ds.flat_input_qss())
        
        # Icône MD3
        icon = md3_icon('refresh', color=p.primary, size=theme_manager.image.icon_btn)
        
        table = M3TableWidget()
        table.setStyleSheet(ds.table_qss())
        table.horizontalHeader().setFixedHeight(ds.space_lg)
        
        self.setStyleSheet(f"""
            QWidget#panel {{
                background: {p.surface};
                border: {ds.border_width}px solid {p.outline_variant};
                border-radius: {ds.radius_sm}px;
                padding: {ds.space_md}px;
            }}
        """)
```

## 4. Exemples

### Exemple 1 — Correction d'un formulaire LarcProf (pire cas)

```python
# ❌ AVANT (hardcodé)
card_layout.setContentsMargins(6, 6, 6, 6)
card_layout.setSpacing(6)
field.setFixedHeight(32)
field.setStyleSheet("border: 1px solid #BDBDBD; border-radius: 4px; padding: 20px; color: #212121;")

# ✅ APRÈS (Design System)
layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
layout.setSpacing(ds.space_sm)
field.setFixedHeight(ds.field_height)
field.setStyleSheet(ds.flat_input_qss())
```

### Exemple 2 — Correction d'un panel LarcSuperviseur

```python
# ❌ AVANT
self._sidebar.setFixedWidth(233)
sidebar_layout.setContentsMargins(6, 6, 6, 6)

# ✅ APRÈS
self._sidebar.setFixedWidth(ds.sidebar_width)
sidebar_layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
```

## 5. Step by Step — Correction des applications

| Ordre | Application | Action | Résultat |
|---|---|---|---|
| 1 | LarcProf (priorité haute) | Remplacer 57 hardcodings QSS | Design System conforme |
| 2 | LarcSuperviseur | Remplacer ~25 hardcodings | Design System conforme |
| 3 | LarcSecretaire | Remplacer ~11 hardcodings restants | 0 hardcoded |
| 4 | LarcHub + LarcDesign | Vérifier et corriger | Design System conforme |
| 5 | Vérifier `parent_manager.py` | Confirmer 0 hardcoded | Fichier de référence |

### Sous-système Q — Ergonomie des fenêtres de liste (recherche, tableaux)

**Principe** : une fenêtre de liste (recherche d'élèves, tableaux de résultats, listes)
doit offrir le **même niveau de rétroaction M3 que les vignettes `StudentCard`** :
hover state layer, état vide inline, raccourcis clavier, info-bulles.

| # | Règle | ❌ Anti-pattern | ✅ M3 | Priorité |
|---|---|---|---|---|
| Q1 | **Hover state layer sur les lignes de tableau** | `ds.table_qss()` seul (aucun `::item:hover`) | `ds.table_qss()` + `M3TableWidget::item:hover { background: {p.surface_variant}; }` + `viewport().setCursor(Qt.PointingHandCursor)` | 🔴 Bloquant |
| Q2 | **État vide INLINE** (zéro résultat) | `QMessageBox.information(...)` modal qui interrompt | Icône `md3_icon("search_off", ...)` + message dans le panneau (`_empty_state`), tableau caché | 🔴 Bloquant |
| Q3 | **Clavier** : Entrée = ouvrir + focus initial | Entrée ne fait rien sur la ligne sélectionnée | `eventFilter` → `Qt.Key_Return`/`Qt.Key_Enter` ouvre la fiche ; `showEvent` → `setFocus()` sur le champ de recherche | 🟡 Important |
| Q4 | **Affordance** : info-bulles + feedback de chargement | Zone cliquable sans indice ; requête sans retour visuel | `setToolTip(...)` sur photo/actions ; label « Recherche en cours… » (`_search_status`) pendant la requête | 🟡 Important |

**Exemple — recherche élève (StudentForm) :**

```python
# Q1 : hover + curseur sur les lignes de résultats
self._results_table.viewport().setCursor(Qt.PointingHandCursor)
self._results_table.setStyleSheet(
    ds.table_qss()
    + f"M3TableWidget::item:hover {{ background: {ds.p.surface_variant}; }}"
)

# Q2 : état vide inline (jamais de QMessageBox modal)
self._empty_state = M3Frame()   # icône md3_icon("search_off") + M3Label
# count == 0 →  self._results_table.hide(); self._empty_state.show()

# Q3 : Entrée ouvre la fiche + focus initial
# eventFilter : obj == self._results_table and event.key() in (Qt.Key_Return, Qt.Key_Enter)
#     → ouvrir la fiche si une ligne est sélectionnée
# showEvent → self._search_input.setFocus()

# Q4 : info-bulle + indicateur de chargement
self._detail_photo.setToolTip(_("student_form.open_file"))
# avant la requête : self._search_status.setText(_("student_form.searching")); show()
# après (finally)  : self._search_status.hide()
```

**Règles dérivées Q5–Q6 :**
- **Q5** — Le `_restyle()` doit ré-appliquer le QSS hover (`::item:hover`) ET la couleur de l'état vide / du statut à chaque `theme_changed` (D7).
- **Q6** — Les clés i18n doivent exister dans fr.json ET en.json (`student_form.searching`, `student_form.search_no_results`, `student_form.open_file`).

**Companion statique Q1+Q3 (R-linter) :**

La règle `Q1+Q3` du R-linter (`lint_qss_hardcoding.py`) vérifie **statiquement** que
toute table interactive respecte Q1+Q3 :

```text
Toute M3TableWidget/QTableWidget avec un signal interactif connecté
(cellDoubleClicked, cellClicked, itemDoubleClicked, itemClicked) DOIT avoir :
  • {var}.viewport().setCursor(Qt.PointingHandCursor)   (Q1 — affordance)
  • {var}.installEventFilter(self)                      (Q3 — Entrée-ouvre)
  • une méthode def eventFilter() dans le même bloc      (Q3 — sinon le
    installEventFilter est orphelin et Qt l'ignore silencieusement)
```

- L'analyse est scoping par **bloc top-level** (classe/def) → pas de faux positif quand
  deux classes du même fichier partagent le même nom de variable (ex: `_Page._table`
  et `_TimelinePage._table`).
- Une table **sans** signal interactif (affichage seul : dashboard, stats) est exempte.
- Lancement : `python scripts/lint_qss_hardcoding.py` (fait partie du scan global).
- **Limite connue** : si une classe installe l'eventFilter mais HÉRITE la méthode
  `eventFilter()` d'une classe parente, la règle signale un faux positif (heuristique
  de bloc). Préférer définir `eventFilter()` dans la classe qui crée la table.

**Companion statique Q2 (R-linter) :**

La règle `Q2` du R-linter vérifie **statiquement** qu'aucun `QMessageBox.information`
n'est utilisé comme état vide (zéro résultat) :

```text
Tout QMessageBox.information dont le message est un état vide DOIT être remplacé
par un _empty_state INLINE (icône + message dans le panneau, tableau caché).
Marqueurs détectés :
  • clés i18n .no_users, .no_address, .no_results, .no_data, .no_students...
    (suffixe `_no_xxx` — pas `.none` / `.empty` : seul le littéral EN
    « empty / none found » est détecté, pas la clé i18n)
  • littéraux « aucun / aucune / rien / vide / introuvable » (FR)
  • littéraux « not found / no results / no data / empty / none found » (EN)
```

- **Périmètre par défaut : `QMessageBox.information` uniquement** (décision
  documentée — le hook pre-commit garde ce défaut).
- **Audit étendu opt-in `--rule Q2w`** : `python scripts/lint_qss_hardcoding.py
  --rule Q2w` signale aussi les `QMessageBox.warning` contenant un marqueur
  d'état vide (ex: `parent.error.no_address`) → findings taggés `[Q2w]`.
  Les validations (`no_parent_selected`, `no_student_available`,
  `validation_required`) ne sont PAS des états vides — le lookahead
  `(?!_selected|_available|_required)` les exclut. Utiliser Q2w en audit manuel
  (pas sur le hook) avant une campagne de correction ciblée.
- **Non signalés** (pas d'état vide) : messages de succès (`save_success`,
  `share_success`, `export_pdf_success`), de redémarrage (`restart_needed`),
  d'expiration (`session_expired`), d'aide (`search_info_msg`), de config manquante
  (`drive_dir_missing`) — le message ne contient aucun marqueur.
- Correction type : `_share_status`/`_addr_status` M3Label inline (color
  `text_disabled`), montré à la place du `QMessageBox`, restylé dans `_restyle()`
  (règle D7).
- Lancement : `python scripts/lint_qss_hardcoding.py` (fait partie du scan global,
  branché sur le hook pre-commit `lint-rlinter`). Variante audit étendu :
  `python scripts/lint_qss_hardcoding.py --rule Q2w` (`.warning` inclus).

## 6. Checklist

- [ ] `ds` importé dans TOUS les fichiers de vues
- [ ] 0 `setContentsMargins(a,b,c,d)` avec valeurs littérales (sauf 0)
- [ ] 0 `setSpacing(n)` avec valeur littérale (utiliser `ds.space_*`)
- [ ] 0 `setFixedWidth(n)` ou `setFixedHeight(n)` avec valeur littérale
- [ ] 0 `border-radius: Npx` en dur (utiliser `ds.radius_*`)
- [ ] 0 `font-size: Npx` en dur (utiliser `ds.font_*`)
- [ ] 0 `color: #XXXXXX` en dur (utiliser `ds.p.*`)
- [ ] 0 `background: #XXXXXX` en dur (utiliser `ds.p.*`)
- [ ] 0 image PNG/JPG comme icône (utiliser `md3_icon()`)
- [ ] Tous les QSS inline utilisent les helpers (`ds.flat_input_qss()`, etc.)
- [ ] **AUCUN `theme=phi`** passé aux widgets phibuilder
- [ ] **Q1** : `::item:hover` + `PointingHandCursor` sur les lignes des tableaux de liste
- [ ] **Q2** : état vide INLINE (icône + message), jamais de `QMessageBox` modal pour 0 résultat
- [ ] **Q3** : Entrée ouvre la fiche sélectionnée + focus initial sur le champ de recherche
- [ ] **Q4** : info-bulles sur les zones cliquables + indicateur de chargement pendant les requêtes
- [ ] **Tous les widgets ont `setObjectName()`** pour le ciblage QSS global
- [ ] **Tout `QWidget()`/`QDialog()` ciblé par QSS utilise `ThemedWidget`/`ThemedDialog`** (contourne le bug Qt `WA_StyledBackground`)
- [ ] **`ds.theme_changed.connect(self._restyle_all)`** dans chaque vue
- [ ] **`_STYLE()` property** utilisée pour le QSS global dynamique
- [ ] LarcProf = 0 hardcodings (57 → 0) + 0 `theme=phi`
- [ ] LarcSuperviseur = 0 hardcodings (~25 → 0) + 0 `theme=phi` ✅ **déjà conforme**
- [ ] LarcSecretaire = 0 hardcodings (~11 → 0) + 0 `theme=phi`

### Sous-système R — Règle de conformité ZERO hardcoding

**Principe** : Aucune valeur en pixels littérale dans le code Python. Toute valeur visuelle
(padding, margin, spacing, border-radius, font-size, width, height) DOIT utiliser un token
`ds.space_*`, `ds.radius_*`, `s(*)`, ou `theme_manager.image.*`.

**Cette règle s'applique à TOUS les modules Larc (Superviseur, Secretaire, Prof, Hub, Design).**

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| R1 | **Aucun `border-radius: Npx`** | `border-radius: 6px` | `border-radius: {ds.radius_sm}px` | 🔴 Bloquant |
| R2 | **Aucun `padding: Npx`** | `padding: 8px 12px` | `padding: {ds.space_xs}px {ds.space_sm}px` | 🔴 Bloquant |
| R3 | **Aucun `margin: Npx`** | `margin: 20px` | `margin: {ds.space_md}px` | 🔴 Bloquant |
| R4 | **Aucun `font-size: Npx`** | `font-size: 14px` | `font-size: {s(14)}px` | 🟡 Important |
| R5 | **Aucun `setFixedHeight(N)`** | `setFixedHeight(52)` | `setFixedHeight(ds.button_height)` (52px) — `ds.field_height` = 32px pour les champs | 🟡 Important |
| R6 | **Aucun `setFixedWidth(N)`** | `setFixedWidth(233)` | `setFixedWidth(ds.sidebar_width)` | 🟡 Important |
| R6b | **Aucun `min-width:` / `max-width:` / `min-height:` / `max-height:` en QSS inline** | `min-width: 180px` | `min-width: {ds.space_xl}px` ou token | 🟡 Important |
| R7 | **Aucun `setContentsMargins(N,N,N,N)`** | `setContentsMargins(6,6,6,6)` | `setContentsMargins(ds.space_sm, ...)` | 🟡 Important |
| R8 | **Aucun `setSpacing(N)`** | `setSpacing(6)` | `setSpacing(ds.space_xs)` | 🟡 Important |
| R9 | **Aucun `setMinimumHeight(N)` > 40** | `setMinimumHeight(48)` | `setMinimumHeight(ds.space_xl)` ou token | 🟢 Faible |
| R9b | **Aucun `setMinimumSize(W,H)` / `setMaximumSize(W,H)` / `setMinimumWidth(N)` / `setMaximumWidth(N)`** | `setMinimumSize(987, 610)` | `setMinimumSize(ds.space_*, ds.space_*)` ou défaut Qt | 🟡 Important |
| R10 | **Aucune ligne alternée dans les tableaux** | `setAlternatingRowColors(True)` ou `alternate-background-color` dans le QSS | `setAlternatingRowColors(False)` sur TOUS les tableaux et ZÉRO `alternate-background-color` dans le QSS | 🔴 Bloquant |
| R11 | **Aucune arithmétique `token + littéral`** | `setColumnWidth(0, ds.sp(XXL) + ds.sp(LG) + 34)` | `setColumnWidth(0, ds.space_xxl + ds.space_lg)` — jamais `+ 34` / `+ 9` | 🟡 Important |

#### R12 — Valeurs autorisées en dehors des tokens

Ces valeurs en pixels sont **acceptées** sans token car ce sont des constantes de structure :

| Valeur | Usage | Justification |
|---|---|---|
| `0` ou `0px` | Marges nulles, bordures transparentes | Zéro universel |
| `1` ou `1px` | Séparateurs fins, épaisseur de bordure | `ds.border_width` si récurrent |
| `17` | `border-radius: 17px` sur `M3ProfileButton` 34×34 | Cercle parfait (34/2) |

#### R13 — Script linter associé

Un script de vérification automatique est disponible :

```bash
python scripts/lint_qss_hardcoding.py                              # Audit simple (5 projets)
python scripts/lint_qss_hardcoding.py --dir .\LarcSuperviseur       # Un seul module
python scripts/lint_qss_hardcoding.py --dir .\LarcCommon            # Rapport détaillé fichier par fichier
python scripts/lint_qss_hardcoding.py --fix                         # Correction auto (valeurs triviales)
python scripts/lint_qss_hardcoding.py --threshold P0                # Uniquement les P0
python scripts/lint_qss_hardcoding.py --json                        # Sortie JSON pure (parsable)
```

**Mode `--dir` : rapport détaillé par fichier** (contrairement à l'audit simple qui
n'affiche qu'un total par projet) :

```bash
python scripts/lint_qss_hardcoding.py --dir .\LarcCommon --group-by subdir    # Groupé par sous-répertoire (défaut)
python scripts/lint_qss_hardcoding.py --dir .\LarcCommon --group-by package   # Groupé par package (ex: larccommon/widgets)
python scripts/lint_qss_hardcoding.py --dir .\LarcCommon --group-by file      # Liste plate, sans en-têtes
python scripts/lint_qss_hardcoding.py --dir .\LarcCommon --group-by auto      # Auto : package si profondeur ≥ 2, sinon subdir
```

| Option | Rôle |
|---|---|
| `--dir .\LarcCommon` | Scanne un répertoire (inclut `larccommon/` ET `phibuilder/`) et liste chaque fichier avec son statut ✅/❌ |
| `--group-by subdir` | (défaut) Regroupe par sous-répertoire de premier niveau (ex: `larccommon/`, `phibuilder/`) |
| `--group-by package` | Regroupe par chemin de package complet (ex: `larccommon/widgets/`, `phibuilder/style/`) |
| `--group-by file` | Liste plate, chaque fichier sur sa ligne, sans en-têtes de groupe |
| `--group-by auto` | Détecte la profondeur max des fichiers : `package` si ≥ 2 niveaux, sinon `subdir` |
| `--json` | Sortie JSON **pure** (plus de ligne « Scan de... » parasite) — parsable par `json.load()` |

Exemple de sortie `--group-by auto` sur LarcCommon (profondeur max = 3 → package) :

```
⚙️  --group-by auto → package (profondeur max = 3)

  ==================================================
  📋 ./LarcCommon — 0 hardcodings sur 82 fichiers scannés
  ==================================================

  ✅ larccommon/ — 0 hardcoding(s) — 16 fichier(s)
    ✅ LarcCommon\larccommon\__init__.py — 0
    ...
  ✅ larccommon/widgets/ — 0 hardcoding(s) — 12 fichier(s)
  ✅ phibuilder/widgets/ — 0 hardcoding(s) — 20 fichier(s)
```

**Le script détecte AUSSI les valeurs en dur dans les f-strings QSS multi-lignes** :
`padding: 2px`/`3px`, `min-width: 180px`, `setMinimumSize(987, 610)`, etc. sont signalés
même quand la ligne contient par ailleurs des tokens (`{ds.radius_sm}`). Un f-string QSS
avec blocs `{{ }}` n'est plus ignoré en bloc — seule la valeur littérale est signalée.

**Limites connues (documentées pour ne pas créer de fausses attentes) :**
- **R11 non détectable automatiquement** : l'arithmétique `token + littéral`
  (`ds.sp(XXL) + 34`) est une règle de revue manuelle — aucun pattern regex fiable ne la couvre.
- **QSS à accolades simples (string non-f-string)** : `"QPushButton { padding: 8px; }"` — le
  masquage `{expr}` transforme tout le bloc en `{TOKEN}` → la valeur interne n'est pas signalée.
  Limite pré-existante : ces lignes étaient ignorées en bloc avant. À migrer en f-string si besoin.

**Intégration pré-commit (obligatoire — hook `lint-rlinter`) :**

Le R-linter est branché sur pre-commit sous l'id `lint-rlinter`, aux côtés du
D-linter (`lint-dlinter`). Il retourne 1 si une violation est détectée → bloque
le commit. Couvre R (zéro hardcoding pixels) + Q1+Q3 (tables interactives sans
curseur main / eventFilter) + Q2 (QMessageBox.information utilisé comme état
vide, zéro résultat).

```yaml
# .pre-commit-config.yaml (config CENTRALE C:\projets + 5 configs locales)
- repo: local
  hooks:
    - id: lint-dlinter
      entry: python C:/projets/scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7 --fix-only
      language: system
      files: \.py$
      stages: [pre-commit]
      verbose: true
      pass_filenames: false
    - id: lint-rlinter
      name: 🔬 Linter QSS Larc (R + Q1+Q3 + Q2 — zéro hardcoding)
      entry: python C:/projets/scripts/lint_qss_hardcoding.py --fix-only
      language: system
      files: \.py$
      stages: [pre-commit]
      verbose: true
      pass_filenames: false
```

> `--fix-only` (comme lint-dlinter) : en cas de violation, le hook n'affiche que
> les lignes compactes `[Règle] fichier:ligne  contexte` au lieu du rapport détaillé.

> ⚠️ Le R-linter force UTF-8 dans main() (`io.TextIOWrapper`) — indispensable
> sous pre-commit Windows (cp1252), sinon `UnicodeEncodeError` sur les emojis 🔍📋✅.

#### R14 — Table de mapping valeurs → tokens (pour --fix et pour les développeurs)

| Valeur (px) | Token espacement | Token shape | Token image | Token police |
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
| 18 | — | — | `theme_manager.image.icon_btn` | `s(18)` |
| 20 | `ds.space_md` | — | — | — |
| 21 | — | — | — | `s(21)` / `ds.table_row_min` |
| 24 | — | — | — | `s(24)` |
| 28 | — | `ds.radius_xl` | — | `s(28)` |
| 32 | `ds.space_lg` | — | — | `s(32)` |
| 34 | — | — | `theme_manager.image.theme_btn` | — |
| 40 | — | — | hauteur bouton M3 | — |
| 52 | `ds.space_xl` | — | `ds.button_height` / `ds.header_height` | — |
| 55 | — | — | `theme_manager.image.logo_small` | — |
| 84 | `ds.space_xxl` | — | — | — |
| 89 | — | — | `theme_manager.image.logo` | — |
| 100 | — | — | `theme_manager.image.add_btn` | — |
| 136 | `ds.space_xxxl` | — | — | — |
| 150 | — | — | `theme_manager.image.avatar` | — |
| 233 | — | — | `ds.sidebar_width` | — |

> **⚠️ Hauteurs réelles (vérifiées dans `design_system.py`)** : `ds.field_height` = **32px** (= `ds.space_lg`), `ds.button_height`/`ds.header_height` = **52px** (= `ds.space_xl`), `ds.table_row_min` = **21px**. Ne PAS confondre : 52px = boutons/en-têtes, 32px = champs, 21px = lignes tableau.

#### R16 — Règle QScrollArea : viewport transparent

**Principe** : Tout `QScrollArea` ou `M3ScrollArea` DOIT avoir son viewport en `background: transparent`.
Le fond réel est géré par le widget parent (QFrame#panel, container#sidebar, etc.) via `_STYLE`.

| # | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|
| R14a | Viewport blanc par défaut | `viewport().setStyleSheet("background: transparent;")` | 🟡 Important |
| R14b | Widget contenu sans fond défini | `widget.setAttribute(Qt.WA_StyledBackground, True)` + `setStyleSheet("background: transparent;")` | 🟡 Important |

**Pattern obligatoire dans INIT** :

**Cas composition** (QScrollArea/M3ScrollArea comme attribut) :
```python
scroll_area = M3ScrollArea()
scroll_area.setWidgetResizable(True)
content_widget = QWidget()
scroll_area.setWidget(content_widget)
scroll_area.setObjectName("mon_scroll")

# 🔴 NE PAS OUBLIER :
scroll_area.viewport().setStyleSheet("background: transparent;")
content_widget.setAttribute(Qt.WA_StyledBackground, True)
content_widget.setStyleSheet("background: transparent;")
```

**Cas héritage** (classe extends M3ScrollArea) :
```python
class MonSidebar(M3ScrollArea):
    def __init__(self):
        super().__init__()
        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        # 🔴 NE PAS OUBLIER :
        self.viewport().setStyleSheet("background: transparent;")
```

**Pattern obligatoire dans le handler de changement de thème** :
```python
def on_theme_changed(self, key):
    ...
    # Maintenir la transparence après changement de thème
    if hasattr(self, "mon_scroll"):
        self.mon_scroll.viewport().setStyleSheet("background: transparent;")
    if hasattr(self, "content_widget"):
        self.content_widget.setStyleSheet("background: transparent;")
```

**Justification** : Le viewport de `QScrollArea` a un fond blanc par défaut en Qt. En mode dark,
ce fond blanc apparaît entre les widgets enfants (cartes, panels) et autour d'eux, cassant
l'harmonie du thème dark. En rendant le viewport transparent, le fond du parent (`p.surface`
ou `p.surface_variant` via `_STYLE`) traverse correctement.

**Vérification rapide** :
```bash
# Linux / macOS :
grep -rn "M3ScrollArea\|QScrollArea" *.py | grep -v "viewport.*transparent" | grep -v "test_"
```
```powershell
# Windows :
findstr /S /N "M3ScrollArea" *.py | findstr /V "transparent"
```

#### R15 — Résultat attendu du linter

Un module **conforme** doit produire :

```
$ python scripts/lint_qss_hardcoding.py --dir .\LarcSuperviseur
Scanning LarcSuperviseur...
  ✅ TopBar <- 0 hardcodings
  ✅ MainWindow <- 0 hardcodings
  ✅ StudentDetail <- 0 hardcodings
  ✅ EventGenerator <- 0 hardcodings
  ...
RÉSULTAT : 0 hardcodings sur 24 fichiers — FÉLICITATIONS ✅
```

#### R17 — Pattern phibuilder (tokens propres de la bibliothèque)

**Principe** : `phibuilder` est la bibliothèque de widgets génériques de LarcCommon.
Elle NE DOIT **JAMAIS** importer `ds` (design_system.py) — dépendance inverse interdite
(les apps importent `ds` ET `phibuilder`, jamais l'inverse). Elle utilise ses **propres tokens** :

| Objet | Rôle | Exemple |
|---|---|---|
| `phibuilder.phi.scale.SpacingToken` | Index Fibonacci (IntEnum) | `SpacingToken.XXS` = 1 |
| `PhiScale(base_spacing=4)` | Échelle → pixels : `spacing(token) = int(token) × 4` | `PhiScale().spacing(SpacingToken.MD)` = 20 |
| `theme.spacing` | Instance `PhiScale(base_spacing=4)` du thème actif | `theme.spacing.spacing(SpacingToken.LG)` = 32 |
| `theme.typo.<nom>.size` | Tokens typo M3 (px) | `theme.typo.label_medium.size` = 12 |

**Table de mapping SpacingToken → px (base 4) :**

| Token | px | | Token | px |
|---|---|---|---|---|
| `XXS` | 4 | | `XL` | 52 |
| `XS` | 8 | | `XXL` | 84 |
| `SM` | 12 | | `XXXL` | 136 |
| `MD` | 20 | | `HUGE` | 220 |
| `LG` | 32 | | `GIANT` | 356 |
| — | — | | `COLOSSAL` | 576 |

**Tokens typo M3 utiles** (`theme.typo.<nom>.size`) : `label_small`=11, `label_medium`=12,
`body_small`=12, `label_large`=14, `body_medium`=14, `title_small`=14, `body_large`=16,
`title_medium`=16, `title_large`=22, `headline_small`=24…

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| R17a | **Tailles indépendantes du thème → `_SCALE = PhiScale()` module-level** (défini UNE fois en haut du fichier, importé de `phibuilder.phi.scale`). Utilisé pour `setMinimumHeight` / `setFixedHeight` / `setMinimumWidth` / `setFixedSize` dans `__init__`, AVANT le `if theme is None: return` | `setMinimumHeight(40)` | `self.setMinimumHeight(_SCALE.spacing(SpacingToken.MD) * 2)` | 🔴 Bloquant |
| R17b | **QSS → `theme.spacing.spacing(SpacingToken.X)`** via aliasing `c, s = theme.colors, theme.spacing` (et `t = theme.typo` si fonts) | `padding: 8px` | `padding: {s.spacing(SpacingToken.XS)}px` | 🔴 Bloquant |
| R17c | **Fonts → `theme.typo.<token>.size`** via aliasing `t = theme.typo` | `font-size: 12px` | `font-size: {t.label_medium.size}px` | 🟡 Important |
| R17d | **Arithmétique de tokens autorisée** (`// 2`, `// 4`, `* 2`, additions de tokens) — jamais de littéral nu | `setFixedWidth(280)` ou `spacing(XXXL) + 8` | `setFixedWidth(_SCALE.spacing(SpacingToken.XXXL) * 2 + _SCALE.spacing(SpacingToken.XS))` | 🟡 Important |

**Règles d'arithmétique R17d (équivalent R11 pour phibuilder) :**

| Valeur cible (px) | Expression token (base 4) |
|---|---|
| 2 | `spacing(XXS) // 2` |
| 6 | `spacing(XXS) + spacing(XXS) // 2` |
| 13 | `spacing(XL) // 4` — *pas de token typo M3 exact pour 13px* |
| 24 | `spacing(MD) + spacing(XXS)` |
| 40 | `spacing(MD) * 2` |
| 80 | `spacing(MD) * 4` |
| 280 | `spacing(XXXL) * 2 + spacing(XS)` |
| 400 | `spacing(MD) * 20` |

> **💡 Convention** : toujours ajouter un commentaire inline documentant l'arithmétique,
ex. `# 40px` ou `# 13px — pas de token typo M3 exact`. Ces commentaires protègent les
futurs agents contre les « magiques numbers ».

> **⚖️ Deux variantes réelles pour les tailles** : `_SCALE.spacing(...)` est réservé aux
tailles structurelles indépendantes du thème (avant le guard `theme is None`).
Quand le widget **garantit** un thème non-None (ex: `M3NavigationBar` déréférence
déjà `theme.colors` en amont), `theme.spacing.spacing(...)` est aussi utilisé — ne pas
« corriger » ces usages en `_SCALE` : ils sont valides car le thème est garanti.

**Exemple complet (pattern réel des 20 widgets corrigés) :**

```python
from phibuilder.phi.scale import PhiScale, SpacingToken

_SCALE = PhiScale()  # tailles indépendantes du thème

class M3MonWidget(QWidget):
    def __init__(self, theme=None, parent=None):
        super().__init__(parent)
        # 1) Tailles structurelles — avant le guard theme
        self.setMinimumHeight(_SCALE.spacing(SpacingToken.MD) * 2)  # 40px
        if theme is None:
            return
        # 2) QSS — aliasing couleurs + spacing + typo
        c, s, t = theme.colors, theme.spacing, theme.typo
        self.setStyleSheet(
            f"M3MonWidget {{ background: {c.surface_variant}; "
            f"padding: {s.spacing(SpacingToken.XS)}px; "
            f"border-radius: {s.spacing(SpacingToken.SM)}px; "
            f"font-size: {t.label_medium.size}px; }}"  # 12px
        )
```

**Règle linter associée** : le R-linter scanne aussi `phibuilder/` avec
`python scripts/lint_qss_hardcoding.py --dir .\LarcCommon` (même masquage `{...}`).
Objectif : **0 hardcoding dans `phibuilder/`**, comme partout ailleurs.

### Sous-système N — Template de création d'un NOUVEAU composant

**Principe** : Pour tout nouveau composant (vue, panel, widget), suivre ce template
strict. Il garantit que le composant réagit au changement de thème, utilise les tokens,
et n'introduit pas de hardcoding.

**RÈGLE ABSOLUE** : Copier-ce template — ne JAMAIS créer un widget sans `_STYLE`,
`_restyle_all`, `ThemedWidget`, et connexion `theme_changed`.

```python
# =============================================================================
# NOUVEAU COMPOSANT — Template obligatoire
# =============================================================================
# 1. Imports
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot
from larccommon.widgets.themed_widget import ThemedWidget, ThemedDialog
from phibuilder.widgets import M3Button, M3Label, M3Frame

# 2. Classe — hériter de ThemedWidget (ou ThemedDialog) pour WA_StyledBackground
class MonNouveauComposant(ThemedWidget):
    """Description du composant."""

    # 3. _STYLE — property dynamique avec TOUS les widgets nommés
    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            QWidget#mon_composant_root {{
                background: {p.surface};
                color: {p.text_strong};                     /* ← D1b : TOUJOURS color: explicite */
                border: 1px solid {p.outline_variant};
                border-radius: {ds.radius_sm}px;             /* ← C : shape-small = Card */
            }}
            M3Label#mon_titre {{
                font-size: {s(14)}px;                        /* ← G : body-medium */
                font-weight: bold;
                color: {p.text_strong};                      /* ← D1 : toujours color: */
            }}
            M3Button#mon_bouton {{
                background: {p.primary};
                color: {p.on_primary};
                border: none;
                border-radius: {ds.radius_lg}px;             /* ← C : shape-large = Filled Button */
                padding: {d.btn_pad_v}px {d.btn_pad_h}px;    /* ← R : padding via DesignTokens */
                font-size: {s(13)}px;                        /* ← G : label-large = boutons */
            }}
            M3Button#mon_bouton:hover {{
                background: {p.primary};                     /* ← L : state layer, pas de changement de couleur */
            }}
        """

    # 4. __init__ — connexion theme_changed AVANT _init_ui
    def __init__(self, parent=None):
        super().__init__(parent)
        ds.theme_changed.connect(self._restyle_all)           # ← J6 : OBLIGATOIRE
        self._init_ui()

    # 5. _init_ui — construction avec setObjectName + setStyleSheet
    def _init_ui(self):
        self.setObjectName("mon_composant_root")              # ← J4 : OBLIGATOIRE
        self.setStyleSheet(self._STYLE())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)  # ← A : use ds.space_*
        layout.setSpacing(ds.space_xs)                       # ← A : use ds.space_*

        self._title = M3Label("Titre")
        self._title.setObjectName("mon_titre")               # ← J4 : ciblé par _STYLE
        layout.addWidget(self._title)

        self._button = M3Button("Action")
        self._button.setObjectName("mon_bouton")             # ← J4 : ciblé par _STYLE
        layout.addWidget(self._button)

        # Icône MD3 (jamais PNG/JPG)
        self._icon = md3_icon(
            "refresh",
            color=theme_manager.palette.text_strong,
            size=theme_manager.image.icon_btn,                # ← E : via theme_manager.image.*
        )

        # Widget avec style inline (si QSS global ne suffit pas)
        self._info = M3Label("Info")
        self._info.setStyleSheet(
            f"font-size: {theme_manager.font_size(12)}px; "  # ← G : body-small
            f"color: {theme_manager.palette.text_soft};"     # ← D1 : TOUJOURS color:
        )
        layout.addWidget(self._info)

    # 6. _restyle_all — appelé sur ds.theme_changed
    def _restyle_all(self):
        """Re-styler TOUS les widgets (QSS global + inline + icônes)."""
        # Étape 1 : QSS global (couvre tous les widgets nommés)
        try:
            self.setStyleSheet(self._STYLE())
        except RuntimeError:
            pass

        # Étape 2 : widgets avec style inline
        p = theme_manager.palette
        s = theme_manager.font_size
        try:
            self._info.setStyleSheet(
                f"font-size: {s(12)}px; color: {p.text_soft};"
            )
        except RuntimeError:
            pass

        # Étape 3 : icônes
        self._icon = md3_icon(
            "refresh",
            color=p.text_strong,
            size=theme_manager.image.icon_btn,
        )

    # 7. Handlers — toujours décorés @safe_slot
    @safe_slot("MonComposant.on_button_clicked")
    def _on_button_clicked(self):
        pass
```

**Checklist création :**

| # | Vérification | ✅ |
|---|---|---|
| N1 | Hérite de `ThemedWidget` (pas `QWidget` nu) | ☐ |
| N2 | `ds.theme_changed.connect(self._restyle_all)` dans `__init__` | ☐ |
| N3 | `setObjectName` sur le widget racine ET tous les enfants QSS | ☐ |
| N4 | Property `_STYLE()` avec QSS dynamique complet | ☐ |
| N5 | `color:` explicite dans TOUTE balise HTML (`<b style='color:{p.text_strong}'>`) | ☐ |
| N6 | ZÉRO hex hardcodé (`#2c3e50`, `#e0e0e0`, etc.) | ☐ |
| N7 | ZÉRO `border-radius: Npx` en dur → `ds.radius_*` | ☐ |
| N8 | ZÉRO `font-size: Npx` en dur → `s(N)` | ☐ |
| N9 | ZÉRO `setFixedHeight(N)` / `setFixedWidth(N)` → tokens | ☐ |
| N10 | ZÉRO `setSpacing(N)` / `setContentsMargins(a,b,c,d)` → `ds.space_*` | ☐ |
| N11 | ZÉRO `theme=phi` passé aux widgets phibuilder | ☐ |
| N12 | ZÉRO image PNG/JPG comme icône → `md3_icon()` | ☐ |
| N13 | `_restyle_all()` couvre : QSS global + inline + icônes | ☐ |
| N14 | Tous les handlers décorés `@safe_slot` | ☐ |
| N15 | Linter lancé : `python scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4` | ☐ |
| N16 | **⚠️ Ne pas confondre** `d.spacing` (=6px, layout dense) avec `ds.space_*` (Fibonacci) — utiliser `ds.space_xs`/`sm` pour les gaps visibles, `d.spacing` pour les layouts internes | ☐ |


### Sous-système H — Header / AppBar (TopBar)

**Principe** : Le Header (ou TopBar) est le bandeau horizontal tout en haut de la fenêtre
principale de chaque module Larc. Il contient :

| Zone | Contenu | Alignement |
|---|---|---|
| **Gauche** | Logo de l'école (image) + Nom du logiciel en gras | `AlignLeft` |
| **Droite** | Indicateur de connexion + Bouton thème + Profil (cercle initiales) | `AlignRight` |
| **Ligne 2** *(optionnel)* | Boutons de période (jour/semaine/mois/trimestre/année) | `AlignLeft` |

**RÉFÉRENCE** : `LarcSuperviseur/views/top_bar.py` — classe `TopBar(QFrame)`.

#### H1 — Layout général

```python
class TopBar(QFrame):
    """Bandeau 1-2 lignes : logo + nom + profil + thème + connexion."""

    def __init__(self, on_period_click=None, on_theme_change=None, on_refresh=None):
        super().__init__()
        self.setObjectName("top_bar")                       # ← ciblé par QssHelper.top_bar()
        self._build_ui()
        ...
```

#### H2 — Contenu de la ligne 1 (gauche → droite)

| Ordre | Composant | Token / Style | Rôle |
|---|---|---|---|
| 1 | **Logo** (QLabel avec QPixmap) | `scaledToHeight(theme_manager.image.logo)` — 89px | Image PNG de l'école depuis `img/logoAEC.png` |
| 2 | **Nom du logiciel** (M3Label) | `font-size: {s(21)}px; font-weight: bold; color: {p.text_strong};` | "LarcSuperviseur", "LarcSecretaire", etc. |
| 3 | *Stretch* | — | Pousse tout à droite |
| 4 | **Connexion** (M3Label) | `color: {p.success}` (intranet), `{p.primary}` (cloud), `{p.text_disabled}` (offline) | `detect_network()` → affiche le statut |
| 5 | **Bouton thème** (M3Button) | `setObjectName("theme_btn"); setFixedSize(34, 34)` | Menu déroulant avec les 4 thèmes (bleu/dark/sobre/contrasté) |
| 6 | **Profil** (M3ProfileButton) | `setFixedSize(34, 34); border-radius: 17px; background: {p.primary}; color: {p.on_primary}` | Initiales de l'utilisateur (2 lettres) + menu (Préférences, Déconnexion) |

```python
def _build_row1(self, row1: QHBoxLayout):
    p = theme_manager.palette
    s = theme_manager.font_size

    # 1. Logo (depuis img/logoAEC.png)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "img", "logoAEC.png")
    self._logo_label = M3Label()
    if os.path.exists(logo_path):
        pix = QPixmap(logo_path)
        self._logo_pixmap = pix.scaledToHeight(
            theme_manager.image.logo, Qt.SmoothTransformation  # 89px → SpacingToken.GIANT
        )
        self._logo_label.setPixmap(self._logo_pixmap)
    else:
        self._logo_label.setText("[Logo]")
    self._logo_label.setAlignment(Qt.AlignCenter)
    row1.addWidget(self._logo_label)

    # 2. Nom du logiciel en gras
    self._app_name = M3Label("LarcSuperviseur")  # ← adapter par module
    self._app_name.setStyleSheet(
        f"font-size: {s(21)}px; font-weight: bold; color: {p.text_strong};"
    )
    row1.addWidget(self._app_name)

    row1.addStretch()  # ← pousse tout à droite

    # 4. Connexion
    self._network_label = M3Label()
    self._update_network_label()  # ← voir H3
    row1.addWidget(self._network_label)

    # 5. Bouton thème
    self._theme_btn = M3Button()
    self._theme_btn.setObjectName("theme_btn")
    self._theme_btn.setFixedSize(theme_manager.image.theme_btn, theme_manager.image.theme_btn)  # 34px
    self._theme_btn.setToolTip("Changer le thème")
    self._theme_btn.setIcon(self._theme_icon())
    self._theme_btn.setIconSize(QSize(theme_manager.image.icon_btn, theme_manager.image.icon_btn))  # 18px
    self._theme_menu = M3Menu()
    for key, label in theme_manager.names():
        pal = theme_manager.get_palette(key)
        ic = md3_icon(
            _THEME_ICON_NAMES.get(key, "light_mode"),
            color=pal.primary if pal else "#1565C0",
            size=theme_manager.image.icon_btn,
        )
        a = self._theme_menu.addAction(ic, label)
        a.setData(key)
    self._theme_menu.triggered.connect(lambda action: on_theme_change(action.data()))
    self._theme_btn.setMenu(self._theme_menu)
    row1.addWidget(self._theme_btn)

    # 6. Profil (cercle avec initiales)
    self._profile_btn = M3ProfileButton("?")
    self._profile_btn.setFixedSize(theme_manager.image.profile_btn, theme_manager.image.profile_btn)  # 34px
    self._profile_btn.setCursor(Qt.PointingHandCursor)
    self._profile_btn.setStyleSheet(
        f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
        f"font-weight: bold; font-size: {s(13)}px; border: none; border-radius: 17px; }}"  # 34/2 = 17 → cercle
        f"QPushButton:hover {{ background: {p.active}; }}"
    )
    self._profile_menu = M3Menu(self)
    prefs = self._profile_menu.addAction(
        md3_icon("settings", color=p.text_strong, size=theme_manager.image.icon_menu),
        "Préférences",
    )
    prefs.triggered.connect(self._on_preferences)
    self._profile_menu.addSeparator()
    logout = self._profile_menu.addAction(
        md3_icon("logout", color=p.text_strong, size=theme_manager.image.icon_menu),
        "Déconnexion",
    )
    logout.triggered.connect(lambda: QCoreApplication.quit())
    self._profile_btn.setMenu(self._profile_menu)
    row1.addWidget(self._profile_btn)
```

#### H3 — Statut réseau

```python
def _update_network_label(self):
    """Met à jour le label de connexion selon l'état réseau."""
    intranet_ok, internet_ok = detect_network()
    p = theme_manager.palette
    s = theme_manager.font_size
    if intranet_ok:
        self._network_label.setText("🔒 Intranet")
        self._network_label.setStyleSheet(
            f"color: {p.success}; font-weight: bold; font-size: {s(12)}px;"
        )
    elif internet_ok:
        self._network_label.setText("☁️ Cloud")
        self._network_label.setStyleSheet(
            f"color: {p.primary}; font-weight: bold; font-size: {s(12)}px;"
        )
    else:
        self._network_label.setText("⚠️ Hors ligne")
        self._network_label.setStyleSheet(
            f"color: {p.text_disabled}; font-size: {s(12)}px;"
        )
```

#### H4 — Icône thème (icône dynamique selon thème actif)

```python
_THEME_ICON_NAMES = {
    "blue": "light_mode",
    "dark": "dark_mode",
    "sobre": "tonality",
    "contrast": "bolt",
}

def _theme_icon(self) -> QIcon:
    name = _THEME_ICON_NAMES.get(theme_manager.active_name, "light_mode")
    p = theme_manager.palette
    return md3_icon(name, color=p.text_strong, size=theme_manager.image.icon_btn)
```

#### H5 — Ligne 2 : boutons période (optionnelle)

Utilisée dans LarcSuperviseur (dashboard), absente dans LarcSecretaire et LarcProf.

```python
def _build_row2(self):
    # 5 boutons fixes : Jour, Semaine, Mois, Trimestre, Année
    fixed = [("Jour", "day"), ("Semaine", "week"), ("Mois", "month"),
             ("Trimestre", "term"), ("Année", "year")]
    for label, key in fixed:
        btn = M3Button(label)
        btn.setObjectName("period_btn")                     # ← ciblé par QssHelper.period_btn()
        btn.setCheckable(True)
        btn.setFixedSize(
            theme_manager.image.logo,                       # 89px (SpacingToken.GIANT)
            theme_manager.image.theme_btn                   # 34px
        )
        btn.clicked.connect(lambda checked, k=key: on_period_click(k))
        self._period_row.addWidget(btn)
```

#### H6 — Restyle après changement de thème

```python
def restyle(self):
    """Appelé par le parent sur ds.theme_changed."""
    p = theme_manager.palette
    s = theme_manager.font_size
    self._theme_btn.setIcon(self._theme_icon())
    self._profile_btn.setStyleSheet(
        f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
        f"font-weight: bold; font-size: {s(13)}px; border: none; border-radius: 17px; }}"
        f"QPushButton:hover {{ background: {p.active}; }}"
    )
    self._app_name.setStyleSheet(
        f"font-size: {s(21)}px; font-weight: bold; color: {p.text_strong};"
    )
    self._update_network_label()
```

#### H7 — Règles absolues du Header

| # | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|
| H7a | Logo en QSS ou base64 inline | `QPixmap` depuis `img/logoAEC.png` + `scaledToHeight(theme_manager.image.logo)` (89px) | 🟡 Important |
| H7b | Nom logiciel en dur sans token | `font-size: {s(21)}px` via `theme_manager.font_size` | 🟡 Important |
| H7c | Profil sans cercle (`border-radius` ≠ 17px) | `border-radius: 17px` (= 34/2 = cercle parfait) | 🔴 Bloquant |
| H7d | Bouton thème sans icône dynamique | `self._theme_icon()` = icône MD3 qui change avec le thème | 🟡 Important |
| H7e | Connexion sans 3 états | `detect_network()` → intranet (success) / cloud (primary) / offline (disabled) | 🔴 Bloquant |
| H7f | Profil sans menu | Menu avec Préférences + Déconnexion | 🔴 Bloquant |
| H7g | `setStyleSheet` inline sur le Header lui-même | `setObjectName("top_bar")` + `QssHelper.top_bar(p, d)` dans `_STYLE` | 🟡 Important |
| H7h | Hauteur du Header non définie | Hauteur naturelle via contenu × `ds.space_xxs` padding vertical | 🟢 Faible |


### Sous-système F — Footer

**Principe** : Les applications Larc (Superviseur, Secretaire, Prof) sont des applications
de **gestion de données denses** (tableaux, formulaires, dashboard, KPIs).
L'espace vertical est précieux. **Par conception, Larc n'a PAS de footer fixe.**

#### F1 — Justification

| Raison | Détail |
|---|---|
| 📊 **Data-dense** | L'essentiel du contenu est dans des tableaux, listes, et KPIs — pas de place pour un footer décoratif |
| 🖥️ **Desktop-first** | Applications fenêtrées, pas de site web — pas besoin de navigation en bas |
| 🔝 **Actions en haut** | Toutes les actions (recherche, filtre, export) sont dans la TopBar ou le Sidebar |
| ♿ **Accessibilité** | Un footer fixe consomme de la hauteur d'écran sans valeur ajoutée pour l'utilisateur |

#### F2 — Équivalent fonctionnel du footer

Ce qui **remplace** un footer dans Larc :

| Fonction footer | Remplacé par |
|---|---|
| Copyright / version | `QStatusBar` ou label en bas du Sidebar (optionnel) |
| Liens de navigation | Sidebar (gauche) |
| Actions rapides | TopBar (haut) + menus contextuels |
| Statut détaillé | Barre de statut dans les dialogues (ex: `_status_lbl` dans EvalManagerWindow) |

#### F3 — Si un footer est vraiment nécessaire dans un module futur

Dans le cas exceptionnel où un module nécessite un footer, respecter ces règles :

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|---|
| F3a | Hauteur fixe en pixels | `setFixedHeight(ds.space_lg)` (32px) — compact |
| F3b | Couleurs hex en dur | `background: {p.surface_variant}; color: {p.text_soft};` |
| F3c | Liens cliquables non stylés | `QPushButton#footer_link { color: {p.primary}; }` avec hover |
| F3d | Texte de copyright en dur | Label avec `font-size: {s(10)}px; color: {p.text_disabled};` |
| F3e | Footer sans réactivité au thème | `setObjectName("footer")` + QSS dans `_STYLE` + `_restyle_all()` |

---

## Emplacement

- `LarcCommon/larccommon/design_system.py` — singleton `ds` avec tous les tokens
- `LarcCommon/larccommon/icons.py` — 40 icônes MD3 vectorielles
- `LarcCommon/larccommon/theme.py` — `theme_manager.image.*` pour les tailles
- `scripts/lint_qss_hardcoding.py` — linter automatique (voir Sous-système R)
- `LarcSuperviseur/views/top_bar.py` — implémentation de référence du Header
- Tous les fichiers `views/*.py` et `views/**/*.py` — application des tokens + pattern J

## Dépendances

- `LarcCommon/larccommon/theme.py` — palette `ds.p.*` liée au thème actif
- `LarcCommon/larccommon/phi_scale.py` — Fibonacci pour les espacements
- `LarcCommon/larccommon/icons.py` — icônes MD3 vectorielles
- `LarcCommon/larccommon/design_system.py` — `ds.phi` (property dynamique), `ds.theme_changed` (Signal)
- `LarcCommon/larccommon/widgets/themed_widget.py` — `ThemedWidget`, `ThemedDialog`
- `scripts/lint_qss_hardcoding.py` — linter qualité (optionnel, recommandé en CI)
