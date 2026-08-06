---
skill: search-detail-pattern
version: "1.0"
priority: P0
category: page-pattern
depends_on: [design-tokens, color-rules, zero-hardcoding, theme-reactivity, ergonomics]
applies_to: [LarcSecretaire, LarcSuperviseur, LarcProf]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer, feature-reviewer]
subsystems: [SD]
---

# Skill: Search-Detail Pattern — Recherche + Fiche Detail

## 0. Contexte

**Projet** : Tous les modules Larc avec recherche d'entites (eleves, parents, professeurs)
**Fichier de reference** : `LarcSecretaire/views/student_form.py::StudentForm` — implementation de reference
**Utilisateurs** : Developpeurs de vues de recherche ET agents IA

Ce skill definit le **pattern canonique de page recherche + detail** pour toutes les applis Larc.
Quelle que soit l'entite recherchee, la structure de page est identique.

## 1. Fonction Principale

### Type : Systeme Ferme

**Entree** : Une page blanche
**Sortie** : Une interface de recherche avec barre, resultats en tableau, et panneau detail
**Traitement** : Appliquer le patron SD1-SD10 dans l'ordre

## 2. Architecture spatiale obligatoire

```
┌──────────────────────────────────────────────────────────────────────┐
│ SD1 — TITRE + ACTION                                                 │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ M3Label "Recherche eleves"                [+] bouton action      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ SD2 — BARRE DE RECHERCHE (2 champs + bouton)                         │
│ ┌────────────────────┬────────────────────┬────────────────────┐    │
│ │ M3TextField (Nom)  │ M3TextField (Pren.) │ [🔍 Rechercher]   │    │
│ │ stretch 2          │ stretch 2          │                    │    │
│ └────────────────────┴────────────────────┴────────────────────┘    │
├──────────────────────────────────────────────────────────────────────┤
│ SD3 — ZONE DE CONTENU (gauche 3, droite 1)                           │
│                                                                      │
│ ┌──────────────────────────┐  ┌────────────────────────────────┐    │
│ │ SD4 — TABLEAU RESULTATS │  │ SD7 — PANNEAU DETAIL           │    │
│ │                          │  │                                │    │
│ │ Nom │ Pren. │ Cl. │Nais.│  │ ┌──────────────────────────┐  │    │
│ │ DUP.│ Jean  │ 5A  │2010  │  │ │ Photo  │●D ●M     │    │  │    │
│ │ MAR.│ Soph. │ 5B  │2011  │  │ │        │●P ●E     │    │  │    │
│ │ ...                      │  │ │ Prénom NOM                 │  │    │
│ │                          │  │ │ Classe · ID                │  │    │
│ │ SD5 — SKELETON loading   │  │ │ Né(e) le ...               │  │    │
│ │ SD6 — ETAT VIDE inline   │  │ │                            │  │    │
│ │                          │  │ │ [Ouvrir le dossier]        │  │    │
│ └──────────────────────────┘  │ └──────────────────────────┘  │    │
│      M3Card (gauche)          │      M3Card (droite)          │    │
└──────────────────────────────────────────────────────────────────────┘
```

### Table des regles SD

