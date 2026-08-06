---
skill: form-pattern
version: "1.0"
priority: P0
category: page-pattern
depends_on: [design-tokens, color-rules, zero-hardcoding, theme-reactivity]
applies_to: [LarcSecretaire, LarcSuperviseur, LarcProf]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer, feature-reviewer]
subsystems: [FP]
---

# Skill: Form Pattern — Formulaire par Sections avec Validation

## 0. Contexte

**Projet** : Tous les modules Larc avec formulaires complexes (fiche eleve, creation, preferences)
**Fichiers de reference** :
  - `LarcSecretaire/views/student_form.py::StudentEditDialog` — formulaire multi-sections
  - `LarcSecretaire/views/student_form.py::StudentCreateDialog` — formulaire de creation
  - `LarcSecretaire/views/parent_manager.py::ParentEditDialog` — formulaire simple
**Utilisateurs** : Developpeurs de formulaires ET agents IA

Ce skill definit le **pattern canonique de formulaire** : sections en cartes scrollables,
bandeau de validation fixe, et helpers de construction reutilisables.

## 1. Fonction Principale

### Type : Systeme Ferme

**Entree** : Un dialogue ou widget vide
**Sortie** : Un formulaire structure avec sections, validation nominative, et scroll
**Traitement** : Appliquer le patron FP1-FP14 dans l'ordre

## 2. Architecture spatiale obligatoire

```
┌──────────────────────────────────────────────────────────────────────┐
│ FP1 — TITRE (title_small)                                            │
├──────────────────────────────────────────────────────────────────────┤
│ FP2 — HEADER ELEVE (photo + nom + actions)                           │
│ ┌──────────┬──────────────────────────────────┬────────────────────┐ │
│ │ PHOTO    │ Prénom NOM          [PDF] [Word] │ [Enregistrer]      │ │
│ │ 120×120  │ Classe · ID                       │ [Annuler]         │ │
│ │          │                                    │                    │ │
│ └──────────┴──────────────────────────────────┴────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ FP3 — BANDEAU DE VALIDATION (fixe, toujours visible)                 │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ☑ Dossier complet    ☐ Sans parent   ☐ Sans photo   ☐ Sans email │ │
│ │ Validé par M.Dupont   Non vérifié      Non vérifié     Non vérifié│ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ FP4 — SCROLL AREA (le reste)                                         │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ FP5 — SECTION CARTE (M3Card + icone + titre + separateur)       │ │
│ │ ┌────────────────────────────────────────────────────────────┐   │ │
│ │ │ 🏫 Identité                                          │   │ │
│ │ │ ─────────────────────────────────────────────────── │   │ │
│ │ │ Nom         │ Prenom      │ Genre                    │   │ │
│ │ │ Date entree │ Date arrivee│ Date naissance           │   │ │
│ │ └────────────────────────────────────────────────────────────┘   │ │
│ │                                                                  │ │
│ │ 🏠 Adresse                                                       │ │
│ │ 📞 Contact                                                       │ │
│ │ 👤 Parents (tableau + boutons)                                   │ │
│ │ 📂 Dossiers                                                      │ │
│ │ 📅 Evenements                                                    │ │
│ │ 📷 Photos                                                        │ │
│ │ 🏫 Bulletins                                                     │ │
│ │ 🔒 Confidentiel (restreint)                                      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Table des regles FP

| # | Regle | Interdit | Obligatoire | Priorite |
|---|---|---|---|---|
| FP1 | **Titre** en haut | title_large ou absent | `title_small` | P0 |
| FP2 | **Header** photo + nom + actions | Actions en bas du scroll | Photo 120x120, Prenom+Nom en headline_large+title_large, boutons a droite | P0 |
| FP3 | **Bandeau de validation** fixe | Checkboxes en bas du scroll (section 10) | QFrame fixe entre le header et le scroll, 4 checkboxes + labels "Valide par X" ou "Non verifie" | P0 |
| FP4 | **Scroll area** pour le contenu | Mettre tout dans un layout non scrollable | `M3ScrollArea` avec `setWidgetResizable(True)`, viewport transparent (R16) | P0 |
| FP5 | **Sections en cartes** | Layouts sans conteneur | Chaque section = `M3Card(ELEVATED)` avec icone + titre + separateur | P0 |
| FP6 | **Helpers** `_section_card()` et `_field_row()` | Dupliquer le code de carte | Deux helpers dedies — un pour la carte, un pour label+champ | P0 |
| FP7 | **Grille de champs** responsive | Champs en colonne unique | `QGridLayout` avec `setColumnStretch` egal pour chaque colonne | P1 |
| FP8 | **Tailles uniformes** | Hauteurs de champ variables | Tous les champs `setFixedHeight(ds.field_height)`, sauf TextEdit = `sp(XXXL)` | P0 |
| FP9 | **QSS uniforme** via helper | `setStyleSheet` inline different par champ | `ds.flat_input_qss()` pour les TextField, QSS date dedie pour les DateEdit | P0 |
| FP10 | **Tableau parents** | Absent ou non interactif | `M3TableWidget` avec boutons Ajouter/Modifier/Supprimer, `setMaximumHeight(sp(XXXL))` | P1 |
| FP11 | **Tableau evenements** | Sans validation visuelle | Colonnes: Date, Type, Note, Auteur, Valide, avec couleurs par type d'evenement | P1 |
| FP12 | **Restriction par role** | Tout le monde voit tout | `UserRole` check avant d'afficher les sections confidentielles | P1 |
| FP13 | **Sauvegarde + indicateur dirty** | Bouton Enregistrer inactif | `_mark_dirty()` → change le texte du bouton ("Enregistrer" → "Enregistrer les modifications") | P0 |
| FP14 | **Reactivite au theme** | `_restyle` ne touche pas les cartes | `_restyle()` re-applique le QSS de TOUTES les cartes + champs + tables | P0 |

## 3. Code canonique

### Helpers de construction

```python
def _section_card(title: str, icon_name: str):
    """Carte de section avec icone + titre + separateur."""
    card = M3Card(variant=CardVariant.ELEVATED)
    card.setStyleSheet(
        f"M3Card {{ background: {ds.p.surface}; "
        f"border: 1px solid {ds.p.outline_variant}; "
        f"border-radius: {ds.radius_md}px; }}")
    cl = card.content_layout()
    cl.setSpacing(ds.space_sm)
    cl.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
    # FP6 : en-tete de carte
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
    # FP6 : separateur
    sep = M3Frame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {ds.p.outline_variant};")
    cl.addWidget(sep)
    return card, cl

