---
skill: ergonomics
version: "3.0"
priority: P0
category: design
depends_on: [design-tokens, color-rules, theme-reactivity]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [Q, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21]
---

# Skill: Ergonomics — Patterns de Composition M3+Fibonacci

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Hub, Design)
**Fichier de référence liste** : `LarcSecretaire/views/parent_manager.py` — 0 hardcoded ✅
**Fichier de référence formulaire** : `LarcSecretaire/views/student_form.py` — Q1-Q14 conforme ✅
**Utilisateurs** : Développeurs de vues ET agents IA construisant des UI
**Dépendances** : `design-tokens`, `color-rules`, `theme-reactivity`

Ce skill garantit une ergonomie cohérente pour TOUTES les interfaces Larc :
fenêtres de liste (Q1-Q6), formulaires (Q7-Q14), et composition spatiale
M3+Fibonacci (Q15-Q21).

**Projet** : Larc (Superviseur, Secretaire, Prof)
**Fichier de référence** : `LarcSecretaire/views/parent_manager.py` — 0 hardcoded ✅
**Utilisateurs** : Développeurs de vues de liste/recherche
**Dépendances** : `design-tokens`, `color-rules`, `theme-reactivity`

Ce skill garantit une ergonomie cohérente pour toutes les fenêtres de liste (recherche d'élèves, tableaux, sélecteurs).

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Vue PySide6 sans retour visuel M3, sans structure spatiale harmonieuse
**Sortie** : Interface Material Design 3 complète avec proportions Fibonacci et templates canoniques
**Traitement** : Appliquer Q1-Q6 (listes) → Q7-Q14 (formulaires) → Q15-Q21 (composition spatiale)

## 2. Contraintes Fondamentales

### Table des règles Q

| # | Règle | ❌ Anti-pattern | ✅ M3 | Priorité |
|---|---|---|---|---|
| Q1 | **Hover state layer sur les lignes** | `ds.table_qss()` seul (pas de `::item:hover`) | `ds.table_qss()` + `M3TableWidget::item:hover { background: {p.surface_variant}; }` + `viewport().setCursor(Qt.PointingHandCursor)` | 🔴 P0 |
| Q2 | **État vide INLINE** (zéro résultat) | `QMessageBox.information(...)` modal | Icône `md3_icon("search_off")` + message dans le panneau (`_empty_state`), tableau caché | 🔴 P0 |
| Q3 | **Clavier** : Entrée = ouvrir + focus initial | Entrée ne fait rien | `eventFilter` → `Qt.Key_Return`/`Qt.Key_Enter` ouvre la fiche ; `showEvent` → `setFocus()` sur la recherche | 🟡 P1 |
| Q4 | **Affordance** : info-bulles + feedback chargement | Zone cliquable sans indice ; requête sans retour | `setToolTip(...)` sur photo/actions ; label « Recherche en cours… » (`_search_status`) | 🟡 P1 |
| Q5 | **Restyle** : thème réactif | QSS hover/perdu après changement de thème | `_restyle()` ré-applique `::item:hover` + couleur état vide/statut | 🔴 P0 |
| Q6 | **i18n** : clés de traduction | Texte en dur | Clés `student_form.searching`, `student_form.search_no_results`, `student_form.open_file` dans fr.json + en.json | 🟡 P1 |

### Q1 — Hover + curseur sur les lignes

```python
# ✅ Pattern obligatoire
self._results_table.viewport().setCursor(Qt.PointingHandCursor)
self._results_table.setStyleSheet(
    ds.table_qss()
    + f"M3TableWidget::item:hover {{ background: {ds.p.surface_variant}; }}"
)
```

### Q2 — État vide inline

```python
# ✅ Pattern — JAMAIS de QMessageBox modal pour 0 résultat
self._empty_state = M3Frame()
# Icône + message
empty_icon = QLabel()
empty_icon.setPixmap(md3_icon("search_off", color=ds.p.text_disabled, size=48).pixmap(48, 48))
empty_msg = M3Label(_("student_form.search_no_results"))
empty_msg.setStyleSheet(f"color: {ds.p.text_disabled}; font-size: {theme_manager.font_size(14)}px;")

# count == 0 → self._results_table.hide(); self._empty_state.show()
# count > 0  → self._results_table.show(); self._empty_state.hide()
```

### Q3 — Entrée ouvre la fiche + focus initial

```python
class MaVue(QWidget):
    def __init__(self):
        super().__init__()
        self._results_table.installEventFilter(self)
    
    def showEvent(self, event):
        super().showEvent(event)
        self._search_input.setFocus()
    
    def eventFilter(self, obj, event):
        if obj == self._results_table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                row = self._results_table.currentRow()
                if row >= 0:
                    self._open_detail(row)
                return True
        return super().eventFilter(obj, event)
```

### Q4 — Info-bulles + indicateur de chargement

```python
self._detail_photo.setToolTip(_("student_form.open_file"))

# Avant la requête
self._search_status.setText(_("student_form.searching"))
self._search_status.show()

# Après (finally)
self._search_status.hide()
```

### Q5 — Restyle des éléments Q

Le `_restyle()` doit ré-appliquer le QSS hover (`::item:hover`) ET la couleur de l'état vide/statut à chaque `theme_changed`. Voir **[theme-reactivity](../theme-reactivity/SKILL.md)**.

### Q6 — Clés i18n requises

```json
// fr.json
{
  "student_form.searching": "Recherche en cours…",
  "student_form.search_no_results": "Aucun résultat trouvé.",
  "student_form.open_file": "Ouvrir le dossier"
}
```

## 3. Code complet — Pattern Recherche Élève

```python
class StudentSearchView(ThemedWidget):
    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle_all)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Barre de recherche
        self._search_input = M3TextField(placeholder=_("search_placeholder"))
        self._search_input.setFixedHeight(ds.field_height)
        self._search_input.textChanged.connect(self._on_search)
        layout.addWidget(self._search_input)
        
        # Statut recherche
        self._search_status = M3Label("")
        self._search_status.setStyleSheet(f"color: {ds.p.text_soft}; font-size: {theme_manager.font_size(12)}px;")
        self._search_status.hide()
        layout.addWidget(self._search_status)
        
        # Tableau résultats — Q1
        self._results_table = M3TableWidget(rows=0, columns=4)
        self._results_table.set_headers(["Nom", "Prénom", "Classe", "Statut"])
        self._results_table.viewport().setCursor(Qt.PointingHandCursor)
        self._results_table.installEventFilter(self)  # Q3
        
        # État vide — Q2
        self._empty_state = self._build_empty_state()
        self._empty_state.hide()
        
        layout.addWidget(self._results_table, 1)
        layout.addWidget(self._empty_state, 1)
    
    def _build_empty_state(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(md3_icon("search_off", color=ds.p.text_disabled, size=48).pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
        msg = M3Label(_("student_form.search_no_results"))
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"color: {ds.p.text_disabled}; font-size: {theme_manager.font_size(14)}px;")
        layout.addWidget(msg)
        return widget
    
    def _on_search(self, text):
        self._search_status.setText(_("student_form.searching"))
        self._search_status.show()
        try:
            results = self._query(text)
            if not results:
                self._results_table.hide()
                self._empty_state.show()  # Q2
            else:
                self._empty_state.hide()
                self._results_table.show()
                self._populate_table(results)
        finally:
            self._search_status.hide()
    
    def _restyle_all(self):
        # Q5: ré-appliquer le hover
        self._results_table.setStyleSheet(
            ds.table_qss()
            + f"M3TableWidget::item:hover {{ background: {ds.p.surface_variant}; }}"
        )
        self._search_status.setStyleSheet(f"color: {ds.p.text_soft}; font-size: {theme_manager.font_size(12)}px;")
```

## 4. Exemples

### Exemple 1 — QMessageBox → état vide inline

```python
# ❌ AVANT — interrompt l'utilisateur
if not results:
    QMessageBox.information(self, "Recherche", "Aucun élève trouvé.")
    return

# ✅ APRÈS — état vide inline, non bloquant
if not results:
    self._results_table.hide()
    self._empty_state.show()
    return
```

### Exemple 2 — Tableau sans hover

```python
# ❌ AVANT
table = M3TableWidget()
table.setStyleSheet(ds.table_qss())

# ✅ APRÈS — Q1
table = M3TableWidget()
table.viewport().setCursor(Qt.PointingHandCursor)
table.setStyleSheet(
    ds.table_qss()
    + f"M3TableWidget::item:hover {{ background: {ds.p.surface_variant}; }}"
)
```

## 5. Step by Step — Mise à niveau d'une vue de liste

| Ordre | Action | Règle |
|---|---|---|
| 1 | Ajouter `viewport().setCursor(Qt.PointingHandCursor)` | Q1 |
| 2 | Ajouter `::item:hover` dans le QSS tableau | Q1 |
| 3 | Remplacer tout `QMessageBox.information` état vide par `_empty_state` widget | Q2 |
| 4 | Installer `eventFilter` pour Entrée + `showEvent` focus | Q3 |
| 5 | Ajouter `setToolTip` sur les zones cliquables | Q4 |
| 6 | Ajouter label `_search_status` pour le chargement | Q4 |
| 7 | Connecter `_restyle_all` pour le hover + état vide | Q5 |
| 8 | Ajouter les clés i18n dans fr.json + en.json | Q6 |
| 9 | Vérifier le ratio sidebar/contenu (liste = `ds.sidebar_width`, détail = stretch 1) | Q15a, Q16a |
| 10 | Lancer `lint_qss_hardcoding.py` — doit passer Q1+Q3+Q2 | Vérification |

## 6. Checklist Globale

### Q1-Q6 — Vues de liste
- [ ] Q1 : `viewport().setCursor(Qt.PointingHandCursor)` sur chaque table interactive
- [ ] Q1 : `::item:hover` dans le QSS de chaque table interactive
- [ ] Q2 : 0 `QMessageBox.information` avec message d'état vide
- [ ] Q2 : `_empty_state` widget (icône + message) présent et fonctionnel
- [ ] Q3 : `installEventFilter(self)` sur les tables interactives + `eventFilter` gère Entrée
- [ ] Q3 : `showEvent` → `setFocus()` sur le champ de recherche
- [ ] Q4 : `setToolTip` sur les zones cliquables + indicateur de chargement
- [ ] Q5 : `_restyle_all` ré-applique le QSS hover + couleur état vide
- [ ] Q6 : Clés i18n dans fr.json ET en.json

### Q7-Q14 — Formulaires et composition
- [ ] Q7 : Chaque section dans une `_section_card()` avec icône + titre + séparateur + ratio φ
- [ ] Q8 : Labels AU-DESSUS des champs + rythme Fibonacci 47px par ligne
- [ ] Q9 : ≥ 5 sections → single-page scrollable avec header sticky `ds.header_height`
- [ ] Q10 : `flat_input_qss()` uniquement sur les QLineEdit
- [ ] Q11 : Save/Create dans le header (jamais dans le scroll)
- [ ] Q12 : Composants complexes intégrés avec min/max height
- [ ] Q13 : Test dark theme : Q13a-Q13f
- [ ] Q14 : Grilles responsives avec `setColumnStretch` + N = round(largeur / 233)

### Q15-Q21 — Composition spatiale M3+Fibonacci
- [ ] Q15 : Ratios φ : sidebar/contenu, header/contenu, card padding/spacing, grille N colonnes
- [ ] Q16 : Template adapté au type d'écran (master-detail, full-width form, dashboard)
- [ ] Q17 : Rythme vertical : progression Fibo + sauts hiérarchiques 2-3 crans + interlignage φ
- [ ] Q18 : Densité cohérente (comfortable ou compact) selon le volume de données
- [ ] Q19 : Centre visuel au ~⅜, boutons secondaire-gauche/primaire-droite
- [ ] Q20 : Skeleton (si chargement), Snackbar (feedback non-bloquant), FAB (si action principale)
- [ ] Q21 : Formulaire créé à partir du template canonique Q21

### Linters
- [ ] `python scripts/lint_qss_hardcoding.py` → 0 violation Q1+Q3+Q2+R

---

## Sous-système Q7-Q14 — Patterns de Composition M3+Fibonacci

Ces règles couvrent l'ASSEMBLAGE des tokens en interfaces complètes.
Les tokens définissent les briques (espacements, couleurs, polices) — ces règles
définissent COMMENT les assembler pour produire une UI Material Design cohérente.

### Q7 — Section Card : pattern canonique

**Principe** : Toute section d'un formulaire ou d'une page de détail DOIT être encapsulée
dans une carte M3 avec : icône + titre + séparateur + corps.

```python
def _section_card(title: str, icon_name: str) -> tuple[M3Card, QVBoxLayout]:
    """Pattern canonique pour une carte de section M3."""
    card = M3Card(variant=CardVariant.ELEVATED)
    card.setStyleSheet(
        f"M3Card {{ background: {ds.p.surface}; "
        f"border: 1px solid {ds.p.outline_variant}; "
        f"border-radius: {ds.radius_md}px; }}")
    cl = card.content_layout()
    cl.setSpacing(ds.space_sm)
    cl.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
    # En-tête : icône + titre + stretch
    hdr = QHBoxLayout()
    hdr.setSpacing(ds.space_xs)
    icon_lbl = QLabel()
    icon_lbl.setPixmap(md3_icon(icon_name, color=ds.p.primary, size=20).pixmap(20, 20))
    hdr.addWidget(icon_lbl)
    title_lbl = M3Label(title, style="title_medium")
    title_lbl.setStyleSheet(f"color: {ds.p.text_strong}; font-weight: bold;")
    hdr.addWidget(title_lbl)
    hdr.addStretch()
    cl.addLayout(hdr)
    # Séparateur subtil
    sep = M3Frame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {ds.p.outline_variant};")
    cl.addWidget(sep)
    return card, cl
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q7a | **Card variant** | `CardVariant.FILLED` (fond surface_variant, moins de contraste) | `CardVariant.ELEVATED` + bordure `outline_variant` explicite | 🟡 P1 |
| Q7b | **Card radius** | `radius_sm` (8px — trop petit pour une carte de section) | `radius_md` (12px — distinction visuelle claire entre les cartes) | 🟡 P1 |
| Q7c | **Section header** | Titre sans icône, ou icône sans titre | Icône MD3 20px primary + titre `title_medium` bold + séparateur 1px `outline_variant` | 🟡 P1 |
| Q7d | **Card padding** | `space_sm` ou `space_md` | `space_m3` (16px — padding M3 standard pour les cartes) | 🟡 P1 |
| Q7e | **Card spacing** | `space_sm` (12px — cartes trop proches) | `space_md` (20px — Fibonacci, distinction nette entre sections) | 🟡 P1 |
| Q7f | **Ratio padding/contenu** | Padding = spacing interne (confusion visuelle) | Padding externe (`space_m3`=16) / spacing interne (`space_sm`=12) ≈ 1.33 → proche de √φ (1.27). La card RESPire plus qu'elle ne serre. | 🟡 P1 |

### Q8 — Form Field Layout : label AU-DESSUS du champ

**Principe** : En Material Design, les labels de champ sont placés AU-DESSUS du champ,
pas à côté (pas de `QFormLayout`). C'est le standard M3 pour les formulaires.

```python
def _field_row(label: str, widget, is_date: bool = False) -> QVBoxLayout:
    """Pattern canonique pour une ligne de formulaire M3."""
    row = QVBoxLayout()
    row.setSpacing(ds.space_xxs)
    lbl = M3Label(label, style="label_small")
    lbl.setStyleSheet(f"color: {ds.p.text_soft}; font-weight: bold;")
    row.addWidget(lbl)
    widget.setMinimumHeight(ds.field_height)
    if not is_date:
        widget.setStyleSheet(ds.flat_input_qss())
    row.addWidget(widget)
    return row
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q8a | **Label position** | `QFormLayout` (label à gauche du champ) | Label AU-DESSUS du champ via `QVBoxLayout` + `M3Label(label_small, text_soft)` | 🔴 P0 |
| Q8b | **Label style** | `body_medium` + `text_strong` (trop lourd) | `label_small` (11px) + `text_soft` + bold — discret, hiérarchie claire | 🟡 P1 |
| Q8c | **Label spacing** | `space_sm` ou `space_xs` | `space_xxs` (4px — accolé au champ, lien visuel fort) | 🟡 P1 |
| Q8d | **Grid columns** | Grille à 2 colonnes maximum | 3 colonnes recommandé pour formulaires denses (ex: Prénom/Nom/Genre) | 🟢 P2 |
| Q8e | **Field row height rhythm** | Hauteurs de ligne arbitraires | Label `s(11)`=11px + gap `space_xxs`=4px + champ `field_height`=32px = 47px par ligne → proche de F₁₀=55 moins `space_xs`=8. Les lignes de formulaire s'empilent avec un rythme Fibonacci. | 🟡 P1 |

### Q9 — Single-Page Scrollable vs Tabs : règle de décision

**Principe** : Pour les formulaires complexes (6+ sections), préférer le **single-page scrollable**
plutôt que des onglets ou une sidebar de navigation.

| Critère | Tabs / Sidebar | Single-Page Scrollable |
|---|---|---|
| Nombre de sections | ≤ 4 sections | ≥ 5 sections |
| Découverte du contenu | L'utilisateur doit cliquer pour voir | Tout est visible en scrollant |
| Charge cognitive | Haute (où est cette info ?) | Basse (tout est là) |
| Complexité d'implémentation | Simple (QStackedWidget) | Moyenne (QScrollArea + cartes) |
| Empreinte visuelle | Compacte (une page à la fois) | Longue (tout est affiché) |

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q9a | **≥ 5 sections** | Sidebar + QStackedWidget (trop de clics) | M3ScrollArea + toutes les sections en cartes scrollables | 🟡 P1 |
| Q9b | **≤ 4 sections** | Single-page scrollable (overkill) | Sidebar + stack OU chips horizontaux — au choix | 🟢 P2 |
| Q9c | **Header fixe** | Boutons Save/Cancel dans le scroll (disparaissent) | Header STICKY hors scroll avec photo + nom + actions toujours visibles | 🔴 P0 |
| Q9d | **Scroll background** | Viewport blanc (casse le thème dark) | `viewport().setStyleSheet("background: transparent;")` ET `content.setStyleSheet(f"background: {ds.p.background};")` | 🔴 P0 |
| Q9e | **Scroll momentum** | Header et contenu sans relation proportionnelle | Le header sticky fait EXACTEMENT `ds.header_height` (52px = F₁₂). Le ratio header/contenu visible ≈ 52 / (hauteur_fenêtre - 52) → tend vers 1/φ pour une fenêtre de ~900px. | 🟡 P1 |

### Q10 — QSS Specificity : ne pas appliquer flat_input_qss() aux QDateEdit/QComboBox

**Principe** : `ds.flat_input_qss()` cible les sélecteurs `QLineEdit`. L'appliquer sur un
`QDateEdit` ou `QComboBox` écrase leur QSS spécifique et cause des bugs d'affichage
(texte noir sur fond sombre en dark theme).

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q10a | **flat_input_qss() sur QDateEdit** | `date_edit.setStyleSheet(ds.flat_input_qss())` | QSS dédié avec `QDateEdit { ... }` ET `QDateEdit QLineEdit { ... }` | 🔴 P0 |
| Q10b | **flat_input_qss() sur QComboBox** | `combo.setStyleSheet(ds.flat_input_qss())` | QSS dédié ciblant `QComboBox` et ses sous-contrôles | 🔴 P0 |
| Q10c | **QSS date fields** | Padding uniforme `space_md` (20px) sur toutes les faces | `padding: {ds.space_xs}px {ds.space_sm}px` (8px vertical, 12px horizontal) | 🟡 P1 |
| Q10d | **Date field width** | `setFixedWidth(104)` — trop étroit pour `yyyy-MM-dd` | `setMinimumWidth(ds.sp(SpacingToken.XXXL))` (136px) — laisse respirer la date | 🟡 P1 |

**Pattern QSS obligatoire pour QDateEdit :**
```python
w.setStyleSheet(
    f"QDateEdit {{ border: 1px solid {ds.p.outline}; "
    f"border-radius: {ds.radius_xs}px; "
    f"padding: {ds.space_xs}px {ds.space_sm}px; "
    f"color: {ds.p.text_strong}; background: {ds.p.surface}; }}"
    f"QDateEdit QLineEdit {{ color: {ds.p.text_strong}; "
    f"background: {ds.p.surface}; }}")
```

### Q11 — Action Buttons Placement

**Principe** : Les boutons d'action principaux (Sauvegarder, Créer, Annuler) doivent être
TOUJOURS visibles, jamais enfouis dans le scroll.

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q11a | **Save/Create** | Bouton dans le contenu scrollable (disparaît au scroll) | Dans le HEADER (toujours visible) — variant `FILLED`, proéminent | 🔴 P0 |
| Q11b | **Cancel** | Bouton FILLED (confusion avec Save) | `OUTLINED` ou `TONAL` dans le header, à côté de Save | 🟡 P1 |
| Q11c | **Export (PDF/Word)** | Boutons FILLED (volent l'attention) | `TONAL` dans le header, moins proéminents que Save | 🟢 P2 |
| Q11d | **Button height** | `ds.button_height` (52px — trop grand pour une barre d'action) | `ds.field_height + ds.space_xs` (40px — compact, professionnel) | 🟡 P1 |

### Q12 — Complex Component Integration in Scroll

**Principe** : Quand un composant complexe (avec sa propre sidebar/splitter interne) est intégré
dans une page scrollable, lui donner une hauteur fixe pour qu'il ne pousse pas les autres sections
hors de l'écran.

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q12a | **Hauteur illimitée** | `addWidget(panel)` sans contrainte de hauteur | `panel.setMinimumHeight(450)` + `panel.setMaximumHeight(650)` | 🔴 P0 |
| Q12b | **Timeline** | Onglet séparé dans la sidebar | Popup modale (`M3Dialog`) ouverte depuis le bouton « Chronologie » du composant | 🟡 P1 |

### Q13 — Dark Theme Validation Checklist

**Principe** : Après chaque création d'UI, basculer en thème dark et vérifier ces points.

| # | Vérification | Symptôme si KO | Correction |
|---|---|---|---|
| Q13a | **Texte des champs** | Texte noir sur fond sombre = illisible | Vérifier que `QDateEdit QLineEdit` a `color: {p.text_strong}` dans son QSS |
| Q13b | **Fond du scroll** | Viewport blanc visible entre les cartes | `viewport().setStyleSheet("background: transparent;")` + fond sur le widget contenu |
| Q13c | **Fond des cartes** | Cartes de la même couleur que le fond → pas de distinction | `surface` pour les cartes, `background` pour le fond — différence visible |
| Q13d | **Bordures** | Bordures invisibles (trop foncées) | `outline_variant` doit être plus clair que `background` en dark |
| Q13e | **Labels** | Labels illisibles (trop foncés) | `text_soft` pour les labels — assez contrasté en dark (vérifié dans les 4 palettes) |
| Q13f | **Tableaux** | Lignes de tableau invisibles | `ds.table_qss()` gère automatiquement les couleurs dark |

### Q14 — Responsive Grid pour Formulaires

**Principe** : Utiliser `QGridLayout` avec `setColumnStretch` pour des grilles responsives.
Les champs s'étirent pour remplir l'espace disponible.

```python
grid = QGridLayout()
grid.setSpacing(ds.space_md)
# 3 colonnes égales
grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1); grid.setColumnStretch(2, 1)
# Ligne 0 : 3 champs (un par colonne)
grid.addLayout(_field_row("Prénom", inp_prenom), 0, 0)
grid.addLayout(_field_row("Nom", inp_nom), 0, 1)
grid.addLayout(_field_row("Genre", inp_genre), 0, 2)
# Ligne 1 : champ pleine largeur (span 3 colonnes)
grid.addLayout(_field_row("Rue", inp_rue), 1, 0, 1, 3)
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q14a | **Colonnes fixes** | `setColumnWidth(0, 200)` ou largeurs en pixels | `setColumnStretch(i, 1)` — toutes les colonnes s'étirent également | 🟡 P1 |
| Q14b | **Span pleine largeur** | Champ étroit pour une donnée longue (ex: adresse) | `addLayout(row, r, 0, 1, N)` avec N = nombre total de colonnes | 🟢 P2 |
| Q14c | **Grid spacing** | `space_sm` (12px — trop serré pour une grille) | `space_md` (20px — Fibonacci, respiration entre les champs) | 🟡 P1 |
| Q14d | **Nombre optimal de colonnes** | Colonnes arbitraries sans logique de proportion | N = round(largeur_dispo / 233) où 233 = F₂₀ = `ds.sidebar_width`. Une colonne de ~233px est la largeur naturelle pour un champ + label. Si N > 3 → utiliser 3 colonnes max. | 🟢 P2 |

## Checklist Q7-Q14

- [ ] Q7 : Chaque section dans une `_section_card()` avec icône + titre + séparateur + ratio padding/contenu φ
- [ ] Q8 : Labels AU-DESSUS des champs, pas en `QFormLayout` + rythme Fibonacci des lignes (47px)
- [ ] Q9 : ≥ 5 sections → single-page scrollable avec header sticky `ds.header_height` + ratio header/contenu φ
- [ ] Q10 : `flat_input_qss()` uniquement sur les QLineEdit, pas sur QDateEdit/QComboBox
- [ ] Q11 : Save/Create dans le header (jamais dans le scroll)
- [ ] Q12 : Composants complexes intégrés avec min/max height
- [ ] Q13 : Test dark theme : texte, fonds, bordures, labels, tableaux
- [ ] Q14 : Grilles responsives avec `setColumnStretch` + N colonnes = round(largeur / 233)

---

## Sous-système Q15-Q21 — Système de Composition Spatiale M3+Fibonacci

Ces règles couvrent la DIVISION DE L'ESPACE et les PROPORTIONS GLOBALES.
Les tokens (Q1-Q14) définissent les briques — ces règles (Q15-Q21) définissent
COMMENT répartir l'espace pour produire une UI harmonieuse, équilibrée, et mathématiquement fondée.

### Q15 — Golden Ratio Layout System (φ ≈ 1.618)

**Principe fondateur** : Toute division spatiale majeure dans l'interface suit le nombre d'or
(φ ≈ 1.618) ou la séquence de Fibonacci. C'est le système nerveux de la composition —
il détermine COMMENT l'espace est réparti, pas quelles valeurs utiliser.

#### Q15a — Ratio Sidebar / Contenu

Tout layout master-detail (liste + fiche) divise l'espace horizontal selon :
- **Liste** (gauche) : `ds.sidebar_width` = 233px (F₂₀ = 233 dans la séquence 4,4,8,12,20,32,52,84,136,220...)
- **Contenu** (droite) : le reste de la largeur → ratio ~38/62 ≈ 1/φ

```python
# ✅ Pattern canonique master-detail
content = QHBoxLayout()
content.setSpacing(ds.space_md)
# Panneau liste — largeur fixe Fibonacci
liste = M3Card(variant=CardVariant.ELEVATED)
liste.setFixedWidth(ds.sidebar_width)  # 233px = F₂₀
content.addWidget(liste)
# Panneau détail — occupe le reste (~377px+)
detail = M3Card(variant=CardVariant.ELEVATED)
content.addWidget(detail, 1)  # stretch = 1 → ratio φ
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q15a | **Ratio sidebar/contenu** | Liste et détail en stretch égal (50/50) | Liste = `ds.sidebar_width` fixe, détail = stretch 1 → ratio ~38/62 ≈ 1/φ | 🔴 P0 |

#### Q15b — Ratio Header / Contenu

Le header sticky a une hauteur fixe basée sur Fibonacci :
- **Header** : `ds.header_height` = 52px = F₁₂
- **Ratio** : pour une fenêtre de ~900px, 52 / (900-52) ≈ 1/16 ≈ φ⁻⁴ — le header est un élément structurel proportionné

```python
# ✅ Header sticky (jamais dans le scroll)
header = QWidget()
header.setFixedHeight(ds.header_height)  # 52px = F₁₂
header.setStyleSheet(f"background: {ds.p.surface};")
# Le contenu scrollable prend le reste — ratio header/contenu ≈ φ⁻⁴
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q15b | **Header height** | Hauteur arbitraire (40px, 60px) | EXACTEMENT `ds.header_height` (52px = F₁₂) | 🔴 P0 |

#### Q15c — Card Proportions Internes

Une carte M3 bien proportionnée suit des ratios φ :
- **Padding externe** : `space_m3` = 16px (M3 standard)
- **Spacing interne** : `space_sm` = 12px (Fibonacci)
- **Ratio padding/spacing** : 16/12 ≈ 1.33 → proche de √φ (1.27)
- **Titre** : `s(16)` = title_medium = 16px
- **Contenu** : `s(14)` = body_medium = 14px
- **Ratio titre/contenu** : 16/14 ≈ 1.14 → proche de φ⁰·²⁵

```python
def _section_card(title: str, icon_name: str) -> tuple[M3Card, QVBoxLayout]:
    """Pattern canonique — proportions φ internes."""
    card = M3Card(variant=CardVariant.ELEVATED)
    card.setStyleSheet(
        f"M3Card {{ background: {ds.p.surface}; "
        f"border: 1px solid {ds.p.outline_variant}; "
        f"border-radius: {ds.radius_md}px; }}")
    cl = card.content_layout()
    # Padding M3 standard = 16px, spacing Fibonacci = 12px → ratio 16/12 ≈ √φ
    cl.setSpacing(ds.space_sm)    # 12px — Fibonacci
    cl.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)  # 16px — M3
    # En-tête : icône 20px + titre 16px — gap space_xs (8px = F₂)
    hdr = QHBoxLayout()
    hdr.setSpacing(ds.space_xs)   # 8px = F₂ — gap icône-texte
    icon_lbl = QLabel()
    icon_lbl.setPixmap(md3_icon(icon_name, color=ds.p.primary, size=20).pixmap(20, 20))
    hdr.addWidget(icon_lbl)
    title_lbl = M3Label(title, style="title_medium")  # 16px
    title_lbl.setStyleSheet(f"color: {ds.p.text_strong}; font-weight: bold;")
    hdr.addWidget(title_lbl)
    hdr.addStretch()
    cl.addLayout(hdr)
    # Séparateur subtil — 1px
    sep = M3Frame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {ds.p.outline_variant};")
    cl.addWidget(sep)
    return card, cl
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q15c | **Card proportions** | Padding = spacing (pas de hiérarchie) | Padding `space_m3`(16) / spacing `space_sm`(12) ≈ √φ + titre `s(16)` / contenu `s(14)` ≈ φ⁰·²⁵ | 🟡 P1 |

#### Q15d — Grille de Formulaire : Formule φ

Pour N colonnes dans un formulaire :
```
largeur_dispo = largeur_fenêtre - 2 × ds.space_md     # marges de page
gap_total     = (N - 1) × ds.space_md                   # espacement entre colonnes
largeur_col   = (largeur_dispo - gap_total) / N
```

La largeur optimale d'une colonne ≈ 233px (F₂₀) — assez pour un champ + label.
**Règle** : N = round(largeur_dispo / 233), clampé à [1, 3].

```python
# ✅ Calcul canonique du nombre de colonnes
largeur_dispo = largeur_fenetre - 2 * ds.space_md
N = max(1, min(3, round(largeur_dispo / 233)))  # 233 = F₂₀
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q15d | **Form grid columns** | Nombre de colonnes arbitraire | N = round(largeur_dispo / 233), clampé [1,3] | 🟡 P1 |

### Q16 — Page-Level Layout Templates

**Principe** : Trois templates canoniques couvrent 95% des interfaces Larc.
Chaque template est un pattern COMPLET que les agents peuvent copier et adapter.

#### Q16a — Master-Detail (Liste + Fiche)

Pour les écrans de recherche/consultation : liste à gauche, détail à droite.

```python
class MasterDetailView(ThemedWidget):
    """Template canonique master-detail M3+Fibonacci."""

    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # ── Barre de recherche + titre (header inline) ──
        header = QHBoxLayout()
        title = M3Label("Titre page", style="title_large")  # s(18)
        header.addWidget(title)
        header.addStretch()
        search = M3TextField(placeholder="Rechercher…")
        search.setFixedWidth(233)  # F₂₀
        header.addWidget(search)
        layout.addLayout(header)

        # ── Contenu master-detail ──
        content = QHBoxLayout()
        content.setSpacing(ds.space_md)  # 20px — Fibonacci

        # Panneau liste (gauche) — largeur fixe F₂₀
        self._list_panel = M3Card(variant=CardVariant.ELEVATED)
        self._list_panel.setFixedWidth(ds.sidebar_width)  # 233px
        # Tableau résultats avec Q1-Q4...
        content.addWidget(self._list_panel)

        # Panneau détail (droite) — stretch, ratio φ
        self._detail_panel = M3Card(variant=CardVariant.ELEVATED)
        # Contenu détail avec Q7 (section cards)...
        content.addWidget(self._detail_panel, 1)

        layout.addLayout(content, 1)
```

Ratio vertical : si la liste fait H de haut, le détail fait aussi H (même hauteur). La section de liste occupe ~38% de la largeur, le détail ~62% → ratio 1/φ.

#### Q16b — Full-Width Scrollable Form

Pour les formulaires d'édition (6+ champs) : header sticky + cartes scrollables.

```python
class FullWidthFormView(ThemedWidget):
    """Template canonique formulaire pleine page M3+Fibonacci."""

    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header STICKY (hors scroll) — Q9c + Q15b ──
        header = QWidget()
        header.setFixedHeight(ds.header_height)  # 52px = F₁₂
        header.setStyleSheet(f"background: {ds.p.surface}; "
                            f"border-bottom: 1px solid {ds.p.outline_variant};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(ds.space_md, ds.space_xs, ds.space_md, ds.space_xs)

        # Photo + nom
        photo = QLabel()
        photo.setFixedSize(ds.sp(SpacingToken.XXXL) + ds.sp(SpacingToken.MD),
                          ds.sp(SpacingToken.XXXL))  # 136+20=156 × 136
        header_layout.addWidget(photo)

        name = M3Label("Nom Prénom", style="title_large")  # s(18)
        header_layout.addWidget(name)
        header_layout.addStretch()

        # Actions — Q11
        cancel_btn = M3Button("Annuler", variant=ButtonVariant.OUTLINED)
        cancel_btn.setFixedHeight(ds.field_height + ds.space_xs)  # 40px
        header_layout.addWidget(cancel_btn)

        save_btn = M3Button("Sauvegarder", variant=ButtonVariant.FILLED)
        save_btn.setFixedHeight(ds.field_height + ds.space_xs)  # 40px
        header_layout.addWidget(save_btn)

        layout.addWidget(header)

        # ── Contenu scrollable — Q9a + Q9d ──
        scroll = M3ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background: transparent;")
        content = QWidget()
        content.setStyleSheet(f"background: {ds.p.background};")
        scroll.setWidget(content)

        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        scroll_layout.setSpacing(ds.space_md)  # 20px — Fibonacci, Q7e

        # Sections en cartes — Q7
        for section_title, icon_name, fields in SECTIONS:
            card, card_layout = _section_card(section_title, icon_name)
            grid = _build_form_grid(fields)  # Q14 + Q15d
            card_layout.addLayout(grid)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        layout.addWidget(scroll, 1)
```

#### Q16c — Dashboard Grid

Pour les tableaux de bord : grille de cartes en 2-3 colonnes.

```python
class DashboardView(ThemedWidget):
    """Template canonique dashboard M3+Fibonacci."""

    def _build_dashboard(self, cards_data):
        grid = QGridLayout()
        grid.setSpacing(ds.space_md)  # 20px — Fibonacci

        N = min(3, max(1, round(self.width() / 233)))  # Q15d
        for i in range(N):
            grid.setColumnStretch(i, 1)

        for idx, card_info in enumerate(cards_data):
            row, col = divmod(idx, N)
            card = self._build_kpi_card(card_info)
            # Hauteur minimum Fibonacci
            card.setMinimumHeight(144)  # F₁₂ = 144 (Fibonacci standard: 144)
            grid.addWidget(card, row, col)

        return grid
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q16a | **Master-Detail** | Liste + détail en 50/50 | Liste 233px fixe (F₂₀), détail stretch 1 → ratio 1/φ | 🔴 P0 |
| Q16b | **Full-Width Form** | Header sans sticky, actions dans le scroll | Header `ds.header_height` sticky + actions (Q11) hors scroll | 🔴 P0 |
| Q16c | **Dashboard** | Hauteurs de cartes arbitraires | Hauteur minimum 144px (F₁₂), N colonnes = round(largeur/233) | 🟡 P1 |

### Q17 — Vertical Rhythm (Fibonacci)

**Principe** : L'espacement vertical entre les blocs suit la séquence de Fibonacci.
Chaque changement de niveau hiérarchique saute de 2-3 crans dans l'échelle.

#### Q17a — Progression des espacements

L'échelle complète, du plus proche au plus éloigné :

```
space_xxs  =   4px   F₂  — gap icône-texte, label-champ
space_xs   =   8px   F₃  — gap standard entre widgets liés
space_sm   =  12px   F₄  — gap entre sous-sections proches
space_m3   =  16px   M3  — padding de carte, padding de dialogue
space_md   =  20px   F₅  — gap entre sections distinctes
space_lg   =  32px   F₆  — marge de page, gap entre groupes de sections
space_xl   =  52px   F₇  — hauteur header/bouton, gap entre zones majeures
space_xxl  =  84px   F₈  — marge de page large, séparation de zones
space_xxxl = 136px   F₉  — hero sections, séparation maximale
```

Le ratio entre deux niveaux consécutifs tend vers φ (ex: 84/52 ≈ 1.615, 52/32 ≈ 1.625).

#### Q17b — Règle du triple saut

Un changement de niveau hiérarchique saute de 2-3 crans :

| Transition | Saut | Ancien → Nouveau |
|---|---|---|
| Label → Champ | +1 | `space_xxs` (4) → lien direct |
| Champ → Champ suivant | +1 | `space_xs` (8) |
| Groupe de champs → Sous-section | +2 | `space_xs` (8) → `space_md` (20) |
| Sous-section → Section (carte) | +2 | `space_sm` (12) → `space_md` (20) |
| Section → Zone majeure | +3 | `space_md` (20) → `space_xl` (52) |

```python
# ✅ Exemple : rythme vertical dans un formulaire
layout.setSpacing(ds.space_md)        # 20px — entre cartes de section (saut +2)
card_layout.setSpacing(ds.space_sm)   # 12px — entre sous-sections (niveau intermédiaire)
field_grid.setSpacing(ds.space_md)    # 20px — entre colonnes
field_row.setSpacing(ds.space_xxs)    #  4px — label accolé au champ (niveau le plus proche)
```

#### Q17c — Interlignage φ

Tout texte multi-lignes utilise une hauteur de ligne = taille × φ :

```python
# ✅ Hauteur de ligne = font_size × φ
line_height = round(font_size * 1.618)
# Ex: s(14) → 14 × 1.618 ≈ 23px d'interligne
# Ex: s(13) → 13 × 1.618 ≈ 21px = ds.table_row_min
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q17a | **Progression espacements** | Mélange arbitraire de niveaux | Suivre l'échelle Fibo (4→8→12→20→32→52→84→136) avec ratio → φ | 🟡 P1 |
| Q17b | **Triple saut hiérarchique** | Même espacement partout (pas de hiérarchie visuelle) | Chaque changement de niveau saute 2-3 crans (ex: 8→20, 12→20, 20→52) | 🟡 P1 |
| Q17c | **Interlignage** | line-height arbitraire | Hauteur de ligne = round(font_size × 1.618) | 🟢 P2 |

### Q18 — Content Density Presets

**Principe** : Deux niveaux de densité au choix, selon le volume de données.
Chaque preset est un ensemble cohérent de tokens — ne jamais les mélanger.

#### Q18a — Comfortable (défaut)

Pour les formulaires, dashboards, pages avec < 20 éléments :

| Paramètre | Valeur | Token |
|---|---|---|
| Padding conteneur | 16px | `space_m3` |
| Spacing interne | 12px | `space_sm` |
| Hauteur ligne tableau | 21px | `table_row_min` |
| Hauteur champ | 32px | `field_height` |
| Hauteur bouton action | 40px | `field_height + space_xs` |
| Police standard | 14px | `s(14)` = body_medium |
| Police bouton | 13px | `s(13)` = label_large |
| Card spacing | 20px | `space_md` |

#### Q18b — Compact

Pour les tableaux denses (> 20 lignes), listes admin, vues de données :

| Paramètre | Valeur | Expression |
|---|---|---|
| Padding conteneur | 8px | `space_xs` |
| Spacing interne | 4px | `space_xxs` |
| Hauteur ligne tableau | 17px | `s(13) + 4` |
| Hauteur champ | 28px | `field_height - space_xxs` |
| Hauteur bouton action | 34px | `field_height + space_xxs` |
| Police standard | 13px | `s(13)` |
| Police bouton | 12px | `s(12)` |
| Card spacing | 12px | `space_sm` |

#### Q18c — Règle de choix

```python
if nombre_lignes > 20 or nombre_colonnes > 6:
    density = "compact"
elif is_form or nombre_champs < 10:
    density = "comfortable"  # défaut
else:
    density = "comfortable"
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q18a | **Comfortable** | Mixer les tokens des deux presets | Utiliser le set complet comfortable (16/12/21/32/40) | 🟡 P1 |
| Q18b | **Compact** | Appliquer compact à un formulaire (< 10 champs) | Réserver aux tableaux > 20 lignes, listes admin | 🟡 P1 |
| Q18c | **Choix densité** | Densité arbitraire, incohérente entre vues | > 20 lignes → compact ; formulaire → comfortable | 🟢 P2 |

### Q19 — Visual Weight & Balance

**Principe** : L'œil humain trouve naturellement harmonieux ce qui suit le nombre d'or.
Une interface bien équilibrée place son centre visuel au golden ratio vertical.

#### Q19a — Centre visuel au golden ratio

Le point focal naturel d'un écran est à ⅜ du haut (1/φ² ≈ 0.382) :
- Pour une fenêtre de 900px : centre visuel à ~344px du haut
- Les informations les plus importantes (nom, statut, KPIs) doivent être proches de ce point

```python
# ✅ Le header (52px) + la première section (~144px) placent le début
#    du contenu principal à ~200px du haut, proche du centre visuel pour
#    une fenêtre de ~600px de contenu utile.
```

#### Q19b — Placement des boutons d'action

Dans une barre d'action (header, footer, dialog button box) :
- **Actions secondaires** (Cancel, Retour) : à GAUCHE
- **Actions primaires** (Save, Créer, OK) : à DROITE
- Jamais l'inverse

```python
# ✅ Pattern canonique — Q11b + Q19b
action_bar = QHBoxLayout()
# Secondaire → gauche
cancel_btn = M3Button("Annuler", variant=ButtonVariant.OUTLINED)
action_bar.addWidget(cancel_btn)
action_bar.addStretch()  # séparation — le stretch crée un espace Fibo
# Primaire → droite
save_btn = M3Button("Sauvegarder", variant=ButtonVariant.FILLED)
action_bar.addWidget(save_btn)
```

#### Q19c — Ratio titre/contenu dans une card

Le rapport entre l'espace du titre et le corps dans une carte suit φ :

```python
# ✅ Card bien proportionnée
# Padding au-dessus du titre : space_m3 (16px)
# Titre : s(16) = 16px
# Gap titre-séparateur : space_sm (12px)
# Séparateur : 1px
# Gap séparateur-contenu : space_sm (12px)
# Contenu : s(14) = 14px
# Padding en-dessous : space_m3 (16px)
#
# Ratio espace_titre / espace_contenu ≈ (16+16+12+1) / (12+14+16) ≈ 45/42 ≈ 1.07
# → proche de φ⁰·¹⁵ : léger déséquilibre en faveur du titre = hiérarchie correcte
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q19a | **Centre visuel** | Infos critiques en bas de page | Éléments clés (nom, KPIs) proches du golden ratio vertical (~⅜ depuis le haut) | 🟢 P2 |
| Q19b | **Ordre des boutons** | Save à gauche, Cancel à droite | Secondaire (OUTLINED) → gauche, Primaire (FILLED) → droite, séparés par stretch | 🔴 P0 |
| Q19c | **Card title/content ratio** | Titre et contenu sans hiérarchie de poids | Espace titre légèrement > espace contenu (ratio ≈ 1.07), via le séparateur et les gaps | 🟢 P2 |

### Q20 — State & Feedback Patterns M3

**Principe** : Les états visuels (chargement, feedback, actions flottantes) suivent
les patterns Material Design 3 avec des dimensions basées sur Fibonacci.

#### Q20a — Skeleton Loading

Pour le chargement initial, avant que les données n'arrivent :

```python
def _build_skeleton(self) -> QWidget:
    """Skeleton loader — animation de chargement M3."""
    skeleton = QWidget()
    layout = QVBoxLayout(skeleton)
    layout.setSpacing(ds.space_sm)

    # Avatar placeholder — cercle surface_variant
    avatar_size = 89  # F₁₉ ≈ theme_manager.image.logo
    avatar = QLabel()
    avatar.setFixedSize(avatar_size, avatar_size)
    avatar.setStyleSheet(
        f"background: {ds.p.surface_variant}; "
        f"border-radius: {avatar_size // 2}px;")

    # Barres de texte — largeurs Fibonacci décroissantes
    bar_widths = [233, 144, 89]  # F₂₀, F₁₉, F₁₈
    bars = []
    for w in bar_widths:
        bar = QFrame()
        bar.setFixedSize(w, 14)  # hauteur = body_medium
        bar.setStyleSheet(
            f"background: {ds.p.surface_variant}; "
            f"border-radius: {ds.radius_sm}px;")
        bars.append(bar)

    # ... assemblage dans le layout
    return skeleton
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q20a | **Skeleton** | Écran vide sans indication de chargement | Avatar cercle F₁₉(89) + barres largeurs Fibo (233, 144, 89), fond `surface_variant` | 🟡 P1 |

#### Q20b — Snackbar / Toast

Pour les notifications éphémères (succès, erreur, info) :

```python
def _show_snackbar(self, message: str, duration_ms: int = 4000):
    """Snackbar M3 — barre de notification en bas de l'écran."""
    snackbar = M3Frame()
    snackbar.setObjectName("snackbar")
    snackbar.setFixedHeight(48)  # M3 standard (proche de F₁₂=52 moins space_xxs)
    snackbar.setMaximumWidth(344)  # M3 standard (~F₂₂ = 377 arrondi)
    snackbar.setStyleSheet(f"""
        M3Frame#snackbar {{
            background: {ds.p.inverse_surface};
            color: {ds.p.inverse_on_surface};
            border-radius: {ds.radius_sm}px;
            padding: {ds.space_xs}px {ds.space_m3}px;
        }}
    """)
    # Position : bottom-center avec margin space_lg
    # Auto-fermeture après duration_ms
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q20b | **Snackbar** | QMessageBox modal pour un feedback non-bloquant | Snackbar 48px haut, max 344px large, fond `inverse_surface`, auto-fermeture | 🟡 P1 |

#### Q20c — FAB (Floating Action Button)

Pour l'action principale d'un écran (créer, ajouter) :

```python
# ✅ FAB — bouton circulaire en bas à droite
fab = M3Button("+", variant=ButtonVariant.FILLED)
fab.setFixedSize(56, 56)  # F₁₃(52) + space_xxs(4) = 56 — M3 standard
fab.setStyleSheet(f"""
    M3Button {{
        background: {ds.p.primary_container};
        color: {ds.p.on_primary_container};
        border: none;
        border-radius: {56 // 2}px;  # cercle parfait
        font-size: {theme_manager.font_size(24)}px;  # icon large
    }}
    M3Button:hover {{
        background: {ds.p.primary};  # state layer → élévation
        color: {ds.p.on_primary};
    }}
""")
# Position : bottom-right
# Margin depuis le bord : ds.space_lg (32px = F₆)
```

**Règle de décision FAB vs bouton header :**

| Contexte | Choix | Raison |
|---|---|---|
| Écran de liste (recherche élèves) | Bouton "+" dans le header | Action secondaire, la recherche est primaire |
| Écran de création (nouvelle fiche) | PAS de FAB | Save est dans le header sticky |
| Dashboard, vue d'ensemble | FAB si UNE action domine | L'action principale est toujours visible |

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q20c | **FAB** | FAB sur un écran de formulaire (conflit avec Save header) | FAB 56×56, bottom-right, margin `space_lg`, UNIQUEMENT si l'action est l'action PRINCIPALE de l'écran | 🟢 P2 |

### Q21 — Template Canonique : Formulaire d'Édition Complet

**Principe** : Ce template est le **fichier de référence** pour toute création de formulaire
d'édition dans Larc. Il intègre TOUTES les règles Q7-Q21 en un seul code complet et copiable.
C'est l'équivalent de `parent_manager.py` pour les vues de liste.

```python
# =============================================================================
# TEMPLATE CANONIQUE — Formulaire d'édition M3+Fibonacci (Q7-Q21)
# Fichier de référence pour tout nouveau formulaire Larc
# =============================================================================
from larccommon.design_system import ds
from larccommon.icons import icon as md3_icon
from larccommon.l10n import _
from larccommon.safe_slot import safe_slot
from larccommon.theme import theme_manager
from larccommon.widgets.themed_widget import ThemedWidget
from phibuilder.phi.scale import SpacingToken
from phibuilder.widgets import (
    M3Button, M3Card, M3ComboBox, M3DateEdit, M3Frame,
    M3Label, M3ScrollArea, M3TextField,
)
from phibuilder.widgets.button import ButtonVariant
from phibuilder.widgets.card import CardVariant
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)


# ── Helper: Section Card (Q7 + Q15c) ──
def _section_card(title: str, icon_name: str) -> tuple[M3Card, QVBoxLayout]:
    """Pattern canonique — carte de section avec proportions φ."""
    card = M3Card(variant=CardVariant.ELEVATED)
    card.setStyleSheet(
        f"M3Card {{ background: {ds.p.surface}; "
        f"border: 1px solid {ds.p.outline_variant}; "
        f"border-radius: {ds.radius_md}px; }}")  # Q7b
    cl = card.content_layout()
    # Q7d+Q7f : padding/spacing en ratio √φ
    cl.setSpacing(ds.space_sm)     # 12px — Fibonacci
    cl.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)  # 16px — M3
    # Q7c : icône 20px + titre 16px + séparateur 1px
    hdr = QHBoxLayout()
    hdr.setSpacing(ds.space_xs)    # 8px — Fibonacci
    icon_lbl = QLabel()
    icon_lbl.setPixmap(md3_icon(icon_name, color=ds.p.primary, size=20).pixmap(20, 20))
    hdr.addWidget(icon_lbl)
    title_lbl = M3Label(title, style="title_medium")  # s(16)
    title_lbl.setStyleSheet(f"color: {ds.p.text_strong}; font-weight: bold;")
    hdr.addWidget(title_lbl)
    hdr.addStretch()
    cl.addLayout(hdr)
    sep = M3Frame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {ds.p.outline_variant};")
    cl.addWidget(sep)
    return card, cl


# ── Helper: Field Row (Q8 + Q8e) ──
def _field_row(label: str, widget, is_date: bool = False) -> QVBoxLayout:
    """Pattern canonique — label AU-DESSUS du champ, rythme Fibo 47px."""
    row = QVBoxLayout()
    row.setSpacing(ds.space_xxs)   # Q8c : 4px — lien visuel fort
    lbl = M3Label(label, style="label_small")  # s(11)
    lbl.setStyleSheet(f"color: {ds.p.text_soft}; font-weight: bold;")  # Q8b
    row.addWidget(lbl)
    widget.setMinimumHeight(ds.field_height)  # 32px
    if not is_date:
        widget.setStyleSheet(ds.flat_input_qss())
    row.addWidget(widget)
    # Total ligne = 11 + 4 + 32 = 47px → proche F₁₀(55) - space_xs(8) — Q8e
    return row


# ── Helper: Grille de formulaire (Q14 + Q15d) ──
def _build_form_grid(fields: list[tuple[str, QWidget, bool]], parent_width: int = 900) -> QGridLayout:
    """Construit une grille responsive avec Q14 + Q15d."""
    largeur_dispo = parent_width - 2 * ds.space_md
    N = max(1, min(3, round(largeur_dispo / 233)))  # Q15d
    grid = QGridLayout()
    grid.setSpacing(ds.space_md)   # Q14c
    for i in range(N):
        grid.setColumnStretch(i, 1)  # Q14a

    for idx, (label, widget, is_date) in enumerate(fields):
        row, col = divmod(idx, N)
        field_layout = _field_row(label, widget, is_date)
        # Si champ long (adresse, notes) → span pleine largeur — Q14b
        if col == 0 and idx == len(fields) - 1 and len(fields) % N == 1:
            grid.addLayout(field_layout, row, 0, 1, N)
        else:
            grid.addLayout(field_layout, row, col)

    return grid


# ── CLASSE PRINCIPALE ──
class EditFormView(ThemedWidget):
    """Template canonique de formulaire d'édition M3+Fibonacci.

    Intègre : Q7 (section cards), Q8 (labels dessus), Q9 (scrollable),
    Q10 (QSS spécifique), Q11 (actions header), Q13 (dark theme),
    Q14 (grille responsive), Q15 (ratios φ), Q16b (full-width form),
    Q17 (rythme vertical), Q18 (comfortable), Q19 (boutons ordonnés).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        ds.theme_changed.connect(self._restyle)  # D6
        self._init_ui()

    # ── QSS global (J4 + D1b) ──
    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design
        s = theme_manager.font_size
        return f"""
            QWidget#edit_form_root {{
                background: {p.background};
                color: {p.text_strong};           /* D1b */
            }}
            QWidget#sticky_header {{
                background: {p.surface};
                color: {p.text_strong};           /* D1b */
                border-bottom: 1px solid {p.outline_variant};
            }}
            QWidget#scroll_content {{
                background: {p.background};
                color: {p.text_strong};           /* D1b */
            }}
        """

    def _init_ui(self):
        self.setObjectName("edit_form_root")
        self.setStyleSheet(self._STYLE())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ═══ HEADER STICKY (Q9c + Q11 + Q15b + Q19b) ═══
        header = QWidget()
        header.setObjectName("sticky_header")
        header.setFixedHeight(ds.header_height)  # 52px = F₁₂ — Q15b
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(ds.space_md, ds.space_xs, ds.space_md, ds.space_xs)

        # Photo + identité
        photo = QLabel()
        photo.setFixedSize(ds.sp(SpacingToken.XXXL) + ds.sp(SpacingToken.MD),
                          ds.sp(SpacingToken.XXXL))  # 156×136
        photo.setStyleSheet(
            f"background: {ds.p.primary_container}; "
            f"border-radius: {ds.radius_sm}px;")
        photo.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(photo)

        name_lbl = M3Label("—", style="title_large")  # s(18)
        name_lbl.setStyleSheet(f"color: {ds.p.text_strong}; font-weight: bold;")
        header_layout.addWidget(name_lbl)
        header_layout.addStretch()

        # Q19b : secondaire gauche, primaire droite
        cancel_btn = M3Button(_("cancel"), variant=ButtonVariant.OUTLINED)
        cancel_btn.setFixedHeight(ds.field_height + ds.space_xs)  # 40px — Q11d
        header_layout.addWidget(cancel_btn)

        save_btn = M3Button(_("save"), variant=ButtonVariant.FILLED)
        save_btn.setFixedHeight(ds.field_height + ds.space_xs)  # 40px — Q11d
        header_layout.addWidget(save_btn)

        layout.addWidget(header)

        # ═══ SCROLL CONTENT (Q9a + Q9d + Q16b) ═══
        scroll = M3ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background: transparent;")  # Q9d
        content = QWidget()
        content.setObjectName("scroll_content")
        scroll.setWidget(content)

        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        scroll_layout.setSpacing(ds.space_md)  # 20px — Q7e + Q17b (saut +2)

        # Sections — une carte par groupe logique (Q7)
        for section_title, icon_name, fields in self.SECTIONS:
            card, card_layout = _section_card(section_title, icon_name)
            grid = _build_form_grid(fields, parent_width=900)
            card_layout.addLayout(grid)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        layout.addWidget(scroll, 1)

        # Stocker les références pour _restyle (D7)
        self._header = header
        self._photo = photo
        self._name_lbl = name_lbl
        self._cancel_btn = cancel_btn
        self._save_btn = save_btn
        self._scroll = scroll
        self._content = content

    # ── Restyle (Q5 + D7) ──
    @safe_slot("EditFormView._restyle")
    def _restyle(self):
        self.setStyleSheet(self._STYLE())
        p = theme_manager.palette
        if hasattr(self, "_photo"):
            self._photo.setStyleSheet(
                f"background: {p.primary_container}; "
                f"border-radius: {ds.radius_sm}px;")
        if hasattr(self, "_name_lbl"):
            self._name_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        if hasattr(self, "_content"):
            self._content.setStyleSheet(f"background: {p.background}; color: {p.text_strong};")
        # Q9d : maintenir viewport transparent après changement de thème
        if hasattr(self, "_scroll"):
            self._scroll.viewport().setStyleSheet("background: transparent;")

    # ── Sections à définir par la sous-classe ──
    SECTIONS: list[tuple[str, str, list[tuple[str, QWidget, bool]]]] = []
```

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| Q21a | **Template formulaire** | Créer un formulaire sans structure Q7-Q21 | Copier ce template, remplacer SECTIONS, adapter les champs | 🔴 P0 |
| Q21b | **Header sticky** | Header absent ou dans le scroll | Header `ds.header_height` avec photo + nom + actions (Q19b) hors scroll | 🔴 P0 |
| Q21c | **Sections en cartes** | Champs sans regroupement logique | Une carte Q7 par groupe logique (identité, adresse, contacts...) | 🟡 P1 |

---

## Checklist Q15-Q21

- [ ] Q15 : Ratio sidebar/contenu = `ds.sidebar_width` / stretch 1 → 1/φ
- [ ] Q15 : Header = EXACTEMENT `ds.header_height` (52px = F₁₂)
- [ ] Q15 : Card padding/spacing = 16/12 ≈ √φ ; titre/contenu = 16/14 ≈ φ⁰·²⁵
- [ ] Q15 : Grille formulaire : N = round(largeur / 233), clampé [1,3]
- [ ] Q16 : Master-Detail avec liste F₂₀ fixe + détail stretch 1
- [ ] Q16 : Full-Width Form avec header sticky + scroll content
- [ ] Q16 : Dashboard avec hauteur min 144px (F₁₂), N colonnes = round(largeur/233)
- [ ] Q17 : Progression espacements suit l'échelle Fibo (4→8→12→20→32→52→84→136)
- [ ] Q17 : Sauts hiérarchiques de 2-3 crans (jamais 1 seul cran entre niveaux)
- [ ] Q17 : Interlignage = round(font_size × 1.618)
- [ ] Q18 : Densité comfortable (16/12/21/32) pour formulaires et dashboards
- [ ] Q18 : Densité compact (8/4/17/28) pour tableaux > 20 lignes
- [ ] Q19 : Centre visuel au golden ratio (~⅜ depuis le haut) pour les infos clés
- [ ] Q19 : Boutons : secondaire GAUCHE, primaire DROITE, séparés par stretch
- [ ] Q20 : Skeleton avec largeurs Fibo (233, 144, 89) si chargement > 500ms
- [ ] Q20 : Snackbar (48px haut, 344px large) pour feedback non-bloquant
- [ ] Q20 : FAB 56×56 bottom-right UNIQUEMENT si action principale de l'écran
- [ ] Q21 : Tout nouveau formulaire copie le template canonique Q21

---

## Step by Step — Création d'un nouveau formulaire (Q7-Q21)

| Ordre | Action | Règle |
|---|---|---|
| 1 | Copier le template Q21 dans un nouveau fichier | Q21a |
| 2 | Définir `SECTIONS` : liste de (titre, icône, [(label, widget, is_date)]) | Q7, Q21c |
| 3 | Construire le header sticky avec photo + nom + actions | Q9c, Q11, Q15b, Q19b |
| 4 | Construire le scroll avec une carte par section | Q9a, Q9d |
| 5 | Dans chaque carte, utiliser `_build_form_grid()` pour la grille | Q14, Q15d |
| 6 | Pour les QDateEdit/QComboBox, utiliser le QSS dédié (pas flat_input_qss) | Q10 |
| 7 | Connecter `ds.theme_changed.connect(self._restyle)` | D6, Q5 |
| 8 | Implémenter `_restyle()` : QSS global + chaque widget inline + viewport | D7, Q13 |
| 9 | Vérifier le rythme vertical : sauts de 2-3 crans entre niveaux | Q17b |
| 10 | Vérifier la densité : comfortable par défaut (16/12/21/32) | Q18a |
| 11 | Test dark theme : Q13a-Q13f | Q13 |
| 12 | Lancer les linters | Vérification |

---

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.*, s(), theme_manager.image.*
- **[color-rules](../color-rules/SKILL.md)** — D1 (couleur explicite), D6/D7 (restyle)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + _restyle_all
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — Règles R1-R17, zéro pixel littéral
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — Spécification visuelle du sidebar
- **[card-dashboard](../card-dashboard/SKILL.md)** — Pattern de dashboard avec KPI cards