| # | Regle | Interdit | Obligatoire | Priorite |
|---|---|---|---|---|
| SD1 | **Titre** en haut | Style body | `title_medium`, aligne a gauche | P0 |
| SD2 | **Barre de recherche** a 2+ champs | Un seul champ generique | Champs dedies (Nom, Prenom) + bouton FILLED, `returnPressed` et `clicked` connectes | P0 |
| SD3 | **Zone de contenu** ratio 3:1 | Ratio 1:1 ou pas de panneau detail | `QHBoxLayout` avec stretch 3 et 1 | P0 |
| SD4 | **Tableau resultats** avec colonnes badges | Juste nom/classe, pas de validation visible | Nom, Prenom, Classe, Naissance + colonnes D/M/P/E avec `setCellWidget` (cercles colores) | P1 |
| SD5 | **Skeleton loading** pendant la requete | Rien, ou popup "Chargement..." | `M3Skeleton.table()` superpose, `start()` avant, `stop()` + `hide()` dans finally | P0 |
| SD6 | **Etat vide inline** zero resultat | `QMessageBox.information` modal | Icone `search_off` + message inline, tableau cache | P0 |
| SD7 | **Panneau detail** a droite | Absent, ou en popup obligatoire | `M3Card`, photo + badges D/M/P/E + infos + bouton "Ouvrir" | P0 |
| SD8 | **Badges validation** dans le tableau | Cellules texte ("Oui"/"Non") | `setCellWidget()` avec `QLabel` cercle colore: vert=valide, rouge=non | P0 |
| SD9 | **Selection auto** si 1 seul resultat | L'utilisateur doit cliquer | `selectRow(0)` si `count == 1` | P1 |
| SD10 | **Focus initial** sur le premier champ | Pas de focus | `showEvent` → `QTimer.singleShot(50, champ.setFocus)` | P1 |

## 3. Code canonique

