---
skill: event-generator
version: "1.0"
priority: P1
category: feature
depends_on: [design-tokens, color-rules]
applies_to: [LarcSuperviseur, LarcProf]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: []
subsystems: [A, B, C]
---

# Skill: Event Generator — Wizard d'Événements

## 0. Contexte

**Projet** : LarcSuperviseur, LarcProf
**Module** : `LarcSuperviseur/views/core/event_actions.py`, `LarcCommon/larccommon/event_helpers.py`
**Utilisateurs** : Superviseurs (gestion des absences/retards), professeurs (saisie)
**Dépendances** : `design-tokens`, `color-rules`

Le **EventGenerator** est un wizard séquentiel qui permet de saisir rapidement des événements élèves : arrivées, départs, sorties, retours, absences justifiées/injustifiées, retards.

## 1. Fonction Principale

### Type : Système Ouvert

**Entrée** : Sélection d'élève(s) + type d'événement + date/heure
**Sortie** : Enregistrement dans la table des événements PostgreSQL
**Traitement** : Wizard 3 modes → Absence journée / Retard / Événements (arrivée, départ, sortie, retour)

## 2. Types d'événements

| Type | Icône | Description |
|---|---|---|
| `arrival` | ▲ | Arrivée d'un élève |
| `departure` | ▼ | Départ d'un élève |
| `exit` | → | Sortie temporaire |
| `return` | ← | Retour après sortie |
| `absence` | ✕ | Absence injustifiée |
| `justified` | ✓ | Absence justifiée |
| `late` | ⏰ | Retard |

### Sous-système A — event_helpers.py

```python
from larccommon.event_helpers import event_icon, event_color

icon = event_icon('absence')   # → '✕'
color = event_color('absence') # → '#e74c3c'
```

**⚠️ Dette technique connue** : `event_color()` utilise des couleurs hex en dur (`#27ae60`, `#2980b9`, etc.). Migration prévue vers les tokens palette :

```python
# ❌ Actuel — hex hardcodés
'arrival': '#27ae60'

# ✅ Cible — tokens palette
'arrival': ds.p.success       # vert
'departure': ds.p.primary     # bleu
'absence': ds.p.error         # rouge
'late': ds.p.tertiary         # orange
```

### Sous-système B — Modes du wizard

| Mode | Description | Utilisateurs |
|---|---|---|
| **Absence journée** | Marquer un élève absent toute la journée | Superviseur |
| **Retard** | Enregistrer un retard avec heure | Superviseur, Prof |
| **Événements** | Arrivée, départ, sortie, retour | Superviseur |

### Sous-système C — Structure DB

```sql
-- Table des événements (simplifié)
CREATE TABLE larc_events (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES larcauth_aecuser(id),
    event_type VARCHAR(20),  -- 'arrival', 'departure', 'exit', 'return', 'absence', 'justified', 'late'
    event_date DATE,
    event_time TIME,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 3. Code

### Pattern wizard (simplifié)

```python
class EventGenerator(QWidget):
    MODE_ABSENCE = 1
    MODE_LATE = 2
    MODE_EVENTS = 3

    def __init__(self):
        super().__init__()
        self._mode = None
        self._step = 0
        self._students = []
        self._init_ui()

    def _start_wizard(self, mode):
        self._mode = mode
        self._step = 1
        self._show_step()

    def _show_step(self):
        if self._step == 1:
            self._show_student_selection()
        elif self._step == 2:
            self._show_event_details()
        elif self._step == 3:
            self._confirm_and_save()
```

## 4. Exemples

### Enregistrer une absence

```python
# 1. Superviseur sélectionne l'élève
# 2. Choisit "Absence journée"
# 3. Confirme → INSERT dans larc_events
```

### Enregistrer un retard

```python
# 1. Prof sélectionne l'élève
# 2. Choisit "Retard"
# 3. Saisit l'heure d'arrivée
# 4. Confirme → INSERT avec event_type='late', event_time
```

## 5. Step by Step — Migration des couleurs

| Ordre | Action |
|---|---|
| 1 | Remplacer les hex dans `event_color()` par des tokens palette |
| 2 | `'arrival': '#27ae60'` → `ds.p.success` |
| 3 | `'departure': '#2980b9'` → `ds.p.primary` |
| 4 | `'absence': '#e74c3c'` → `ds.p.error` |
| 5 | `'late': '#f1c40f'` → `ds.p.tertiary` |
| 6 | Connecter `theme_changed` pour que les couleurs suivent le thème |
| 7 | Supprimer les exceptions du linter pour ce fichier |

## 6. Checklist

- [ ] 3 modes disponibles : Absence, Retard, Événements
- [ ] Sélection d'élève fonctionnelle (individuel ou groupe)
- [ ] event_type valide (7 types)
- [ ] Date et heure correctement enregistrées
- [ ] ⚠️ `event_color()` contient des hex hardcodés — migration vers tokens planifiée
- [ ] `event_icon()` retourne des icônes Unicode (pas d'images)
- [ ] Traductions i18n pour les types d'événements

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.p.success, ds.p.error, etc.
- **[color-rules](../color-rules/SKILL.md)** — Règles D1-D3 pour la migration des couleurs
- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — @safe_slot sur les handlers du wizard
