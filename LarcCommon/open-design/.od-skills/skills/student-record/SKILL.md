---
skill: student-record
version: "1.0"
priority: P0
category: feature
depends_on: [design-tokens, color-rules, theme-reactivity, toolkit-reference, card-dashboard]
applies_to: [LarcSecretaire, LarcSuperviseur]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer]
subsystems: [A, B, C, D, E, F]
---

# Skill: Student Record — Dossier Élève par Catégories

## 0. Contexte

**Projet** : LarcSecretaire (principal), LarcSuperviseur (consultation)
**Modules** : `LarcSecretaire/views/student_form.py` (fiche élève), `LarcSecretaire/views/dossier_panel.py` (dossiers documentaires)
**Utilisateurs** : Secrétaire, Responsable RH, Superviseur (lecture seule)
**Dépendances** : `design-tokens`, `color-rules`, `theme-reactivity`

Ce skill définit le **pattern de gestion du dossier élève** : une interface organisée par catégories pour créer, modifier et consulter toutes les informations d'un élève, avec pièces jointes.

## 1. Fonction Principale

### Type : Système Ouvert

**Entrée** : Élève sélectionné (ou nouveau) → catégories d'information + documents
**Sortie** : Dossier complet modifié dans PostgreSQL (`larcauth_student`)
**Traitement** : Navigation par catégories → formulaire adapté à chaque catégorie → sauvegarde JSONB + fichiers joints

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Barre de recherche                                       │
│   [Rechercher un élève...]                                  │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────────────────────────────────────────┐ │
│ │ 📋 Liste  │ 📂 Catégories                                   │ │
│ │ résultats │ ┌──────────────────────────────────────────┐ │ │
│ │           │ │ [Coordonnées] [Adresse] [Parents] [Docs] │ │ │
│ │ Dupont M  │ ├──────────────────────────────────────────┤ │ │
│ │ Martin J  │ │                                          │ │ │
│ │ Leclerc S │ │  Formulaire de la catégorie active       │ │ │
│ │           │ │  (champs adaptés au contexte)            │ │ │
│ │           │ │                                          │ │ │
│ │           │ │  [Modifier]  [Enregistrer]  [Annuler]    │ │ │
│ │           │ └──────────────────────────────────────────┘ │ │
│ └──────────┴──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Catégories d'information

### Sous-système A — Catégories de la fiche élève

Chaque catégorie = un onglet. Chaque onglet = un formulaire adapté.

| Catégorie | Contenu | Qui modifie | Qui consulte |
|---|---|---|---|
| **Identité** | Nom, prénom, date naissance, genre, nationalité, langue | Secrétaire | Tous |
| **Coordonnées** | Email, téléphone, adresse postale | Secrétaire | Secrétaire, Superviseur |
| **Parents** | Nom parent 1, tel parent 1, email parent 1, idem parent 2 | Secrétaire | Secrétaire, Superviseur |
| **Scolarité** | Classe, programme (PEI/MYP/DP), date entrée, date sortie | Secrétaire | Tous |
| **Médical** | Allergies, traitements, médecin traitant, contacts urgence | Secrétaire, Infirmerie | Secrétaire, Superviseur |
| **Administratif** | Numéro dossier, bourse, régime, transport | Secrétaire | Secrétaire |

### Sous-système B — Dossiers documentaires (6 sections)

Chaque section = une liste d'entrées typées avec fichiers joints. Stockage JSONB dans `larcauth_student.notes_json`.

| Section | Types d'entrées | Exemples de champs |
|---|---|---|
| **Médicale** | Ordonnance, Vaccin, Certificat, Allergie, Traitement | Médecin, validité, n° document |
| **Pédagogique** | Bulletin, Conseil de classe, Évaluation, Projet | Période, matière, note, commentaire |
| **Administrative** | Inscription, Radiation, Bourse, Transport, Assurance | Date effet, référence, validité |
| **Communication** | Courrier envoyé, Courrier reçu, Email, Appel, RDV | Sens (entrant/sortant), destinataire, suivi |
| **Orientation** | Vœux, Décision, Stage, Entretien | Établissement, filière, statut |
| **Autre** | Note libre, Document divers | Description |

