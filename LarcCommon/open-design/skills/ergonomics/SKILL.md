---
skill: ergonomics
version: "1.0"
priority: P1
category: design
depends_on: [design-tokens, color-rules, theme-reactivity]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf]
linters: [lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [Q]
---

# Skill: Ergonomics — Fenêtres de Liste

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof)
**Fichier de référence** : `LarcSecretaire/views/parent_manager.py` — 0 hardcoded ✅
**Utilisateurs** : Développeurs de vues de liste/recherche
**Dépendances** : `design-tokens`, `color-rules`, `theme-reactivity`

Ce skill garantit une ergonomie cohérente pour toutes les fenêtres de liste (recherche d'élèves, tableaux, sélecteurs).

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Fenêtre de liste sans hover, sans état vide, sans clavier, sans affordance
**Sortie** : Fenêtre avec retour visuel M3 complet (hover, empty state, keyboard, tooltips)
**Traitement** : Appliquer Q1-Q6

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
| 9 | Lancer `lint_qss_hardcoding.py` — doit passer Q1+Q3+Q2 | Vérification |

## 6. Checklist

- [ ] Q1 : `viewport().setCursor(Qt.PointingHandCursor)` sur chaque table interactive
- [ ] Q1 : `::item:hover` dans le QSS de chaque table interactive
- [ ] Q2 : 0 `QMessageBox.information` avec message d'état vide
- [ ] Q2 : `_empty_state` widget (icône + message) présent et fonctionnel
- [ ] Q3 : `installEventFilter(self)` sur les tables interactives
- [ ] Q3 : `eventFilter` gère `Qt.Key_Return`/`Qt.Key_Enter`
- [ ] Q3 : `showEvent` → `setFocus()` sur le champ de recherche
- [ ] Q4 : `setToolTip` sur les zones cliquables (photo, actions)
- [ ] Q5 : `_restyle_all` ré-applique le QSS hover + couleur état vide
- [ ] Q6 : Clés `student_form.searching`, `.search_no_results`, `.open_file` dans fr.json ET en.json
- [ ] `python scripts/lint_qss_hardcoding.py` → 0 violation Q1+Q3+Q2

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.table_qss(), ds.p.*, theme_manager.font_size()
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _restyle_all (Q5)
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R10 (pas de alternatingRowColors)
- **[testing](../testing/SKILL.md)** — Tests des états vides