def _field_row(label: str, widget, is_date: bool = False):
    """Label au-dessus du champ."""
    row = QVBoxLayout()
    row.setSpacing(ds.space_xxs)
    lbl = M3Label(label, style="label_small")
    lbl.setStyleSheet(f"color: {ds.p.text_soft}; font-weight: bold;")
    row.addWidget(lbl)
    widget.setMinimumHeight(ds.field_height)  # FP8
    if not is_date:
        widget.setStyleSheet(ds.flat_input_qss())  # FP9
    row.addWidget(widget)
    return row
```

### Bandeau de validation (FP3)

```python
# Construit en dehors du scroll, ajoute avant le scroll dans le layout
self._val_banner = QWidget()
self._val_banner.setStyleSheet(
    f"background: {ds.p.surface_variant}; border: 1px solid {ds.p.outline_variant}; "
    f"border-radius: {ds.radius_md}px; padding: {ds.space_sm}px;")
val_layout = QHBoxLayout(self._val_banner)
val_layout.setSpacing(ds.space_md)
val_layout.setContentsMargins(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm)

_CHECK_LABELS = {
    "dossier_valid": ("sec_main.kpi.no_doc",    "student_form.check_dossier"),
    "parent_valid":  ("sec_main.kpi.no_parent",  "student_form.check_parent"),
    "photo_valid":   ("sec_main.kpi.no_photo",   "student_form.check_photo"),
    "email_valid":   ("sec_main.kpi.no_email",   "student_form.check_email"),
}

self._val_items: dict[str, tuple[QCheckBox, M3Label]] = {}
for key, label, _icon in [
    ("dossier_valid", "Doss. incomplets", "description"),
    ("parent_valid",  "Sans parent", "person"),
    ("photo_valid",   "Sans photo", "image"),
    ("email_valid",   "Sans email", "mail"),
]:
    item_box = QVBoxLayout()
    item_box.setSpacing(ds.space_xxs)
    item_box.setAlignment(Qt.AlignCenter)
    cb = QCheckBox(label)
    cb.toggled.connect(lambda checked, k=key: self._on_flag_toggled(k, checked))
    item_box.addWidget(cb, 0, Qt.AlignCenter)
    who_lbl = M3Label("Non verifie", style="label_small")
    who_lbl.setStyleSheet(f"color: {ds.p.text_disabled};")
    who_lbl.setAlignment(Qt.AlignCenter)
    item_box.addWidget(who_lbl, 0, Qt.AlignCenter)
    val_layout.addLayout(item_box)
    self._val_items[key] = (cb, who_lbl)