```python
class SearchDetailWidget(ThemedWidget):
    """Pattern canonique : recherche multi-champs + tableau resultats + panneau detail."""

    # Index des colonnes
    _COL_NOM, _COL_PRENOM, _COL_CLASSE, _COL_NAISSANCE = range(4)
    _COL_D, _COL_M, _COL_P, _COL_E = range(4, 8)
    _COL_ID = 8  # cachee

    def __init__(self):
        super().__init__()
        ds.theme_changed.connect(self._restyle)
        self._init_ui()

    def _init_ui(self):
        p = ds.p
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # SD1 — Titre
        layout.addWidget(M3Label("Recherche", style="title_medium"))

        # SD2 — Barre de recherche a 2 champs
        search_row = QHBoxLayout()
        search_row.setSpacing(ds.space_sm)
        self._inp_a = M3TextField(placeholder="Champ 1...")
        self._inp_a.setFixedHeight(ds.field_height)
        self._inp_a.setStyleSheet(ds.flat_input_qss())
        self._inp_a.returnPressed.connect(self._on_search)
        search_row.addWidget(self._inp_a, 2)
        self._inp_b = M3TextField(placeholder="Champ 2...")
        self._inp_b.setFixedHeight(ds.field_height)
        self._inp_b.setStyleSheet(ds.flat_input_qss())
        self._inp_b.returnPressed.connect(self._on_search)
        search_row.addWidget(self._inp_b, 2)
        btn = M3Button("Rechercher", variant=ButtonVariant.FILLED)
        btn.setMinimumHeight(ds.field_height)
        btn.clicked.connect(self._on_search)
        search_row.addWidget(btn)
        layout.addLayout(search_row)

        # SD3 — Zone de contenu (gauche 3, droite 1)
        content = QHBoxLayout()
        content.setSpacing(ds.space_md)

        # ── Gauche : tableau resultats (M3Card) ──
        results_card = M3Card(variant=CardVariant.ELEVATED, parent=self)
        rc_layout = results_card.content_layout()
        rc_layout.setContentsMargins(ds.space_xs, ds.space_xs, ds.space_xs, ds.space_xs)

        # Label compteur
        self._results_label = M3Label("0 resultats", style="label_small")
        self._results_label.setStyleSheet(f"font-weight: bold; color: {p.text_strong};")
        rc_layout.addWidget(self._results_label)

        # SD4 — Tableau avec colonnes badges D/M/P/E
        self._table = M3TableWidget()
        self._table.set_headers(["Nom", "Prenom", "Classe", "Ne(e) le", "D", "M", "P", "E", "ID"])
        self._table.setColumnHidden(self._COL_ID, True)
        self._table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._table.setStyleSheet(ds.table_qss())
        self._table.viewport().setCursor(Qt.PointingHandCursor)
        self._table.itemSelectionChanged.connect(self._on_selected)
        self._table.installEventFilter(self)
        hh = self._table.horizontalHeader()
        badge_w = 28
        for col in (self._COL_D, self._COL_M, self._COL_P, self._COL_E):
            hh.setSectionResizeMode(col, M3HeaderView.Fixed)
            self._table.setColumnWidth(col, badge_w)
        rc_layout.addWidget(self._table, 1)

        # SD5 — Skeleton loading
        self._skeleton = M3Skeleton.table(self, rows=6, cols=5)
        self._skeleton.set_label("Recherche en cours...")
        self._skeleton.hide()
        rc_layout.addWidget(self._skeleton)

        # SD6 — Etat vide
        self._empty_state = M3Frame()
        es_layout = QVBoxLayout(self._empty_state)
        es_layout.setSpacing(ds.space_sm)
        es_icon = QLabel()
        es_icon.setPixmap(md3_icon("search_off", color=p.text_disabled, size=55).pixmap(55, 55))
        es_icon.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_icon)
        self._empty_label = M3Label("Aucun resultat", style="body_medium")
        self._empty_label.setStyleSheet(f"color: {p.text_disabled};")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setWordWrap(True)
        es_layout.addWidget(self._empty_label)
        self._empty_state.hide()
        rc_layout.addWidget(self._empty_state, 1)

        content.addWidget(results_card, 3)

        # ── Droite : panneau detail (M3Card) ──
        self._detail_panel = M3Card(variant=CardVariant.ELEVATED, parent=self)
        dp_layout = self._detail_panel.content_layout()
        dp_layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        dp_layout.setSpacing(ds.space_md)

        # Photo + badges
        self._detail_photo = QLabel()
        self._detail_photo.setFixedSize(150, 150)
        self._detail_photo.setStyleSheet(f"background: {p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._detail_photo.setAlignment(Qt.AlignCenter)
        self._detail_photo.setCursor(Qt.PointingHandCursor)

        # SD8 — Badges validation a cote de la photo
        badges_layout = QVBoxLayout()
        badges_layout.setSpacing(3)
        self._badges: dict[str, QLabel] = {}
        for key, letter in [("dossier", "D"), ("parent", "M"), ("photo", "P"), ("email", "E")]:
            circle = QLabel(letter)
            circle.setFixedSize(24, 24)
            circle.setAlignment(Qt.AlignCenter)
            circle.setStyleSheet(
                f"background: {p.surface}; color: {p.error}; "
                f"border: 2px solid {p.error}; "
                f"font-weight: bold; font-size: 10px; border-radius: 12px;")
            badges_layout.addWidget(circle)
            self._badges[key] = circle

        # Infos texte + bouton
        self._detail_name = M3Label("—", style="headline_large")
        self._detail_class = M3Label("", style="body_medium")
        self._detail_birth = M3Label("", style="body_medium")
        self._detail_id = M3Label("", style="body_medium")
        self._open_btn = M3Button("Ouvrir", variant=ButtonVariant.FILLED)

        # Layout detail
        info_row = QHBoxLayout()
        info_row.addWidget(self._detail_photo)
        info_row.addLayout(badges_layout)
        text_col = QVBoxLayout()
        text_col.addWidget(self._detail_name)
        text_col.addWidget(self._detail_class)
        text_col.addWidget(self._detail_birth)
        text_col.addWidget(self._detail_id)
        text_col.addStretch()
        info_row.addLayout(text_col, 1)
        dp_layout.addLayout(info_row)
        dp_layout.addWidget(self._open_btn, 0, Qt.AlignCenter)
        dp_layout.addStretch()

        self._detail_panel.hide()
        content.addWidget(self._detail_panel, 1)

        layout.addLayout(content, 1)
        self._restyle()

    def _execute_search(self, query_a: str, query_b: str):
        """Lance la recherche avec skeleton loading."""
        self._table.hide()
        self._empty_state.hide()
        self._detail_panel.hide()
        self._skeleton.show()
        self._skeleton.start()
        QApplication.processEvents()
        try:
            # ... requete SQL ...
            self._results = rows
            self._populate_table()
        finally:
            self._skeleton.stop()
            self._skeleton.hide()

    def _populate_table(self):
        """SD8 : badges de validation en setCellWidget."""
        self._table.setRowCount(0)
        for r in self._results:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, self._COL_NOM, QTableWidgetItem(r["nom"]))
            self._table.setItem(row, self._COL_PRENOM, QTableWidgetItem(r["prenom"]))
            # ... autres colonnes ...
            for flag_key, col_idx, letter in [
                ("dossier", self._COL_D, "D"), ("parent", self._COL_M, "M"),
                ("photo", self._COL_P, "P"), ("email", self._COL_E, "E"),
            ]:
                ok = r.get(flag_key, {}).get("ok", False)
                badge = QLabel(letter)
                badge.setAlignment(Qt.AlignCenter)
                if ok:
                    badge.setStyleSheet(
                        f"background: {ds.p.success}; color: #FFF; "
                        f"font-weight: bold; font-size: 8px; border-radius: 9px; padding: 1px;")
                else:
                    badge.setStyleSheet(
                        f"background: transparent; color: {ds.p.error}; "
                        f"font-weight: bold; font-size: 8px; "
                        f"border: 1px solid {ds.p.error}; border-radius: 9px; padding: 1px;")
                self._table.setCellWidget(row, col_idx, badge)
        count = len(self._results)
        self._results_label.setText(f"{count} resultat(s)")
        if count == 0:
            self._empty_state.show()
        else:
            self._table.show()
            if count == 1:  # SD9
                self._table.selectRow(0)

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_focus_once", False):
            self._focus_once = True
            # SD10
            QTimer.singleShot(50, self._inp_a.setFocus)

    # SD10 — Entree = ouvrir
    def eventFilter(self, obj, event):
        if obj == self._table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._open_detail()
                return True
        return super().eventFilter(obj, event)
```