### Sous-système C — Structure d'une entrée de dossier

Chaque entrée = un document typé avec métadonnées et fichiers joints.

```python
{
    "id": "uuid",
    "type": "ordonnance",          # clé du type (registre TYPES)
    "section": "medicale",         # section parente
    "date": "2026-08-02",
    "status": "actif",             # actif | archivé | expiré | à renouveler
    "title": "Ordonnance Dr Martin",
    "note": "Renouvellement trimestriel",
    "fields": {                    # champs spécifiques au type
        "medecin": "Dr Martin",
        "validite": "2026-12-31",
        "num_doc": "ORD-2026-001"
    },
    "files": [{"name": "ordonnance.pdf", "path": "media/dossiers/uuid/ordonnance.pdf"}],
    "created_by": 42,
    "created_at": "2026-08-02T10:30:00"
}
```

### Sous-système D — Statuts et badges

| Statut | Badge | Couleur | Condition |
|---|---|---|---|
| **Actif** | `ACTIF` | `p.success` | Document en cours de validité |
| **À renouveler** | `À RENOUV.` | `p.tertiary` | Date de validité < 30 jours |
| **Expiré** | `EXPIRÉ` | `p.error` | Date de validité dépassée |
| **Archivé** | `ARCHIVÉ` | `p.text_disabled` | Document archivé manuellement |

```python
STATUS_STYLES = {
    "actif":       ("success", "ACTIF"),
    "a_renouveler": ("tertiary", "À RENOUV."),
    "expire":      ("error", "EXPIRÉ"),
    "archive":     ("text_disabled", "ARCHIVÉ"),
}
```

### Sous-système E — Filtres par section

Chaque section propose un filtre par type ET par statut.

```
┌─────────────────────────────────────────────┐
│ 📂 Médicale                                 │
│ [Tous ▼] [Tous les statuts ▼]    [+ Ajouter] │
├─────────────────────────────────────────────┤
│ Date       │ Type         │ Titre      │ St. │
│ 02/08/2026 │ Ordonnance   │ Dr Martin  │ ACT │
│ 15/07/2026 │ Vaccin        │ DTP 2026   │ ACT │
│ 10/01/2026 │ Certificat    │ Sport      │ EXP │
└─────────────────────────────────────────────┘
```

### Sous-système F — Vue chronologique (timeline)

Une vue agrégée de TOUTES les sections, triée par date décroissante.

```
┌─────────────────────────────────────────────┐
│ 📅 Chronologie — Toutes sections            │
│ [Section ▼] [Type ▼]                       │
├─────────────────────────────────────────────┤
│ 02/08/2026 │ Médicale  │ Ordonnance │ ACTIF │
│ 28/07/2026 │ Comm.     │ Email entr.│ ACTIF │
│ 15/07/2026 │ Médicale  │ Vaccin     │ ACTIF │
│ 10/06/2026 │ Pédago.   │ Bulletin T2│ ACTIF │
└─────────────────────────────────────────────┘
```

## 3. Code complet

### Fiche élève (student_form.py)

