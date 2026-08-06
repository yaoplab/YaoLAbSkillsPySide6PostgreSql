---
skill: card-dashboard
version: "1.0"
priority: P1
category: design
depends_on: [design-tokens, color-rules, toolkit-reference]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [A, B, C, D, E]
---

# Skill: Card Dashboard — Vignettes Configurables

## 0. Contexte

**Projet** : LarcSuperviseur, LarcSecretaire, LarcProf
**Module** : `LarcCommon/larccommon/widgets/card.py` (StudentCard), `card_config.py` (CardConfig)
**Utilisateurs** : Tous les développeurs de vues utilisant des vignettes élèves
**Dépendances** : `design-tokens`, `color-rules`, `toolkit-reference`

Ce skill définit le **pattern de vignette configurable** : chaque rôle (secrétaire, superviseur, prof) voit des informations différentes sur la carte élève, adaptées à ses besoins métier. **Une seule card class, plusieurs configurations.**

## 1. Fonction Principale

### Type : Système Ouvert

**Entrée** : Élève (données DB) + rôle utilisateur (ADMIN/COORD/SECR/SUPERVISEUR/PROF)
**Sortie** : Vignette cliquable montrant les informations pertinentes pour ce rôle
**Traitement** : La config du rôle active/désactive les champs visibles et choisit les métriques affichées

## 2. Contraintes Fondamentales

**Avant de cliquer = décider si j'agis.** La vignette est un mini-tableau de bord, pas une fiche détaillée.

## 3. Configurations par Rôle

### Sous-système A — Matrice des champs par rôle

| Champ | Secrétaire | Superviseur | Prof | Description |
|---|---|---|---|---|
| **Photo** | ✅ | ✅ | ✅ | Reconnaissance immédiate |
| **Nom Prénom** | ✅ | ✅ | ✅ | Identité |
| **Classe** | ✅ | ✅ | ✅ | Contexte |
| **Programme** (PEI/MYP/DP) | ✅ | ✅ | ❌ | Couleur codée — pertinent pour admin |
| **Indicateur présence** | ✅ | ✅ | ❌ | Aujourd'hui : présent/absent/retard |
| **Nb absences mois** | ✅ | ✅ | ❌ | Alerte si >5 |
| **Nb retards mois** | ✅ | ✅ | ❌ | Alerte si >3 |
| **Sorties en cours** | ✅ | ❌ | ❌ | Gestion administrative pure |
| **Dernier événement** | ✅ | ✅ | ❌ | Type + date + heure |
| **Niveau/moyenne période** | ❌ | ❌ | ✅ | Indicateur pédagogique |
| **Événements aujourd'hui** | ❌ | ✅ | ✅ | Arrivée/départ/retard du jour |
| **Bouton action rapide** | ❌ | ✅ | ✅ | « Signaler retard » / « Signaler absence » |

### Sous-système B — Configurations visuelles

```python
# larccommon/widgets/card_config.py
from dataclasses import dataclass

@dataclass
class CardFields:
    """Champs visibles sur la carte — configurables par rôle."""
    show_photo:        bool = True
    show_name:         bool = True
    show_classroom:    bool = True
    show_program:      bool = False   # PEI/MYP/DPFr/DPEn
    show_presence:     bool = False   # Indicateur aujourd'hui
    show_absences:     bool = False   # Compteur mois
    show_lates:        bool = False   # Compteur mois
    show_exits:        bool = False   # Sorties en cours
    show_last_event:   bool = False   # Dernier événement
    show_level:        bool = False   # Niveau/moyenne (prof)
    show_today_events: bool = False   # Événements du jour
    show_quick_action: bool = False   # Bouton action rapide

# Configurations par rôle
CARD_SECRETAIRE = CardFields(
    show_program=True, show_presence=True,
    show_absences=True, show_lates=True,
    show_exits=True, show_last_event=True,
)

CARD_SUPERVISEUR = CardFields(
    show_program=True, show_presence=True,
    show_absences=True, show_lates=True,
    show_last_event=True, show_today_events=True,
    show_quick_action=True,
)

CARD_PROF = CardFields(
    show_today_events=True, show_quick_action=True,
    show_level=True,
)

CARD_MINIMAL = CardFields(
    show_classroom=False,
)  # Photo + nom uniquement
```

### Sous-système C — États visuels de la vignette

