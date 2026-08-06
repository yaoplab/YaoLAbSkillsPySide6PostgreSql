---
skill: card-grid-pattern
version: "1.0"
priority: P0
category: page-pattern
depends_on: [design-tokens, color-rules, zero-hardcoding, theme-reactivity, card-dashboard]
applies_to: [LarcSecretaire, LarcSuperviseur, LarcProf]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer, feature-reviewer]
subsystems: [CG]
---

# Skill: Card Grid Pattern — Grille de Vignettes Responsive

## 0. Contexte

**Projet** : Tous les modules Larc avec grilles de cartes (eleves d'une classe, liste de professeurs)
**Fichiers de reference** :
  - `LarcSecretaire/views/supervisor_panel.py::SupervisorPanel` — grille avec cartes + detail
  - `LarcSuperviseur/views/main_window.py` — grille avec stats presence
  - `LarcCommon/larccommon/widgets/card_grid.py::fill_cards_grid()` — helper de grille
**Utilisateurs** : Developpeurs de grilles de cartes ET agents IA

Ce skill definit le **pattern canonique de grille de vignettes** : header avec actions,
grille responsive, skeleton loading, et detail au clic.

## 1. Fonction Principale

### Type : Systeme Ferme

**Entree** : Une liste d'entites (eleves, profs...) sans presentation
**Sortie** : Une grille de vignettes responsive avec indicateurs, presence, badges
**Traitement** : Appliquer le patron CG1-CG12 dans l'ordre

## 2. Architecture spatiale obligatoire

```
┌──────────────────────────────────────────────────────────────────────┐
│ CG1 — HEADER (titre + actions)                                       │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ M3Label "PEI 5A — 23 eleves"  [📋] [📱] [📊] [+]              │ │
│ │ title_small                     Liste Tailles KPI   Ajouter      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ CG2 — GRILLE DE CARTES (QGridLayout responsive)                      │
│                                                                      │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ │ DUPONT  │ │ MARTIN  │ │ LECLERC │ │ BERNARD │ │ PETIT   │       │
│ │ Jean    │ │ Sophie  │ │ Marc    │ │ Julie   │ │ Paul    │       │
│ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │       │
│ │ │PHOTO│ │ │ │PHOTO│ │ │ │PHOTO│ │ │ │PHOTO│ │ │ │PHOTO│ │       │
│ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │       │
│ │ ●D●M●P●E│ │ ●D●M●P●E│ │ ●D●M●P●E│ │ ●D●M●P●E│ │ ●D●M●P●E│       │
│ │ Présent │ │ Absent  │ │ Présent │ │ Présent │ │ Retard  │       │
│ │ 0 sort. │ │ 2 sort. │ │ 1 sort. │ │ 0 sort. │ │ 0 sort. │       │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                                                                      │
│ CG3 — SKELETON loading (superpose pendant le chargement)             │
│ CG4 — ETAT VIDE "Selectionnez une classe"                            │
└──────────────────────────────────────────────────────────────────────┘
```

### Anatomie d'une StudentCard

```
┌─────────────────────────┐
│ DUPONT                  │  ← nom en gras (text_strong)
│ Jean                    │  ← prenom (text_soft)
│ ┌─────────────────────┐ │
│ │                     │ │
│ │       PHOTO         │ │  ← photo_badge (QFrame arrondi, primary_container)
│ │                     │ │
│ └─────────────────────┘ │
│ ●D  ●M  ●P  ●E         │  ← 4 cercles D/M/P/E (14px)
│ Présent                 │  ← status (success/error/tertiary)
│ 2 sortie(s)             │  ← exit count (text_disabled)
└─────────────────────────┘
```

### Table des regles CG

| # | Regle | Interdit | Obligatoire | Priorite |
|---|---|---|---|---|
| CG1 | **Header** avec titre + compteur + actions | Juste un titre | `title_small`, compteur "(N eleves)", boutons actions alignes a droite | P0 |
| CG2 | **Grille responsive** `QGridLayout` | `setFixedWidth` ou colonnes en dur | `cols = max(1, viewport.width() // (card_w + spacing))` recalcule au resize | P0 |
| CG3 | **Skeleton loading** pendant chargement | Blocage UI sans feedback | Page skeleton via `QStackedWidget` (page 0=grille, 1=skeleton, 2=detail) | P0 |
| CG4 | **Etat vide** si pas de classe selectionnee | Widget vide | Message "Selectionnez une classe dans la sidebar" | P1 |
| CG5 | **Chaque carte** = `StudentCard` du toolkit | QFrame custom | `StudentCard(sid, last_name, first_name, cfg)`, configuration via `PHI_MEDIUM`/`PHI_COMPACT`/`PHI_LARGE` | P0 |
| CG6 | **Badges D/M/P/E** sous la photo | Absents ou texte | 4 `QLabel` cercles 14px, vert si valide, rouge bordure sinon | P0 |
| CG7 | **Presence** = status colore | Texte sans couleur | `card.set_status(text, color)` avec success/error/tertiary | P1 |
| CG8 | **Sorties** = compteur du trimestre | Journee seulement | `card.set_exit_count(n)` — requete separee sur la periode | P1 |
| CG9 | **Absent** = carte rouge | Meme carte que les presents | `card.set_absent(True)` → fond error_container, bordure error | P0 |
| CG10 | **Clic carte** → ouvre le detail | Rien ou popup | `card.clicked.connect(on_student_clicked)` → QStackedWidget page 2 ou dialogue | P0 |
| CG11 | **Tailles de carte** commutables | Une seule taille | 3 tailles : compact / medium / large via `PHI_COMPACT` etc. | P1 |
| CG12 | **Resize automatique** | Grille fixe | `resizeEvent` re-calcule les colonnes et re-positionne les cartes | P0 |

## 3. Code canonique

### Structure du widget

```python
class CardGridPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._students: list[dict] = []
        self._cards: list[StudentCard] = []
        self._current_class_id = 0
        self._card_size = "medium"
        self._card_sizes = {"compact": PHI_COMPACT, "medium": PHI_MEDIUM, "large": PHI_LARGE}
        self._init_ui()

    def _init_ui(self):
        p = ds.p
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # CG1 — Header
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(0, 3, 0, 3)

        self._header = M3Label("Selectionnez une classe", style="title_small")
        hdr_row.addWidget(self._header, 1)

        # Boutons d'action a droite
        for action in ACTIONS:
            btn = M3Button(label, variant=ButtonVariant.TONAL)
            btn.setFixedSize(ds.sp(SpacingToken.XL), ds.sp(SpacingToken.XL))
            btn.clicked.connect(handler)
            hdr_row.addWidget(btn)

        # CG11 — Selecteur de taille
        for key, icon_name in [("compact", "view_comfy"), ("medium", "view_module"), ("large", "dashboard")]:
            btn = M3Button(variant=ButtonVariant.TONAL)
            btn.setFixedSize(ds.sp(SpacingToken.XL), ds.sp(SpacingToken.XL))
            btn.setIcon(md3_icon(icon_name, color=ds.p.text_soft, size=22))
            btn.setCheckable(True)
            if key == self._card_size:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, k=key: self._on_card_size(k))
            hdr_row.addWidget(btn)

        layout.addLayout(hdr_row)

        # CG3 — StackedWidget (0=grille, 1=skeleton, 2=detail)
        self._stack = QStackedWidget()

        # Page 0 : grille de cartes dans un scroll
        scroll = M3ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background: transparent;")
        self._cards_widget = QWidget()
        self._cards_grid = QGridLayout(self._cards_widget)
        self._cards_grid.setSpacing(ds.space_xs)
        scroll.setWidget(self._cards_widget)
        self._stack.addWidget(scroll)

        # Page 1 : skeleton loading
        self._loading_page = QWidget()
        lp_layout = QVBoxLayout(self._loading_page)
        lp_layout.setAlignment(Qt.AlignCenter)
        self._loading_skeleton = M3Skeleton.table(self._loading_page, rows=5, cols=4)
        self._loading_skeleton.set_label("Chargement...")
        lp_layout.addWidget(self._loading_skeleton)
        self._stack.addWidget(self._loading_page)

        # Page 2 : detail eleve (ou dialogue a la place)
        self._detail_page = self._build_detail()
        self._stack.addWidget(self._detail_page)

        self._stack.setCurrentIndex(0)
        layout.addWidget(self._stack, 1)

    def _load_students(self, class_id: int):
        self._current_class_id = class_id
        # CG3 : montrer le skeleton
        if getattr(self, "_loading_students", False):
            return
        self._loading_students = True
        try:
            self._stack.setCurrentIndex(1)
            self._loading_skeleton.start()
            QApplication.processEvents()
            # ... requete SQL ...
            self._students = rows
            self._rebuild_cards()
        finally:
            self._loading_students = False
            self._loading_skeleton.stop()
            self._stack.setCurrentIndex(0)

    def _rebuild_cards(self):
        # CG2 — Grille responsive
        self._clear_grid()
        self._cards = []
        cfg = self._card_sizes.get(self._card_size, PHI_MEDIUM)
        card_w = cfg.card_w
        cols = max(1, self.width() // (card_w + 10))

        for i, s in enumerate(self._students):
            card = StudentCard(s["id"], s["last_name"], s["first_name"], cfg)
            # CG6 — Badges validation
            val = s.get("validation", {})
            if isinstance(val, str):
                import json; val = json.loads(val) if val else {}
            card.set_validation(val)
            # CG10 — Clic
            card.clicked.connect(self._on_card_clicked)
            self._cards_grid.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

        self._load_presence()

    def _load_presence(self):
        # CG7 + CG9 — Presence et absents
        # CG8 — Sorties sur la periode (pas la journee)
        period_from, period_to = self._time_manager.period_dates()
        today = QDate.currentDate().toString("yyyy-MM-dd")
        # ... 2 requetes separees : sorties(periode) + presence(aujourd'hui) ...
        for card in self._cards:
            stats = event_stats.get(card._sid, {})
            exit_count = stats.get("exit", 0)
            presence = stats.get("presence", "Present")
            card.set_exit_count(exit_count)
            if presence == "Absent":
                card.set_status("Absent", ds.p.error)
                card.set_absent(True)
            else:
                card.set_status("Present", ds.p.success)
                card.set_absent(False)

    # CG12 — Resize recalcule les colonnes
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_cards") and self._cards:
            cfg = self._card_sizes.get(self._card_size, PHI_MEDIUM)
            cols = max(1, self.width() // (cfg.card_w + 10))
            for i, card in enumerate(self._cards):
                self._cards_grid.addWidget(card, i // cols, i % cols)
```

### StudentCard avec badges (CG5-CG6)

```python
class StudentCard(QFrame):
    def __init__(self, student_id, last_name, first_name, cfg=None):
        # ...
        # CG6 — 4 cercles D/M/P/E sous la photo
        self._badge_labels: dict[str, QLabel] = {}
        _badge_size = 14
        badges_row = QHBoxLayout()
        badges_row.setSpacing(2)
        for badge_key, letter in [("dossier_valid","D"),("parent_valid","M"),
                                    ("photo_valid","P"),("email_valid","E")]:
            circle = QLabel(letter)
            circle.setFixedSize(_badge_size, _badge_size)
            circle.setAlignment(Qt.AlignCenter)
            circle.setStyleSheet(
                f"background: {p.surface}; color: {p.error}; "
                f"border: 1px solid {p.error}; "
                f"border-radius: {_badge_size // 2}px; "
                f"font-size: {max(7, _badge_size - 7)}px; font-weight: bold;")
            badges_row.addWidget(circle)
            self._badge_labels[badge_key] = circle
        layout.addLayout(badges_row)

    def set_validation(self, validation: dict | None):
        """CG6 : colore les cercles vert/rouge selon validation."""
        if not validation:
            return
        for flag_key, badge_key in [
            ("dossier","dossier_valid"), ("parent","parent_valid"),
            ("photo","photo_valid"), ("email","email_valid"),
        ]:
            circle = self._badge_labels.get(badge_key)
            if not circle:
                continue
            entry = validation.get(flag_key, {})
            ok = entry.get("ok", False) if isinstance(entry, dict) else False
            if ok:
                circle.setStyleSheet(
                    f"background: {p.success}; color: #FFF; "
                    f"border: 1px solid {p.success}; ...")
            else:
                circle.setStyleSheet(
                    f"background: {p.surface}; color: {p.error}; "
                    f"border: 1px solid {p.error}; ...")
```

## 5. Step by Step

1. Creer le header avec titre + compteur + boutons d'action (CG1)
2. Creer le `QStackedWidget` avec 3 pages (CG3)
3. Page 0 : `M3ScrollArea` + `QGridLayout` pour les cartes (CG2)
4. Page 1 : `M3Skeleton.table` pour le chargement (CG3)
5. Page 2 : panneau detail (ou dialogue) (CG10)
6. Implementer `_load_students` avec skeleton + try/finally (CG3)
7. Implementer `_rebuild_cards` avec grille responsive (CG2) + badges (CG6)
8. Implementer `_load_presence` avec 2 requetes separees (CG7-CG9)
9. Connecter `card.clicked` → ouvre le detail (CG10)
10. Implementer `resizeEvent` pour recalculer la grille (CG12)

## 6. Checklist

- [ ] CG1 : header avec title_small + compteur + boutons d'action
- [ ] CG2 : grille QGridLayout responsive, cols recalculees au resize
- [ ] CG3 : QStackedWidget 3 pages (grille, skeleton, detail)
- [ ] CG4 : etat vide si pas de classe selectionnee
- [ ] CG5 : StudentCard utilise PHI_MEDIUM/COMPACT/LARGE
- [ ] CG6 : badges D/M/P/E sous la photo (14px, vert/rouge)
- [ ] CG7 : presence coloree (success/error/tertiary)
- [ ] CG8 : sorties comptees sur le trimestre (pas la journee)
- [ ] CG9 : absent → fond error_container, bordure error
- [ ] CG10 : clic carte → detail (QStackedWidget page 2 ou dialogue)
- [ ] CG11 : 3 tailles de cartes commutables
- [ ] CG12 : resizeEvent re-positionne les cartes
- [ ] 0 hex hardcode — tout via ds.p.*
- [ ] 0 pixel litteral — tout via tokens
- [ ] theme_changed → _restyle() reconnecte le QSS

## References croisees

- **[design-tokens](../design-tokens/SKILL.md)** — ds.table_row_min, SpacingToken
- **[color-rules](../color-rules/SKILL.md)** — D1, P1-P5 (couleurs programmes)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — _restyle() complet
- **[card-dashboard](../card-dashboard/SKILL.md)** — StudentCard, PHI_MEDIUM etc.
- **[toolkit-reference](../toolkit-reference/SKILL.md)** — QStackedWidget, M3ScrollArea
- **[skeleton.py](../../larccommon/widgets/skeleton.py)** — M3Skeleton.table()