```python
class StudentForm(ThemedWidget):
    def __init__(self):
        super().__init__(object_name="student_form")
        # Catégories sous forme d'onglets
        self._tabs = M3TabWidget()
        self._tabs.addTab(self._build_identity_tab(), _("student.identity"))
        self._tabs.addTab(self._build_contact_tab(), _("student.contact"))
        self._tabs.addTab(self._build_parents_tab(), _("student.parents"))
        self._tabs.addTab(self._build_school_tab(), _("student.school"))

    def _build_identity_tab(self):
        """Catégorie A1 : Identité — mode édition activable."""
        widget = QWidget()
        form = QFormLayout(widget)
        self._edt_last_name = M3TextField(placeholder="Nom")
        self._edt_first_name = M3TextField(placeholder="Prénom")
        self._edt_birth_date = M3DateEdit()
        form.addRow(_("student.last_name"), self._edt_last_name)
        form.addRow(_("student.first_name"), self._edt_first_name)
        form.addRow(_("student.birth_date"), self._edt_birth_date)
        return widget

    def _load_student(self, student_id: int):
        """Charge les données d'un élève dans toutes les catégories."""
        cur = db.server_conn.cursor()
        cur.execute("SELECT * FROM larcauth_student WHERE id = %s", (student_id,))
        row = cur.fetchone()
        if row:
            self._populate_all_tabs(row)

    def _save_all(self):
        """Sauvegarde toutes les catégories modifiées."""
        data = self._collect_all_tabs()
        cur = db.server_conn.cursor()
        cur.execute("""
            UPDATE larcauth_student SET
                last_name = %s, first_name = %s, birth_date = %s,
                email = %s, phone = %s, address = %s,
                parent1_name = %s, parent1_phone = %s,
                parent2_name = %s, parent2_phone = %s,
                classroom_id = %s, program = %s,
                notes_json = %s,
                sync_version = sync_version + 1, updated_at = NOW()
            WHERE id = %s
        """, (*data, student_id))
```

### Dossier documentaire (dossier_panel.py)

```python
class DossierPanel(QWidget):
    entry_edited = Signal()

    def __init__(self, student_id: int):
        self._student_id = student_id
        self._tabs = M3TabWidget()
        # Une page par section + timeline
        for section_key, section_label in SECTIONS:
            page = _SectionPage(section_key, student_id)
            self._tabs.addTab(page, section_label)
        self._timeline = _TimelinePage(student_id)
        self._tabs.addTab(self._timeline, _("dossier.timeline"))

    def _load_entries(self, section: str) -> list[dict]:
        """Charge les entrées d'une section depuis le JSONB."""
        cur = db.server_conn.cursor()
        cur.execute(
            "SELECT notes_json FROM larcauth_student WHERE id = %s",
            (self._student_id,)
        )
        row = cur.fetchone()
        all_notes = json.loads(row[0] or '{}')
        return all_notes.get(section, [])

    def _save_entry(self, section: str, entry: dict):
        """Ajoute/modifie une entrée dans le JSONB."""
        entries = self._load_entries(section)
        # Upsert par id
        existing = next((e for e in entries if e['id'] == entry['id']), None)
        if existing:
            entries[entries.index(existing)] = entry
        else:
            entries.append(entry)
        self._persist(section, entries)

    def _persist(self, section: str, entries: list[dict]):
        """Écrit les entrées dans le JSONB PostgreSQL."""
        all_notes = {}
        # Recharger toutes les sections pour ne pas écraser
        cur = db.server_conn.cursor()
        cur.execute(
            "SELECT notes_json FROM larcauth_student WHERE id = %s",
            (self._student_id,)
        )
        row = cur.fetchone()
        if row and row[0]:
            all_notes = json.loads(row[0])
        all_notes[section] = entries
        cur.execute(
            "UPDATE larcauth_student SET notes_json = %s, "
            "sync_version = sync_version + 1 WHERE id = %s",
            (json.dumps(all_notes, ensure_ascii=False), self._student_id)
        )
```

### Dialogue de saisie adaptatif par type

```python
class _EntryDialog(M3Dialog):
    """Dialogue de saisie qui s'adapte au type d'entrée."""

    def __init__(self, section: str, type_info: dict, entry: dict = None):
        self._section = section
        self._type_info = type_info
        self._entry = entry or {}
        self._fields_widgets = {}

        # Titre
        layout = QVBoxLayout()
        self._edt_title = M3TextField(placeholder=_("dossier.title"))
        layout.addWidget(self._edt_title)

        # Champs dynamiques selon le type
        for field_def in type_info.get('fields', []):
            if field_def['kind'] == 'text':
                w = M3TextField(placeholder=_(field_def['label_key']))
            elif field_def['kind'] == 'date':
                w = M3DateEdit()
            elif field_def['kind'] == 'combo':
                w = M3ComboBox(items=[
                    _(opt[1]) for opt in field_def['options']
                ])
            layout.addWidget(QLabel(_(field_def['label_key'])))
            layout.addWidget(w)
            self._fields_widgets[field_def['key']] = w

        # Zone de note
        self._edt_note = M3TextEdit()
        layout.addWidget(self._edt_note)

        # Fichiers joints
        self._file_panel = FilePanel()
        layout.addWidget(self._file_panel)

        # Statut
        self._cmb_status = M3ComboBox(items=[
            _("dossier.status.active"),
            _("dossier.status.to_renew"),
            _("dossier.status.expired"),
            _("dossier.status.archived"),
        ])
        layout.addWidget(QLabel(_("dossier.status")))
        layout.addWidget(self._cmb_status)
```