# Ajout au layout PRINCIPAL (pas dans le scroll)
layout.addWidget(self._val_banner)   # fixe, toujours visible
layout.addWidget(scroll, 1)         # defile
```

### Checkbox dynamique — le texte change

```python
def _on_flag_toggled(self, key: str, checked: bool):
    # ... ecriture DB JSONB ...
    if key in self._val_items:
        _cb, who_lbl = self._val_items[key]
        prob_key, ok_key = _CHECK_LABELS.get(key, (None, None))
        # FP3 : le texte reflete l'etat
        if prob_key and ok_key:
            _cb.setText(_(ok_key) if checked else _(prob_key))
            _cb.setStyleSheet(
                f"color: {ds.p.success if checked else ds.p.error}; "
                f"font-size: {ds.font_label_lg}px; spacing: {ds.space_xs}px; font-weight: bold;")
        if checked:
            who_lbl.setText(_("student_form.validated_by").format(name=session.full_name))
            who_lbl.setStyleSheet(f"color: {ds.p.success}; font-weight: bold;")
        else:
            who_lbl.setText(_("student_form.not_validated"))
            who_lbl.setStyleSheet(f"color: {ds.p.text_disabled};")
```

### Sauvegarde avec indicateur (FP13)

```python
def _mark_dirty(self):
    if not self._dirty:
        self._dirty = True
        self._update_save_indicator()

def _update_save_indicator(self):
    if self._dirty:
        self._save_btn.setText("Enregistrer les modifications")
    else:
        self._save_btn.setText("Enregistrer")
```

### Reactivite au theme (FP14)

```python
def _restyle(self):
    section_style = (
        f"M3Card {{ background: {ds.p.surface}; "
        f"border: 1px solid {ds.p.outline_variant}; "
        f"border-radius: {ds.radius_md}px; }}")
    for card in getattr(self, "_section_cards", []):
        card.setStyleSheet(section_style)
    for w in self._inp_fields():
        w.setStyleSheet(ds.flat_input_qss())
    for w in self._date_fields():
        w.setStyleSheet(f"border: 1px solid {ds.p.outline}; ...")
    # Bandeau de validation
    if hasattr(self, "_val_banner"):
        self._val_banner.setStyleSheet(
            f"background: {ds.p.surface_variant}; ...")
    # Header
    for lbl in (self._id_prenom, self._id_nom, self._id_classe, self._id_id):
        lbl.setStyleSheet(f"color: {ds.p.text_strong};")
```

## 5. Step by Step

1. Creer le titre (FP1)
2. Creer le header avec photo + nom + boutons (FP2)
3. Creer le bandeau de validation fixe (FP3)
4. Creer la scroll area (FP4)
5. Pour chaque section : `_section_card()` + grille de champs via `_field_row()` (FP5-FP7)
6. Appliquer `ds.flat_input_qss()` et tailles uniformes (FP8-FP9)
7. Ajouter les tableaux parents et evenements (FP10-FP11)
8. Gerer les restrictions par role (FP12)
9. Implementer `_mark_dirty()` et `_update_save_indicator()` (FP13)
10. Connecter `theme_changed` → `_restyle()` (FP14)

## 6. Checklist

- [ ] FP1 : titre en title_small
- [ ] FP2 : header photo 120×120 + Prenom NOM + boutons d'action
- [ ] FP3 : bandeau de validation fixe avant le scroll, texte dynamique
- [ ] FP4 : contenu dans M3ScrollArea, viewport transparent (R16)
- [ ] FP5 : chaque section = M3Card avec icone + titre + separateur
- [ ] FP6 : helpers `_section_card()` et `_field_row()` reutilises
- [ ] FP7 : QGridLayout avec stretch egal par colonne
- [ ] FP8 : tous les champs FixedHeight ds.field_height
- [ ] FP9 : flat_input_qss() sur TextField, QSS date sur DateEdit
- [ ] FP10 : tableau parents avec boutons Ajouter/Modifier/Supprimer
- [ ] FP11 : tableau evenements avec couleurs par type
- [ ] FP12 : sections restreintes cachees par UserRole
- [ ] FP13 : indicateur dirty + bouton Enregistrer qui change
- [ ] FP14 : _restyle() couvre TOUTES les cartes, champs, tables
- [ ] 0 hex hardcode — tout via ds.p.*
- [ ] 0 pixel litteral — tout via tokens
- [ ] Toutes les checkboxes ont color: explicite (D1)

## References croisees

- **[design-tokens](../design-tokens/SKILL.md)** — ds.field_height, ds.space_m3, ds.space_xxxl
- **[color-rules](../color-rules/SKILL.md)** — D1, D3, D5 (couleurs explicites)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — FP14 pattern _restyle
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R1-R11
- **[toolkit-reference](../toolkit-reference/SKILL.md)** — M3Card, M3ComboBox, M3DateEdit
- **[student-record](../student-record/SKILL.md)** — Categories du dossier eleve