## 5. Step by Step

1. Creer le titre (SD1)
2. Creer la barre de recherche a champs dedies (SD2) — `returnPressed` sur chaque champ
3. Creer le layout de contenu ratio 3:1 (SD3)
4. Gauche : M3Card avec tableau + skeleton + etat vide (SD4-SD6)
5. Droite : M3Card avec photo + badges + infos + bouton (SD7-SD8)
6. Implementer `_execute_search` avec try/finally skeleton
7. Implementer `_populate_table` avec `setCellWidget` pour les badges
8. Connecter `showEvent` → focus initial (SD10)
9. Connecter `eventFilter` → Entree ouvre le detail (SD10)
10. Connecter `theme_changed` → `_restyle`

## 6. Checklist

- [ ] SD1 : titre en title_medium
- [ ] SD2 : 2+ champs dedies + bouton FILLED, returnPressed et clicked
- [ ] SD3 : ratio 3:1 gauche/droite
- [ ] SD4 : tableau avec colonnes badges D/M/P/E en setCellWidget
- [ ] SD5 : M3Skeleton.table avec start/stop dans try/finally
- [ ] SD6 : etat vide inline (search_off icone + message), jamais QMessageBox
- [ ] SD7 : panneau detail M3Card avec photo + badges + infos + bouton
- [ ] SD8 : badges cercles colores (vert/rouge) dans le tableau ET le detail
- [ ] SD9 : selection auto si 1 seul resultat
- [ ] SD10 : focus initial sur le 1er champ, Entree ouvre le detail
- [ ] 0 hex hardcode — tout via ds.p.*
- [ ] 0 pixel litteral — tout via tokens
- [ ] Tous les QLabel HTML ont color: explicite (D1)
- [ ] theme_changed → _restyle() reconnecte le QSS

## References croisees

- **[design-tokens](../design-tokens/SKILL.md)** — ds.field_height, ds.table_row_min
- **[color-rules](../color-rules/SKILL.md)** — D1, D3, P1-P5 (couleurs programmes)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — _restyle() complet
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R1-R11
- **[ercgonomics](../ercgonomics/SKILL.md)** — Q1-Q4 (hover, etat vide, clavier, skeleton Q20)