## 4. Exemples

### Exemple 1 — Secrétaire modifie les coordonnées

```python
# La secrétaire recherche un élève, sélectionne, va dans l'onglet Coordonnées
# ❌ AVANT : modification directe dans la base sans audit
cur.execute("UPDATE larcauth_student SET phone = %s WHERE id = %s", (new_phone, sid))

# ✅ APRÈS : via le formulaire avec audit
form = StudentForm()
form._load_student(sid)
# La secrétaire modifie le champ téléphone
form._save_all()  # → audit log + sync_version++
```

### Exemple 2 — Ajout d'un document médical

```python
# ✅ La secrétaire ajoute une ordonnance dans la section Médicale
entry = {
    "id": str(uuid.uuid4()),
    "type": "ordonnance",
    "section": "medicale",
    "date": "2026-08-02",
    "status": "actif",
    "title": "Ordonnance Dr Martin",
    "fields": {
        "medecin": "Dr Martin",
        "validite": "2026-12-31",
        "num_doc": "ORD-2026-001"
    },
    "files": [],
    "created_by": session.user_id,
    "created_at": datetime.now().isoformat()
}
dossier._save_entry("medicale", entry)
# → visible dans la section Médicale ET dans la timeline
```

## 5. Step by Step

*(Voir le code section 3.)*

## 6. Checklist

### Fiche élève
- [ ] Recherche fonctionnelle (par nom, prénom, classe)
- [ ] Liste résultats avec sélection → chargement des catégories
- [ ] 6 catégories sous forme d'onglets (A)
- [ ] Mode édition activable/désactivable par catégorie
- [ ] Sauvegarde avec `sync_version++` et `updated_at`
- [ ] Audit log pour les modifications sensibles
- [ ] Photo avec fallback avatar
- [ ] Validation des champs obligatoires (nom, prénom, classe)

### Dossiers documentaires
- [ ] 6 sections documentaires (B)
- [ ] Registre de types par section avec champs adaptatifs (C)
- [ ] Badges de statut colorés (D)
- [ ] Filtres par type et par statut dans chaque section (E)
- [ ] Timeline chronologique toutes sections confondues (F)
- [ ] Ajout de pièces jointes par entrée
- [ ] Double-clic pour éditer une entrée
- [ ] Stockage JSONB cohérent (pas d'écrasement entre sections)

### Règles design
- [ ] 0 couleur hex hardcodée — tout via `ds.p.*`
- [ ] `theme_changed` → `_restyle_all()` pour la réactivité au thème
- [ ] `ThemedWidget` pour les conteneurs avec QSS background
- [ ] `@safe_slot` sur tous les handlers
- [ ] Traductions i18n pour toutes les catégories, types, statuts
- [ ] Tableaux avec `::item:hover` + `PointingHandCursor` (ergonomics Q1)

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — Tokens de mise en page
- **[color-rules](../color-rules/SKILL.md)** — Palette pour les badges de statut (D)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE + _restyle_all
- **[toolkit-reference](../toolkit-reference/SKILL.md)** — M3TabWidget, M3TableWidget, M3Dialog
- **[card-dashboard](../card-dashboard/SKILL.md)** — Vignette élève dans la liste de résultats
- **[ergonomics](../ergonomics/SKILL.md)** — Q1-Q4 pour la recherche et les tableaux
- **[event-generator](../event-generator/SKILL.md)** — Événements liés à l'élève