| État | Condition | Bordure | Fond | Badge |
|---|---|---|---|---|
| **Normal** | Aucun événement notable | `outline_variant` 1px | `surface` | — |
| **Absent aujourd'hui** | `event_type='absence'` ET `event_date=today` | `error` 2px | `error_container` | 🔴 "ABS" |
| **Retard aujourd'hui** | `event_type='late'` ET `event_date=today` | `tertiary` 2px | `tertiary_container` | 🟠 "RET" |
| **Sortie en cours** | `event_type='exit'` sans `return` | `secondary` 2px | `secondary_container` | 🔵 "SOR" |
| **Multi-événements** | Absence + sortie le même jour | Priorité `error` | `error_container` | 🔴 "ABS" |
| **Absences accumulées** | ≥ 10 absences ce mois | `error` 1px | `surface` | Compteur rouge |
| **Retards accumulés** | ≥ 5 retards ce mois | `tertiary` 1px | `surface` | Compteur orange |
| **Niveau faible** (prof) | Moyenne < 10/20 | `error` 1px | `surface` | Note rouge |
| **Niveau excellent** (prof) | Moyenne ≥ 16/20 | `success` 1px | `surface` | Note verte |

### Sous-système D — Indicateur de présence (pastille)

```python
# Pastille 8×8 px en haut à droite de la photo
class PresenceDot:
    PRESENT  = "present"   # 🟢 Vert (p.success)
    ABSENT   = "absent"    # 🔴 Rouge (p.error)
    LATE     = "late"      # 🟠 Orange (p.tertiary)
    EXITED   = "exited"    # 🔵 Bleu (p.secondary)
    UNKNOWN  = "unknown"   # ⚫ Gris (p.text_disabled)
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| Pastille absente si pas d'événement | Toujours afficher la pastille (grise si pas de données) |
| Pastille sans info-bulle | `setToolTip("Présent aujourd'hui")` |
| Couleur en dur | Token palette (`p.success`, `p.error`, `p.tertiary`, `p.secondary`) |

### Sous-système E — Hover : infobulle enrichie

Au survol de la vignette, afficher une info-bulle avec les infos clés sans cliquer :

```
┌──────────────────────────────────┐
│ DUPONT Marie — 5ème B (PEI)     │
│ Présente aujourd'hui             │
│ 3 absences ce mois               │
│ Dernier événement: Retard 02/08  │
│ → Cliquer pour le détail complet │
└──────────────────────────────────┘
```

```python
card.setToolTip(
    f"{last_name} {first_name} — {classroom} ({program})\n"
    f"{presence_text}\n"
    f"{absences_text}\n"
    f"{last_event_text}\n"
    f"→ Cliquer pour le détail complet"
)
```

## 3. Code complet — StudentCard configurable

```python
from larccommon.widgets.card_config import CardFields, CardConfig, CARD_SECRETAIRE
from larccommon.theme import theme_manager, PROGRAM_STYLES
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap

class StudentCard(QFrame):
    clicked = Signal(int)

    def __init__(self, student: dict, fields: CardFields = None,
                 cfg: CardConfig = None):
        """
        Args:
            student: dict avec id, last_name, first_name, classroom, program,
                     presence, absences, lates, exits, last_event, level...
            fields: configuration des champs visibles (défaut: CARD_SECRETAIRE)
            cfg: configuration Fibonacci (défaut: PHI_MEDIUM)
        """
        super().__init__()
        self._fields = fields or CARD_SECRETAIRE
        self._cfg = cfg or DEFAULT_CONFIG
        self._student = student
        self._build()
        self._apply_state()
        self.setFixedSize(self._cfg.card_w, self._cfg.card_h)
        self.setCursor(Qt.PointingHandCursor)

    def _build(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        layout = QVBoxLayout(self)
        layout.setSpacing(self._cfg.spacing)

        # ── Niveau 1 : Indicateur présence ──
        if self._fields.show_presence:
            self._presence_dot = QLabel()
            self._presence_dot.setFixedSize(8, 8)
            self._presence_dot.setStyleSheet(
                f"background: {self._presence_color()}; border-radius: 4px;")
            self._presence_dot.setToolTip(self._presence_text())
            # Positionné en haut à droite via un QHBoxLayout wrapper

        # ── Niveau 2 : Photo ──
        if self._fields.show_photo:
            self._photo = QLabel()
            pix = QPixmap(get_photo_path(self._student['id']))
            if pix.isNull():
                pix = make_avatar(self._student['last_name'],
                                  self._student['first_name'],
                                  self._cfg.photo_size, self._cfg.avatar_font)
            else:
                pix = pix.scaled(self._cfg.photo_size, self._cfg.photo_size,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._photo.setPixmap(pix)
            self._photo.setAlignment(Qt.AlignCenter)
            layout.addWidget(self._photo, 0, Qt.AlignCenter)

        # ── Niveau 3 : Identité + Contexte ──
        if self._fields.show_name:
            name_html = (
                f"<b style='font-size:{s(self._cfg.font_name)}px; "
                f"color:{p.text_strong}'>{self._student['last_name']}</b><br>"
                f"<span style='font-size:{s(self._cfg.font_name)}px; "
                f"color:{p.text_soft}'>{self._student['first_name']}</span>"
            )
            self._name_label = QLabel(name_html)
            self._name_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self._name_label)

        if self._fields.show_classroom or self._fields.show_program:
            ctx_parts = []
            if self._fields.show_classroom:
                ctx_parts.append(self._student.get('classroom', ''))
            if self._fields.show_program and self._student.get('program'):
                prog = self._student['program']
                prog_color = self._program_color(prog)
                ctx_parts.append(
                    f"<span style='color:{prog_color};font-weight:bold'>{prog}</span>"
                )
            ctx_label = QLabel(" · ".join(ctx_parts))
            ctx_label.setAlignment(Qt.AlignCenter)
            ctx_label.setStyleSheet(
                f"font-size: {s(self._cfg.font_context)}px; color: {p.text_soft};")
            layout.addWidget(ctx_label)

        # ── Niveau 4 : Métriques ──
        metrics = []
        if self._fields.show_absences:
            n = self._student.get('absences', 0)
            color = p.error if n >= 10 else p.text_soft
            metrics.append(f"<span style='color:{color}'>{n} abs.</span>")
        if self._fields.show_lates:
            n = self._student.get('lates', 0)
            color = p.tertiary if n >= 5 else p.text_soft
            metrics.append(f"<span style='color:{color}'>{n} ret.</span>")
        if self._fields.show_exits:
            n = self._student.get('exits', 0)
            metrics.append(f"<span style='color:{p.secondary}'>{n} sorties</span>")
        if self._fields.show_level:
            level = self._student.get('level', '—')
            color = p.success if level >= 16 else (p.error if level < 10 else p.text_strong)
            metrics.append(f"<span style='color:{color}'>{level}/20</span>")

        if metrics:
            metrics_label = QLabel(" · ".join(metrics))
            metrics_label.setAlignment(Qt.AlignCenter)
            metrics_label.setStyleSheet(
                f"font-size: {s(self._cfg.font_metrics)}px;")
            layout.addWidget(metrics_label)

        # ── Niveau 5 : Dernier événement ──
        if self._fields.show_last_event:
            evt = self._student.get('last_event', {})
            if evt:
                evt_text = f"{evt.get('type','?')} — {evt.get('date','?')}"
                evt_label = QLabel(evt_text)
                evt_label.setAlignment(Qt.AlignCenter)
                evt_label.setStyleSheet(
                    f"font-size: {s(self._cfg.font_footer)}px; "
                    f"color: {p.text_disabled};")
                layout.addWidget(evt_label)

        # ── Action rapide ──
        if self._fields.show_quick_action:
            from phibuilder.widgets import M3Button, ButtonVariant
            self._quick_btn = M3Button("Signaler", variant=ButtonVariant.TEXT)
            self._quick_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self._quick_btn.clicked.connect(
                lambda: self._on_quick_action(self._student['id']))
            layout.addWidget(self._quick_btn, 0, Qt.AlignCenter)

        # ── Info-bulle enrichie (E) ──
        self.setToolTip(self._build_tooltip())

    def _apply_state(self):
        """Applique l'état visuel selon les données de l'élève (C)."""
        p = theme_manager.palette
        state = self._determine_state()
        styles = {
            "normal":   (p.outline_variant, p.surface, None),
            "absent":   (p.error, p.error_container, "ABS"),
            "late":     (p.tertiary, p.tertiary_container, "RET"),
            "exited":   (p.secondary, p.secondary_container, "SOR"),
            "multi":    (p.error, p.error_container, "ABS"),
        }
        border, bg, badge = styles.get(state, styles["normal"])
        # Appliquer via setStyleSheet...

    def _program_color(self, prog: str) -> str:
        """Retourne la couleur du programme (P)."""
        from larccommon.theme import PROGRAM_STYLES
        p = theme_manager.palette
        if prog in PROGRAM_STYLES:
            fg_role, _, _ = PROGRAM_STYLES[prog]
            return getattr(p, fg_role)
        return p.text_soft

    def _presence_color(self) -> str:
        """Pastille de présence (D)."""
        p = theme_manager.palette
        mapping = {"present": p.success, "absent": p.error,
                   "late": p.tertiary, "exited": p.secondary}
        return mapping.get(self._student.get('presence', 'unknown'), p.text_disabled)

    def _build_tooltip(self) -> str:
        """Construit l'infobulle enrichie (E)."""
        s = self._student
        lines = [f"{s['last_name']} {s['first_name']} — {s.get('classroom','')}"]
        if self._fields.show_program and s.get('program'):
            lines.append(f"Programme: {s['program']}")
        if self._fields.show_presence:
            lines.append(self._presence_text())
        if self._fields.show_absences:
            lines.append(f"{s.get('absences',0)} absences ce mois")
        if self._fields.show_lates:
            lines.append(f"{s.get('lates',0)} retards ce mois")
        if self._fields.show_level:
            lines.append(f"Moyenne: {s.get('level','—')}/20")
        lines.append("→ Cliquer pour le détail complet")
        return "\n".join(lines)

    def mousePressEvent(self, event):
        self.clicked.emit(self._student['id'])
        super().mousePressEvent(event)
```

## 4. Exemples

### Exemple 1 — Grille secrétaire (30 élèves, format compact)

```python
# ❌ AVANT : toutes les cartes identiques, info minimale
for student in all_students:
    card = StudentCard(student['id'], student['last_name'], student['first_name'])

# ✅ APRÈS : info admin complète, compacte, état visuel
for student in all_students:
    card = StudentCard(student, fields=CARD_SECRETAIRE, cfg=PHI_COMPACT)
    card.clicked.connect(self._on_student_detail)
    # → Voit : photo, nom, classe, programme (couleur), absences, retards, sorties, dernier evt
    # → États visuels : rouge si absent, orange si retard
```

### Exemple 2 — Dashboard superviseur (15 élèves, format medium)

```python
# ✅ Superviseur : focus événements + action rapide
for student in supervised_students:
    card = StudentCard(student, fields=CARD_SUPERVISEUR, cfg=PHI_MEDIUM)
    # → Voit : photo, nom, présence aujourd'hui, événements, bouton « Signaler retard »
```

### Exemple 3 — Vue professeur (classe entière, format compact)

```python
# ✅ Prof : focus pédagogique
for student in class_students:
    card = StudentCard(student, fields=CARD_PROF, cfg=PHI_COMPACT)
    # → Voit : photo, nom, niveau/moyenne, événements aujourd'hui, bouton action
```

## 5. Step by Step

*(Voir le code section 3 pour l'implémentation.)*

## 6. Checklist

- [ ] `CardFields` configurable utilisé au lieu de champs en dur
- [ ] Config par rôle : `CARD_SECRETAIRE`, `CARD_SUPERVISEUR`, `CARD_PROF`
- [ ] États visuels (7 états) implémentés via `_apply_state()`
- [ ] Pastille de présence (8×8) avec info-bulle et token palette
- [ ] Info-bulle enrichie au survol (`setToolTip`)
- [ ] Couleurs programme via `PROGRAM_STYLES` (pas en dur)
- [ ] Proportions Fibonacci via `CardConfig`
- [ ] `fill_cards_grid()` pour la grille responsive
- [ ] `theme_changed` → `_restyle_all()` pour la réactivité au thème
- [ ] 0 couleur hex hardcodée — tout via `ds.p.*` ou `PROGRAM_STYLES`
- [ ] Photo avec fallback `make_avatar()` si pas de photo
- [ ] Clic émet `student_id` pour navigation → détail

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — Tokens espacement, typo, icônes
- **[color-rules](../color-rules/SKILL.md)** — Palette + PROGRAM_STYLES (P1-P4)
- **[toolkit-reference](../toolkit-reference/SKILL.md)** — Widgets disponibles (M3Button, CardConfig)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + _restyle_all
- **[ergonomics](../ergonomics/SKILL.md)** — Q1-Q4 (hover, tooltip, état vide)
