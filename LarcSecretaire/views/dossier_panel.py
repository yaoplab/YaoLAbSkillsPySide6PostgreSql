"""
DossierPanel — Sections documentaires avec notes + fichiers joints.

Niveau 2 : chaque entrée est TYPÉE (registre TYPES par section) — le dialogue
de saisie s'adapte au type (médecin, validité, n° document, sens entrant/sortant...),
chaque entrée porte un STATUT affiché en badge coloré, et chaque section propose
un FILTRE par type.

Niveau 3 : une vue CHRONOLOGIQUE globale (_TimelinePage) agrège toutes les
sections triées par date (filtres section/type, badges, double-clic pour éditer).

Stockage : notes_json (JSONB) dans larcauth_student.
Chaque entrée = un document avec ses propres fichiers joints.
"""

import os
import shutil
from datetime import date

from larccommon.design_system import ds
from larccommon.l10n import _
from larccommon.widgets.table_settings import TableSettings
from phibuilder.widgets import (
    M3Button,
    M3Card,
    M3ComboBox,
    M3DateEdit,
    M3Dialog,
    M3DialogButtonBox,
    M3Frame,
    M3HeaderView,
    M3Label,
    M3StackedWidget,
    M3TableWidget,
    M3TextEdit,
    M3TextField,
)
from phibuilder.widgets.button import ButtonVariant
from phibuilder.widgets.card import CardVariant
from PySide6.QtCore import QDate, QEvent, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
from larccommon.safe_slot import safe_slot
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

SECTIONS = [
    ("medicale", _("dossier.section.medical")),
    ("pedagogique", _("dossier.section.pedagogic")),
    ("administrative", _("dossier.section.administrative")),
    ("communication", _("dossier.section.communication")),
    ("orientation", _("dossier.section.orientation")),
    ("autre", _("dossier.section.other")),
]

# ──────────────────────────────────────────────────────────────
#   Registre des TYPES par section (Niveau 2)
#   Chaque type : key stable (stockée dans l'entrée), label_key i18n,
#   et une liste de champs typés : kind = text | date | combo.
#   combo → options = liste de tuples (valeur, label_key).
# ──────────────────────────────────────────────────────────────
TYPES: dict[str, list[dict]] = {
    "medicale": [
        {
            "key": "ordonnance",
            "label_key": "dossier.type.ordonnance",
            "fields": [
                {"key": "medecin", "kind": "text", "label_key": "dossier.field.medecin"},
                {"key": "validite", "kind": "date", "label_key": "dossier.field.validity"},
                {"key": "num_doc", "kind": "text", "label_key": "dossier.field.num_doc"},
            ],
        },
        {
            "key": "vaccin",
            "label_key": "dossier.type.vaccin",
            "fields": [
                {"key": "vaccin", "kind": "text", "label_key": "dossier.field.vaccine"},
                {"key": "rappel", "kind": "date", "label_key": "dossier.field.booster"},
            ],
        },
        {
            "key": "certificat",
            "label_key": "dossier.type.certificat",
            "fields": [
                {"key": "medecin", "kind": "text", "label_key": "dossier.field.medecin"},
                {"key": "validite", "kind": "date", "label_key": "dossier.field.validity"},
            ],
        },
        {
            "key": "analyse",
            "label_key": "dossier.type.analyse",
            "fields": [
                {"key": "laboratoire", "kind": "text", "label_key": "dossier.field.lab"},
                {"key": "resultat", "kind": "text", "label_key": "dossier.field.result"},
            ],
        },
    ],
    "pedagogique": [
        {
            "key": "bulletin",
            "label_key": "dossier.type.bulletin",
            "fields": [
                {"key": "periode", "kind": "text", "label_key": "dossier.field.period"},
                {"key": "moyenne", "kind": "text", "label_key": "dossier.field.average"},
            ],
        },
        {
            "key": "controle",
            "label_key": "dossier.type.controle",
            "fields": [
                {"key": "matiere", "kind": "text", "label_key": "dossier.field.subject"},
                {"key": "note", "kind": "text", "label_key": "dossier.field.grade"},
            ],
        },
        {
            "key": "appreciation",
            "label_key": "dossier.type.appreciation",
            "fields": [
                {"key": "enseignant", "kind": "text", "label_key": "dossier.field.teacher"},
                {"key": "matiere", "kind": "text", "label_key": "dossier.field.subject"},
            ],
        },
    ],
    "administrative": [
        {
            "key": "acte_naissance",
            "label_key": "dossier.type.acte_naissance",
            "fields": [
                {"key": "num_doc", "kind": "text", "label_key": "dossier.field.num_doc"},
                {"key": "delivre_le", "kind": "date", "label_key": "dossier.field.issued_on"},
                {"key": "delivre_par", "kind": "text", "label_key": "dossier.field.issued_by"},
            ],
        },
        {
            "key": "certificat_scolarite",
            "label_key": "dossier.type.certificat_scolarite",
            "fields": [
                {"key": "annee", "kind": "text", "label_key": "dossier.field.year"},
                {"key": "num_doc", "kind": "text", "label_key": "dossier.field.num_doc"},
            ],
        },
        {
            "key": "piece_identite",
            "label_key": "dossier.type.piece_identite",
            "fields": [
                {"key": "type_piece", "kind": "text", "label_key": "dossier.field.id_type"},
                {"key": "num_doc", "kind": "text", "label_key": "dossier.field.num_doc"},
                {"key": "validite", "kind": "date", "label_key": "dossier.field.validity"},
            ],
        },
    ],
    "communication": [
        {
            "key": "courrier",
            "label_key": "dossier.type.courrier",
            "fields": [
                {
                    "key": "sens",
                    "kind": "combo",
                    "label_key": "dossier.field.direction",
                    "options": [("entrant", "dossier.sens.incoming"), ("sortant", "dossier.sens.outgoing")],
                },
                {"key": "correspondant", "kind": "text", "label_key": "dossier.field.correspondent"},
            ],
        },
        {
            "key": "convocation",
            "label_key": "dossier.type.convocation",
            "fields": [
                {
                    "key": "sens",
                    "kind": "combo",
                    "label_key": "dossier.field.direction",
                    "options": [("entrant", "dossier.sens.incoming"), ("sortant", "dossier.sens.outgoing")],
                },
                {"key": "objet", "kind": "text", "label_key": "dossier.field.subject"},
            ],
        },
        {
            "key": "compte_rendu",
            "label_key": "dossier.type.compte_rendu",
            "fields": [
                {"key": "objet", "kind": "text", "label_key": "dossier.field.subject"},
            ],
        },
    ],
    "orientation": [
        {
            "key": "voeu",
            "label_key": "dossier.type.voeu",
            "fields": [
                {"key": "etablissement", "kind": "text", "label_key": "dossier.field.institution"},
                {"key": "filiere", "kind": "text", "label_key": "dossier.field.stream"},
            ],
        },
        {
            "key": "stage",
            "label_key": "dossier.type.stage",
            "fields": [
                {"key": "entreprise", "kind": "text", "label_key": "dossier.field.company"},
                {"key": "duree", "kind": "text", "label_key": "dossier.field.duration"},
            ],
        },
        {
            "key": "bilan",
            "label_key": "dossier.type.bilan",
            "fields": [
                {"key": "conseiller", "kind": "text", "label_key": "dossier.field.counselor"},
                {"key": "periode", "kind": "text", "label_key": "dossier.field.period"},
            ],
        },
    ],
    "autre": [],
}

# Type générique (compat. anciennes entrées sans type, section « Autre »)
GENERIC_TYPE = {"key": "document", "label_key": "dossier.type.document", "fields": []}

# ──────────────────────────────────────────────────────────────
#   Statuts (badges colorés) — couleurs résolues depuis la palette
#   active (bg = rôle container, fg = text_strong : lisible en dark ET light)
# ──────────────────────────────────────────────────────────────
STATUS_DEFS = [
    {"key": "en_attente", "label_key": "dossier.status.pending", "bg": "tertiary_container"},
    {"key": "valide", "label_key": "dossier.status.valid", "bg": "secondary_container"},
    {"key": "refuse", "label_key": "dossier.status.rejected", "bg": "error_container"},
    {"key": "expire", "label_key": "dossier.status.expired", "bg": "surface_variant"},
]


def _types_for(section: str) -> list[dict]:
    """Types disponibles pour une section (+ le type générique en fallback)."""
    types = list(TYPES.get(section, []))
    if not any(t["key"] == "document" for t in types):
        types = types + [GENERIC_TYPE]
    return types


def _type_def(section: str, type_key: str) -> dict:
    for t in _types_for(section):
        if t["key"] == type_key:
            return t
    return GENERIC_TYPE


def _type_label(section: str, type_key: str) -> str:
    return _(_type_def(section, type_key)["label_key"])


def _status_def(status_key: str) -> dict:
    for s in STATUS_DEFS:
        if s["key"] == status_key:
            return s
    return STATUS_DEFS[0]


def _all_types() -> list[dict]:
    """Tous les types de toutes les sections (dédupliqués, + le générique)."""
    seen: dict[str, dict] = {}
    for sec_types in TYPES.values():
        for t in sec_types:
            seen[t["key"]] = t
    seen[GENERIC_TYPE["key"]] = GENERIC_TYPE
    return list(seen.values())


# Rôles de couleurs des badges de section (résolus depuis la palette active).
# Chaque section prend une couleur de conteneur différente pour être distinguable
# dans la vue chronologique, en dark comme en light (fg = text_strong).
SECTION_BADGE_ROLES = [
    "primary_container",
    "secondary_container",
    "tertiary_container",
    "error_container",
    "surface_variant",
]


def _section_badge_role(section_key: str) -> str:
    """Rôle de couleur de badge pour une section (cyclique sur l'ordre SECTIONS)."""
    for i, (key, _label) in enumerate(SECTIONS):
        if key == section_key:
            return SECTION_BADGE_ROLES[i % len(SECTION_BADGE_ROLES)]
    return "surface_variant"


def _combo_qss() -> str:
    """QSS M3 pour M3ComboBox — tokens palette, aucun hardcoding."""
    p = ds.p
    return (
        f"QComboBox {{ background: {p.surface}; color: {p.text_strong}; "
        f"border: 1px solid {p.outline}; border-radius: {ds.radius_xs}px; "
        f"padding: 0 {ds.space_md}px; font-size: {ds.font_px_md}px; }}"
        f"QComboBox::drop-down {{ border: none; width: {ds.space_xl}px; }}"
        f"QComboBox::down-arrow {{ width: {ds.space_md}px; height: {ds.space_md}px; }}"
        f"QComboBox QAbstractItemView {{ background: {p.surface}; color: {p.text_strong}; "
        f"border: 1px solid {p.outline}; border-radius: {ds.radius_xs}px; outline: none; "
        f"selection-background-color: {p.primary_container}; selection-color: {p.text_strong}; }}"
    )


def _date_qss() -> str:
    """QSS M3 pour M3DateEdit — tokens palette, aucun hardcoding."""
    p = ds.p
    return (
        f"QDateEdit {{ background: {p.surface}; color: {p.text_strong}; "
        f"border: 1px solid {p.outline}; border-radius: {ds.radius_xs}px; "
        f"padding: 0 {ds.space_md}px; }}"
        f"QDateEdit QLineEdit {{ color: {p.text_strong}; background: {p.surface}; }}"
    )


class _EntryDialog(M3Dialog):
    """Dialogue modal typé : le type choisi détermine les champs affichés."""

    def __init__(self, section: str, entry: dict, base_dir: str = "", parent=None):
        super().__init__(parent)
        self._section = section
        self._entry = entry.copy()
        self._base_dir = base_dir
        self._is_create = entry.get("titre", "") == "" and entry.get("doc", "") == ""
        self.setWindowTitle(_("dossier.dialog.title_add") if self._is_create else _("dossier.dialog.title_edit"))
        # Paire dorée purement tokenisée (≈ 815×504)
        _min_h = ds.space_xxl * 6
        self.setMinimumSize(ds.golden_width(_min_h), _min_h)
        self.setModal(True)
        self._field_widgets: dict[str, QWidget] = {}
        self._build_ui()
        self._refresh_files()

    def _build_ui(self):
        p = ds.p
        _fh = ds.field_height
        self.setStyleSheet(f"M3Dialog {{ background-color: {p.surface}; }}")
        layout = QVBoxLayout(self)
        layout.setSpacing(ds.space_sm)
        layout.setContentsMargins(ds.space_lg, ds.space_lg, ds.space_lg, ds.space_md)
        layout.addWidget(
            M3Label(
                _("dossier.dialog.title_add") if self._is_create else _("dossier.dialog.title_edit"),
                style="title_medium",
            )
        )

        # ── Ligne Type + Statut ──
        row = QHBoxLayout()
        row.setSpacing(ds.space_xs)
        type_lbl = M3Label(_("dossier.type_label"), style="label_small")
        type_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        row.addWidget(type_lbl)
        self._type_combo = M3ComboBox()
        for t in _types_for(self._section):
            self._type_combo.addItem(_(t["label_key"]), t["key"])
        idx = self._type_combo.findData(self._entry.get("type", ""))
        self._type_combo.setCurrentIndex(max(idx, 0))
        self._type_combo.setFixedHeight(_fh)
        self._type_combo.setStyleSheet(_combo_qss())
        self._type_combo.currentIndexChanged.connect(self._rebuild_fields)
        row.addWidget(self._type_combo, 1)

        status_lbl = M3Label(_("dossier.status_label"), style="label_small")
        status_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        row.addWidget(status_lbl)
        self._status_combo = M3ComboBox()
        for s in STATUS_DEFS:
            self._status_combo.addItem(_(s["label_key"]), s["key"])
        sidx = self._status_combo.findData(self._entry.get("status", "en_attente"))
        self._status_combo.setCurrentIndex(max(sidx, 0))
        self._status_combo.setFixedHeight(_fh)
        self._status_combo.setStyleSheet(_combo_qss())
        row.addWidget(self._status_combo)
        layout.addLayout(row)

        # ── Zone de champs dynamiques (selon le type) ──
        self._fields_box = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_box)
        self._fields_layout.setSpacing(ds.space_xs)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._fields_box)
        self._rebuild_fields()

        # ── Date + Titre ──
        row2 = QHBoxLayout()
        row2.setSpacing(ds.space_xs)
        date_lbl = M3Label(_("dossier.dialog_date"), style="label_small")
        date_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        row2.addWidget(date_lbl)
        self._inp_date = M3DateEdit()
        self._inp_date.setDisplayFormat("yyyy-MM-dd")
        self._inp_date.setCalendarPopup(True)
        self._inp_date.setSpecialValueText(" ")
        self._inp_date.setFixedHeight(_fh)
        self._inp_date.setStyleSheet(_date_qss())
        try:
            d = QDate.fromString(self._entry.get("date", ""), "yyyy-MM-dd")
            if d.isValid():
                self._inp_date.setDate(d)
        except Exception:
            pass
        row2.addWidget(self._inp_date)
        titre_lbl = M3Label(_("dossier.title_placeholder"), style="label_small")
        titre_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        row2.addWidget(titre_lbl)
        self._inp_titre = M3TextField(placeholder=_("dossier.title_placeholder"))
        self._inp_titre.setFixedHeight(_fh)
        self._inp_titre.setStyleSheet(ds.flat_input_qss())
        self._inp_titre.setText(self._entry.get("titre", ""))
        row2.addWidget(self._inp_titre, 1)
        layout.addLayout(row2)

        # Auto-titre : suggère le libellé du type à la création
        if self._is_create and not self._entry.get("titre"):
            self._inp_titre.setText(_type_label(self._section, self._type_combo.currentData()))

        # ── Description ──
        self._inp_doc = M3TextEdit()
        self._inp_doc.setPlaceholderText(_("dossier.description_placeholder"))
        self._inp_doc.setStyleSheet(ds.flat_input_qss())
        self._inp_doc.setPlainText(self._entry.get("doc", ""))
        layout.addWidget(self._inp_doc, 1)

        # ── Fichiers joints ──
        layout.addWidget(M3Label(_("dossier.attached_files"), style="title_small"))
        self._file_table = M3TableWidget(theme=ds.phi)
        self._file_table.setStyleSheet(ds.table_qss())
        self._file_table.set_headers([_("dossier.file_headers_name"), _("dossier.file_headers_doc")])
        self._file_table.horizontalHeader().setSectionResizeMode(0, M3HeaderView.Interactive)
        self._file_table.setColumnWidth(0, ds.space_xxl + ds.space_lg)
        self._file_table.horizontalHeader().setSectionResizeMode(1, M3HeaderView.Stretch)
        self._file_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._file_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._file_table.setAlternatingRowColors(False)
        self._file_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        file_btns = QHBoxLayout()
        file_btns.setSpacing(ds.space_xs)
        add_btn = M3Button("+", variant=ButtonVariant.FILLED)
        add_btn.clicked.connect(self._add_file)
        file_btns.addWidget(add_btn)
        del_btn = M3Button(_("dossier.delete"), variant=ButtonVariant.OUTLINED)
        del_btn.clicked.connect(self._delete_file)
        file_btns.addWidget(del_btn)
        file_btns.addStretch()
        layout.addLayout(file_btns)
        layout.addWidget(self._file_table)
        buttons = M3DialogButtonBox(M3DialogButtonBox.Ok | M3DialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ── Champs dynamiques selon le type ──

    @safe_slot("Unknown._rebuild_fields")
    def _rebuild_fields(self, *_args):
        """Reconstruit la zone de champs selon le type sélectionné.

        Les valeurs déjà saisies sont conservées et réinjectées si la clé
        existe dans le nouveau type (pas de perte de saisie au changement).
        """
        # Conserver les valeurs déjà saisies dans fields (survit aux allers-retours A→B→A)
        fields = dict(self._entry.get("fields", {}) or {})
        for key, w in self._field_widgets.items():
            fields[key] = self._read_field_value(w)
        self._entry["fields"] = fields
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._field_widgets = {}
        tdef = _type_def(self._section, self._type_combo.currentData())
        p = ds.p
        _fh = ds.field_height
        for f in tdef["fields"]:
            lbl = M3Label(_(f["label_key"]), style="label_small")
            lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
            self._fields_layout.addWidget(lbl)
            w = self._make_field(f, fields.get(f["key"], ""))
            self._field_widgets[f["key"]] = w
            self._fields_layout.addWidget(w)

    def _read_field_value(self, w):
        """Valeur actuelle d'un champ dynamique (date / combo / texte)."""
        if isinstance(w, M3DateEdit):
            return w.date().toString("yyyy-MM-dd") if w.date().isValid() else ""
        if isinstance(w, M3ComboBox):
            return w.currentData() or ""
        return w.text()

    def _make_field(self, fdef: dict, value):
        _fh = ds.field_height
        kind = fdef["kind"]
        if kind == "date":
            w = M3DateEdit()
            w.setDisplayFormat("yyyy-MM-dd")
            w.setCalendarPopup(True)
            w.setSpecialValueText(" ")
            w.setFixedHeight(_fh)
            w.setStyleSheet(_date_qss())
            d = QDate.fromString(str(value), "yyyy-MM-dd") if value else QDate()
            if d.isValid():
                w.setDate(d)
            return w
        if kind == "combo":
            w = M3ComboBox()
            for opt_val, opt_label in fdef.get("options", []):
                w.addItem(_(opt_label), opt_val)
            if value:
                i = w.findData(value)
                if i >= 0:
                    w.setCurrentIndex(i)
            w.setFixedHeight(_fh)
            w.setStyleSheet(_combo_qss())
            return w
        w = M3TextField(str(value))
        w.setFixedHeight(_fh)
        w.setStyleSheet(ds.flat_input_qss())
        return w

    # ── Fichiers joints ──

    def _entry_dir(self) -> str:
        if not self._base_dir:
            return ""
        d = os.path.join(self._base_dir, str(self._entry.get("no", 0)))
        os.makedirs(d, exist_ok=True)
        return d

    def _refresh_files(self):
        d = self._entry_dir()
        self._file_table.setRowCount(0)
        if not d:
            return
        try:
            files = sorted(os.listdir(d))
        except Exception:
            return
        titre = self._entry.get("titre", "")
        for i, fname in enumerate(files):
            self._file_table.setRowCount(i + 1)
            self._file_table.setItem(i, 0, QTableWidgetItem(fname))
            self._file_table.setItem(i, 1, QTableWidgetItem(titre))

    @safe_slot("Unknown._add_file")
    def _add_file(self):
        d = self._entry_dir()
        if not d:
            return
        paths, _ign = QFileDialog.getOpenFileNames(self, _("dossier.add_files"), "")
        if not paths:
            return
        for p in paths:
            shutil.copy2(p, os.path.join(d, os.path.basename(p)))
        self._refresh_files()

    @safe_slot("Unknown._delete_file")
    def _delete_file(self):
        rows = self._file_table.selectionModel().selectedRows()
        if not rows:
            return
        name = self._file_table.item(rows[0].row(), 0).text()
        r = QMessageBox.question(
            self,
            _("dossier.confirm_delete"),
            _("dossier.confirm_delete_file").format(name=name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        try:
            os.remove(os.path.join(self._entry_dir(), name))
            self._refresh_files()
        except Exception as e:
            QMessageBox.critical(self, _("dossier.error"), str(e))

    # ── Sauvegarde ──

    @safe_slot("Unknown._on_save")
    def _on_save(self):
        self._entry["type"] = self._type_combo.currentData()
        self._entry["status"] = self._status_combo.currentData()
        self._entry["titre"] = self._inp_titre.text()
        self._entry["date"] = self._inp_date.date().toString("yyyy-MM-dd") if self._inp_date.date().isValid() else ""
        self._entry["doc"] = self._inp_doc.toPlainText()
        fields = {}
        for key, w in self._field_widgets.items():
            fields[key] = self._read_field_value(w)
        self._entry["fields"] = fields
        self.accept()

    def get_entry(self) -> dict:
        return self._entry


class _Page(M3Frame):
    """Section : filtre par type + table (Date/Type/Statut/Titre/Description) + fichiers + aperçu."""

    # Signal émis après toute MUTATION d'une entrée (ajout, édition, suppression)
    # → DossierPanel le relaie (entries_changed) et rafraîchit la chronologie.
    entries_changed = Signal()

    def __init__(self, key: str, student_id: int, parent=None):
        super().__init__(parent=parent)
        self._key = key
        self._sid = student_id
        self._entries: list[dict] = []
        self._current_entry: dict | None = None
        self._base_dir = ""
        self._build()

    def _build(self):
        p = ds.p
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, 0)
        layout.setSpacing(ds.space_sm)

        # ── Fiche santé (section médicale uniquement) ──
        # La fiche santé vit DANS la section Médical du dossier (pas d'onglet
        # dédié) : allergies, notes médicales, contact urgence.
        self._health_widgets: dict[str, QWidget] = {}
        if self._key == "medicale":
            fiche_card = M3Card(variant=CardVariant.ELEVATED)
            fcl = fiche_card.content_layout()
            fcl.setSpacing(ds.space_sm)
            fcl.addWidget(M3Label(_("dossier.health_fiche"), style="title_small"))
            fg = QGridLayout()
            fg.setSpacing(ds.space_sm)
            fg.setColumnStretch(0, 1)
            fg.setColumnStretch(1, 1)
            r = 0
            fg.addWidget(M3Label(_("student_form.health_allergies"), style="label_small"), r, 0, 1, 2)
            r += 1
            self._health_widgets["allergies"] = M3TextEdit()
            self._health_widgets["allergies"].setFixedHeight(ds.space_xxxl)
            self._health_widgets["allergies"].setPlaceholderText(_("student_form.health_allergies_placeholder"))
            fg.addWidget(self._health_widgets["allergies"], r, 0, 1, 2)
            r += 1
            fg.addWidget(M3Label(_("student_form.health_medical_notes"), style="label_small"), r, 0, 1, 2)
            r += 1
            self._health_widgets["medical_notes"] = M3TextEdit()
            self._health_widgets["medical_notes"].setFixedHeight(ds.space_xxxl)
            self._health_widgets["medical_notes"].setPlaceholderText(_("student_form.health_notes_placeholder"))
            fg.addWidget(self._health_widgets["medical_notes"], r, 0, 1, 2)
            r += 1
            fg.addWidget(M3Label(_("student_form.health_emergency_contact"), style="label_small"), r, 0)
            fg.addWidget(M3Label(_("student_form.health_emergency_phone"), style="label_small"), r, 1)
            r += 1
            self._health_widgets["emergency_contact"] = M3TextField()
            self._health_widgets["emergency_contact"].setFixedHeight(ds.field_height)
            fg.addWidget(self._health_widgets["emergency_contact"], r, 0)
            self._health_widgets["emergency_phone"] = M3TextField()
            self._health_widgets["emergency_phone"].setFixedHeight(ds.field_height)
            fg.addWidget(self._health_widgets["emergency_phone"], r, 1)
            fcl.addLayout(fg)
            layout.addWidget(fiche_card)

        # ── Barre d'actions : ajouter / supprimer / filtre par type ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(ds.space_xs)
        add_btn = M3Button("+ " + _("dossier.add_entry"), variant=ButtonVariant.FILLED)
        add_btn.clicked.connect(self._add_entry)
        btn_row.addWidget(add_btn)
        del_btn = M3Button("- " + _("dossier.delete_entry"), variant=ButtonVariant.OUTLINED)
        del_btn.clicked.connect(self._delete_entry)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        filter_lbl = M3Label(_("dossier.filter_label"), style="label_small")
        filter_lbl.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        btn_row.addWidget(filter_lbl)
        self._filter_combo = M3ComboBox()
        self._filter_combo.addItem(_("dossier.filter.all"), "")
        for t in _types_for(self._key):
            self._filter_combo.addItem(_(t["label_key"]), t["key"])
        self._filter_combo.setFixedHeight(ds.field_height)
        self._filter_combo.setStyleSheet(_combo_qss())
        self._filter_combo.currentIndexChanged.connect(self._refresh_table)
        btn_row.addWidget(self._filter_combo)
        layout.addLayout(btn_row)

        # ── Table principale : Date | Type | Statut | Titre | Description ──
        self._table = M3TableWidget(theme=ds.phi)
        self._table.setStyleSheet(ds.table_qss())
        self._table.set_headers(
            [
                _("dossier.table_headers"),
                _("dossier.table_headers_type"),
                _("dossier.table_headers_status"),
                _("dossier.table_headers_title"),
                _("dossier.table_headers_description"),
            ]
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, M3HeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, M3HeaderView.Interactive)
        hh.setSectionResizeMode(2, M3HeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, M3HeaderView.Interactive)
        hh.setSectionResizeMode(4, M3HeaderView.Stretch)
        self._table.setColumnWidth(1, ds.space_xxxl + ds.space_xl)
        self._table.setColumnWidth(3, ds.space_xxxl * 2)
        self._table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._table.itemSelectionChanged.connect(self._on_select)
        self._table.viewport().setCursor(Qt.PointingHandCursor)
        self._table.setToolTip(_("history.dblclick_hint"))
        self._table.installEventFilter(self)
        self._table.cellDoubleClicked.connect(lambda r, c: self._edit_entry(r))
        self._table.horizontalHeader().sectionResized.connect(self._on_col_resize)
        TableSettings.restore(self._table, f"dossier/{self._key}")
        layout.addWidget(self._table, 3)

        # ── Fichiers + aperçu ──
        bottom = QHBoxLayout()
        bottom.setSpacing(ds.space_sm)
        self._file_table = M3TableWidget(theme=ds.phi)
        self._file_table.setStyleSheet(ds.table_qss())
        self._file_table.set_headers([_("dossier.file_headers_name"), _("dossier.file_headers_doc")])
        self._file_table.horizontalHeader().setSectionResizeMode(0, M3HeaderView.Interactive)
        self._file_table.setColumnWidth(0, ds.space_xxl + ds.space_lg)
        self._file_table.horizontalHeader().setSectionResizeMode(1, M3HeaderView.Stretch)
        self._file_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._file_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._file_table.setAlternatingRowColors(False)
        self._file_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._file_table.viewport().setCursor(Qt.PointingHandCursor)
        self._file_table.setToolTip(_("history.dblclick_hint"))
        self._file_table.installEventFilter(self)
        self._file_table.itemSelectionChanged.connect(self._on_file_selected)
        self._file_table.cellDoubleClicked.connect(self._on_preview_file_row)
        bottom.addWidget(self._file_table, 5)
        self._preview_frame = M3Card(variant=CardVariant.FILLED, parent=self)
        self._preview_layout = self._preview_frame.content_layout()
        self._preview_widget = M3Label(_("dossier.preview_placeholder"))
        self._preview_widget.setAlignment(Qt.AlignCenter)
        self._preview_widget.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {p.text_disabled};")
        self._preview_layout.addWidget(self._preview_widget)
        bottom.addWidget(self._preview_frame, 8)
        layout.addLayout(bottom, 5)

        ds.theme_changed.connect(self._restyle)

    @safe_slot("Unknown._restyle")
    def _restyle(self):
        self._table.setStyleSheet(ds.table_qss())
        self._file_table.setStyleSheet(ds.table_qss())
        self._filter_combo.setStyleSheet(_combo_qss())
        self._preview_widget.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {ds.p.text_disabled};")
        for w in self._health_widgets.values():
            w.setStyleSheet(ds.flat_input_qss())
        self._refresh_table()  # ré-applique les couleurs de badges avec la palette active

    # ── CRUD entrées ──

    def _visible_entries(self) -> list[dict]:
        """Entrées triées par date desc, filtrées par le type sélectionné.

        Les anciennes entrées sans clé `type` sont normalisées en « document »
        pour être cohérentes avec leur affichage (rétrocompatibilité).
        """
        entries = sorted(self._entries, key=lambda e: e.get("date", ""), reverse=True)
        ftype = self._filter_combo.currentData() if hasattr(self, "_filter_combo") else ""
        if ftype:
            entries = [e for e in entries if (e.get("type") or "document") == ftype]
        return entries

    @safe_slot("Unknown._add_entry")
    def _add_entry(self):
        no = len(self._entries) + 1
        ftype = self._filter_combo.currentData() if hasattr(self, "_filter_combo") else ""
        entry = {
            "no": no,
            "date": date.today().isoformat(),
            "type": ftype or _types_for(self._key)[0]["key"],
            "titre": "",
            "doc": "",
            "status": "en_attente",
            "fields": {},
        }
        dlg = _EntryDialog(self._key, entry, self._base_dir, self)
        if dlg.exec() == M3Dialog.Accepted:
            self._entries.append(dlg.get_entry())
            self._refresh_table()
            self.entries_changed.emit()

    def _edit_entry(self, row: int):
        vis = self._visible_entries()
        if 0 <= row < len(vis):
            dlg = _EntryDialog(self._key, vis[row].copy(), self._base_dir, self)
            if dlg.exec() == M3Dialog.Accepted:
                updated = dlg.get_entry()
                for i, e in enumerate(self._entries):
                    if e.get("no") == updated.get("no"):
                        self._entries[i] = updated
                        break
                self._refresh_table()
                self.entries_changed.emit()

    @safe_slot("Unknown._delete_entry")
    def _delete_entry(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        vis = self._visible_entries()
        idx = rows[0].row()
        if idx < 0 or idx >= len(vis):
            return
        e = vis[idx]
        r = QMessageBox.question(
            self,
            _("dossier.confirm_delete_entry"),
            _("dossier.confirm_delete_entry_msg").format(title=e.get("titre", "")),
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        for i, entry in enumerate(self._entries):
            if entry.get("no") == e.get("no"):
                self._entries.pop(i)
                break
        self._current_entry = None
        self._refresh_table()
        self.entries_changed.emit()

    @safe_slot("Unknown._refresh_table")
    def _refresh_table(self, *_args):
        self._table.blockSignals(True)
        vis = self._visible_entries()
        self._table.setRowCount(len(vis))
        p = ds.p
        for i, e in enumerate(vis):
            # Date
            self._table.setItem(i, 0, QTableWidgetItem(e.get("date", "")))
            # Type (libellé en gras, couleur primaire)
            t_item = QTableWidgetItem(_type_label(self._key, e.get("type", "")))
            tf = t_item.font()
            tf.setBold(True)
            t_item.setFont(tf)
            t_item.setForeground(QColor(p.primary))
            self._table.setItem(i, 1, t_item)
            # Statut (badge coloré)
            sd = _status_def(e.get("status", "en_attente"))
            s_item = QTableWidgetItem(_(sd["label_key"]))
            s_item.setBackground(QColor(getattr(p, sd["bg"])))
            s_item.setForeground(QColor(p.text_strong))
            sf = s_item.font()
            sf.setBold(True)
            s_item.setFont(sf)
            s_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 2, s_item)
            # Titre
            self._table.setItem(i, 3, QTableWidgetItem(e.get("titre", "")))
            # Description (extrait)
            doc = e.get("doc", "")
            snippet = doc[:80].replace("\n", " ") + ("…" if len(doc) > 80 else "")
            self._table.setItem(i, 4, QTableWidgetItem(snippet))
        self._table.blockSignals(False)
        if vis:
            self._table.selectRow(0)

    @safe_slot("Unknown._on_select")
    def _on_select(self):
        rows = self._table.selectionModel().selectedRows()
        if rows:
            vis = self._visible_entries()
            idx = rows[0].row()
            if 0 <= idx < len(vis):
                self._current_entry = vis[idx]
                self._refresh_files()

    # ── Fichiers + aperçu ──

    def _entry_dir(self) -> str:
        if not self._base_dir:
            return ""
        no = self._current_entry.get("no", 0) if self._current_entry else 0
        d = os.path.join(self._base_dir, str(no))
        os.makedirs(d, exist_ok=True)
        return d

    def _refresh_files(self):
        d = self._entry_dir()
        self._file_table.setRowCount(0)
        if not d:
            return
        try:
            files = sorted(os.listdir(d))
        except Exception:
            return
        titre = self._current_entry.get("titre", "") if self._current_entry else ""
        for i, fname in enumerate(files):
            self._file_table.setRowCount(i + 1)
            self._file_table.setItem(i, 0, QTableWidgetItem(fname))
            self._file_table.setItem(i, 1, QTableWidgetItem(titre))

    @safe_slot("Unknown._on_preview_file_row")
    def _on_preview_file_row(self, row: int, col: int):
        name = self._file_table.item(row, 0)
        if not name:
            return
        from larccommon.widgets import FileViewer

        FileViewer(os.path.join(self._entry_dir(), name.text()), self).exec()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = obj.currentRow()
            if row < 0:
                return False
            if obj is self._table:
                self._edit_entry(row)
                return True
            if obj is self._file_table:
                self._on_preview_file_row(row, 0)
                return True
        return super().eventFilter(obj, event)

    @safe_slot("Unknown._on_file_selected")
    def _on_file_selected(self):
        rows = self._file_table.selectionModel().selectedRows()
        if not rows or not self._base_dir:
            return
        name = self._file_table.item(rows[0].row(), 0)
        if not name:
            return
        path = os.path.join(self._entry_dir(), name.text())
        ext = os.path.splitext(name.text())[1].lower()
        w = self._preview_layout.takeAt(0)
        if w and w.widget():
            w.widget().deleteLater()
        if ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
            from PySide6.QtGui import QPixmap

            lbl = M3Label()
            pix = QPixmap(path)
            lbl.setPixmap(pix.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl.setAlignment(Qt.AlignCenter)
            self._preview_layout.addWidget(lbl)
        elif ext in {".txt", ".csv", ".md", ".json", ".py", ".sql"}:
            ed = M3TextEdit()
            ed.setReadOnly(True)
            ed.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {ds.p.text_strong};")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    ed.setPlainText(f.read()[:5000])
            except Exception:
                ed.setPlainText(_("dossier.fallback_text"))
            self._preview_layout.addWidget(ed)
        else:
            lbl = M3Label(_("dossier.file_info").format(name=name.text(), bytes=f"{os.path.getsize(path):,}"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {ds.p.text_strong};")
            self._preview_layout.addWidget(lbl)

    @safe_slot("Unknown._on_col_resize")
    def _on_col_resize(self, *_args):
        TableSettings.save(self._table, f"dossier/{self._key}")

    # ── API publique (utilisée par student_form.py) ──

    def set_directory(self, base_dir: str):
        self._base_dir = base_dir
        if self._current_entry:
            self._refresh_files()

    def edit_entry(self, entry: dict):
        """Édite une entrée identifiée par son `no` — appelé depuis la timeline.

        Opère directement sur `self._entries` (pas d'index `vis`) pour rester
        robuste au tri par date et aux filtres de type actifs dans la page.
        """
        for i, e in enumerate(self._entries):
            if e.get("no") == entry.get("no"):
                dlg = _EntryDialog(self._key, e.copy(), self._base_dir, self)
                if dlg.exec() == M3Dialog.Accepted:
                    self._entries[i] = dlg.get_entry()
                    self._refresh_table()
                    self.entries_changed.emit()
                return

    def load_entries(self, entries: list[dict]):
        self._entries = list(entries) if entries else []
        self._current_entry = None
        self._refresh_table()

    def get_entries(self) -> list[dict]:
        return self._entries

    # ── Fiche santé (section médicale) ──

    def set_health(self, data: dict):
        if not self._health_widgets:
            return
        data = data or {}
        self._health_widgets["allergies"].setPlainText(data.get("allergies", "") or "")
        self._health_widgets["medical_notes"].setPlainText(data.get("medical_notes", "") or "")
        self._health_widgets["emergency_contact"].setText(data.get("emergency_contact", "") or "")
        self._health_widgets["emergency_phone"].setText(data.get("emergency_phone", "") or "")

    def get_health(self) -> dict:
        if not self._health_widgets:
            return {}
        return {
            "allergies": self._health_widgets["allergies"].toPlainText().strip(),
            "medical_notes": self._health_widgets["medical_notes"].toPlainText().strip(),
            "emergency_contact": self._health_widgets["emergency_contact"].text().strip(),
            "emergency_phone": self._health_widgets["emergency_phone"].text().strip(),
        }


class ConfidentialPanel(_Page):
    """Liste de documents confidentiels (description + pièces jointes), hors sections du dossier.

    Réutilise toute la mécanique de _Page (types, statuts, fichiers, aperçu)
    avec la clé "confidentiel" : stockée dans notes_json["confidentiel"],
    fichiers dans data/students/{sid}/confidentiel/. Hors de la chronologie.
    """

    def __init__(self, student_id: int, parent=None):
        super().__init__("confidentiel", student_id, parent)


class _TimelinePage(M3Frame):
    """Vue chronologique globale (Niveau 3) : toutes les sections triées par date.

    Filtres par section et par type, badges de section/statut colorés,
    double-clic sur une ligne pour éditer l'entrée dans sa section.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._pages: list[_Page] = []
        self._on_edit = None
        self._build()

    def set_on_edit(self, callback):
        self._on_edit = callback

    def _build(self):
        p = ds.p
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, 0)
        layout.setSpacing(ds.space_sm)

        # ── Filtres : section + type ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(ds.space_xs)
        lbl_sec = M3Label(_("dossier.timeline.section_filter"), style="label_small")
        lbl_sec.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        filter_row.addWidget(lbl_sec)
        self._sec_combo = M3ComboBox()
        self._sec_combo.addItem(_("dossier.filter.all"), "")
        for key, label in SECTIONS:
            self._sec_combo.addItem(label, key)
        self._sec_combo.setFixedHeight(ds.field_height)
        self._sec_combo.setStyleSheet(_combo_qss())
        self._sec_combo.currentIndexChanged.connect(self._on_filter)
        filter_row.addWidget(self._sec_combo)
        lbl_type = M3Label(_("dossier.type_label"), style="label_small")
        lbl_type.setStyleSheet(f"color: {p.text_strong}; font-weight: bold;")
        filter_row.addWidget(lbl_type)
        self._type_combo = M3ComboBox()
        self._type_combo.setFixedHeight(ds.field_height)
        self._type_combo.setStyleSheet(_combo_qss())
        self._type_combo.currentIndexChanged.connect(self._refresh_table)
        filter_row.addWidget(self._type_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ── Table : Date | Section | Type | Statut | Titre ──
        self._table = M3TableWidget(theme=ds.phi)
        self._table.setStyleSheet(ds.table_qss())
        self._table.set_headers(
            [
                _("dossier.table_headers"),
                _("dossier.timeline.section"),
                _("dossier.table_headers_type"),
                _("dossier.table_headers_status"),
                _("dossier.table_headers_title"),
            ]
        )
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, M3HeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, M3HeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, M3HeaderView.Interactive)
        hh.setSectionResizeMode(3, M3HeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, M3HeaderView.Stretch)
        self._table.setColumnWidth(2, ds.space_xxxl + ds.space_xl)
        self._table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._table.viewport().setCursor(Qt.PointingHandCursor)
        self._table.setToolTip(_("history.dblclick_hint"))
        self._table.installEventFilter(self)
        self._table.cellDoubleClicked.connect(self._on_edit_row)
        layout.addWidget(self._table, 1)

        self._hint = M3Label(_("dossier.timeline.hint"))
        self._hint.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {ds.p.text_disabled};")
        layout.addWidget(self._hint)

        ds.theme_changed.connect(self._restyle)
        self._rebuild_type_combo()

    @safe_slot("_TimelinePage._restyle")
    def _restyle(self):
        self._table.setStyleSheet(ds.table_qss())
        self._sec_combo.setStyleSheet(_combo_qss())
        self._type_combo.setStyleSheet(_combo_qss())
        self._hint.setStyleSheet(f"font-size: {ds.font_px_sm}px; color: {ds.p.text_disabled};")
        self._refresh_table()  # ré-applique les couleurs de badges avec la palette active

    # ── Filtres ──

    @safe_slot("_TimelinePage._on_filter")
    def _on_filter(self, *_args):
        self._rebuild_type_combo()
        self._refresh_table()

    def _rebuild_type_combo(self, *_args):
        sec = self._sec_combo.currentData() if hasattr(self, "_sec_combo") else ""
        prev_type = self._type_combo.currentData() if hasattr(self, "_type_combo") else ""
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        self._type_combo.addItem(_("dossier.filter.all"), "")
        types = _all_types() if not sec else _types_for(sec)
        for t in types:
            self._type_combo.addItem(_(t["label_key"]), t["key"])
        # Préserver le type filtré si la section sélectionnée le propose encore
        # (sinon reset sur « Tous ») — indispensable pour le refresh temps réel.
        idx = self._type_combo.findData(prev_type) if prev_type else 0
        self._type_combo.setCurrentIndex(max(idx, 0))
        self._type_combo.blockSignals(False)

    # ── Données ──

    def refresh(self, pages: list):
        self._pages = pages
        self._rebuild_type_combo()
        self._refresh_table()

    def _all_entries(self) -> list[dict]:
        rows = []
        for (key, label), page in zip(SECTIONS, self._pages):
            for e in page.get_entries():
                row = dict(e)
                row["_section_key"] = key
                row["_section_label"] = label
                rows.append(row)
        return rows

    def _visible_entries(self) -> list[dict]:
        rows = self._all_entries()
        sec = self._sec_combo.currentData() if hasattr(self, "_sec_combo") else ""
        ttype = self._type_combo.currentData() if hasattr(self, "_type_combo") else ""
        if sec:
            rows = [r for r in rows if r.get("_section_key") == sec]
        if ttype:
            rows = [r for r in rows if (r.get("type") or "document") == ttype]
        rows.sort(key=lambda r: r.get("date", ""), reverse=True)
        return rows

    @safe_slot("Unknown._refresh_table")
    def _refresh_table(self, *_args):
        self._table.blockSignals(True)
        vis = self._visible_entries()
        self._table.setRowCount(len(vis))
        p = ds.p
        for i, e in enumerate(vis):
            self._table.setItem(i, 0, QTableWidgetItem(e.get("date", "")))
            # Section (badge coloré)
            sec_item = QTableWidgetItem(e.get("_section_label", ""))
            sec_item.setBackground(QColor(getattr(p, _section_badge_role(e.get("_section_key", "")))))
            sec_item.setForeground(QColor(p.text_strong))
            sec_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 1, sec_item)
            # Type (gras, primaire)
            t_item = QTableWidgetItem(_type_label(e.get("_section_key", ""), e.get("type", "")))
            tf = t_item.font()
            tf.setBold(True)
            t_item.setFont(tf)
            t_item.setForeground(QColor(p.primary))
            self._table.setItem(i, 2, t_item)
            # Statut (badge coloré)
            sd = _status_def(e.get("status", "en_attente"))
            s_item = QTableWidgetItem(_(sd["label_key"]))
            s_item.setBackground(QColor(getattr(p, sd["bg"])))
            s_item.setForeground(QColor(p.text_strong))
            sf = s_item.font()
            sf.setBold(True)
            s_item.setFont(sf)
            s_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 3, s_item)
            # Titre
            self._table.setItem(i, 4, QTableWidgetItem(e.get("titre", "")))
        self._table.blockSignals(False)
        if vis:
            self._table.selectRow(0)

    # ── Édition depuis la timeline ──

    @safe_slot("Unknown._on_edit_row")
    def _on_edit_row(self, row: int, col: int):
        vis = self._visible_entries()
        if 0 <= row < len(vis) and self._on_edit:
            self._on_edit(vis[row])

    def eventFilter(self, obj, event):
        if obj is self._table and event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = self._table.currentRow()
            if row >= 0:
                self._on_edit_row(row, 0)
                return True
        return super().eventFilter(obj, event)


class DossierPanel(QWidget):
    """Panneau Dossiers : boutons M3 + contenu table/détail pour chaque section.

    Niveau 3 : la vue chronologique globale (_TimelinePage) est exposée via la
    propriété `timeline` pour être intégrée comme ONGLET COMPLET du
    StudentEditDialog (à côté de Dossiers). Le bouton « Chronologie » du rail
    émet `timeline_requested` pour que le dialogue hôte bascule sur cet onglet.
    """

    # Signal émis quand l'utilisateur clique sur « Chronologie » depuis le rail
    # des sections → le dialogue hôte doit ouvrir son onglet chronologie.
    timeline_requested = Signal()
    # Signal émis après toute mutation d'une entrée (section ou timeline) → le
    # dialogue hôte peut réagir en temps réel (ex : marquer le dossier modifié).
    entries_changed = Signal()

    def __init__(self, student_id: int = 0, parent=None):
        super().__init__(parent)
        self._sid = student_id
        self._pages: list[_Page] = []
        self._current_key = SECTIONS[0][0]
        self._build()
        ds.theme_changed.connect(self._restyle)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ds.space_xs)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(ds.space_xs)
        # ── Bouton Chronologie : navigation vers l'ONGLET du dialogue hôte ──
        self._tl_btn = M3Button(_("dossier.timeline.title"))
        self._tl_btn.setCursor(Qt.PointingHandCursor)
        self._tl_btn.clicked.connect(self.timeline_requested.emit)
        btn_row.addWidget(self._tl_btn)
        self._btns: list[M3Button] = []
        self._stack_info: list[tuple] = []
        for key, label in SECTIONS:
            btn = M3Button(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._select(k))
            btn_row.addWidget(btn)
            self._btns.append(btn)
            self._stack_info.append((key, label))
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self._stack = M3StackedWidget()
        # La chronologie n'est PLUS dans le stack interne : elle est exposée via
        # `self.timeline` pour être ajoutée comme onglet du dialogue hôte.
        self._timeline = _TimelinePage()
        self._timeline.set_on_edit(self.edit_from_timeline)
        for key, label in self._stack_info:
            self._stack.addWidget(_Page(key, self._sid))
            self._pages.append(self._stack.widget(self._stack.count() - 1))
        for page in self._pages:
            page.entries_changed.connect(self._on_entries_changed)
        layout.addWidget(self._stack, 1)
        self._select(self._current_key)

    @safe_slot("DossierPanel._on_entries_changed")
    def _on_entries_changed(self):
        """Mutation d'une entrée dans une section → synchronise la chronologie
        immédiatement (temps réel) puis relaie le signal vers le dialogue hôte."""
        self.refresh_timeline()
        self.entries_changed.emit()

    def _select(self, key: str):
        self._current_key = key
        for i, (k, _label) in enumerate(self._stack_info):
            if k == key:
                self._stack.setCurrentIndex(i)
        self._restyle()

    # ── API publique (utilisée par le dialogue hôte pour la chronologie) ──

    @property
    def timeline(self) -> _TimelinePage:
        """Vue chronologique globale — onglet complet du StudentEditDialog."""
        return self._timeline

    def refresh_timeline(self):
        """Recharge la chronologie depuis l'état courant des sections."""
        self._timeline.refresh(self._pages)

    def edit_from_timeline(self, entry: dict):
        """Édite une entrée depuis la chronologie : bascule sur la section puis ouvre le dialogue."""
        sec = entry.get("_section_key", "")
        page = next(
            (p for (k, _), p in zip(self._stack_info, self._pages) if k == sec),
            None,
        )
        if page is None:
            return
        self._select(sec)
        page.edit_entry(entry)
        self.refresh_timeline()

    @safe_slot("DossierPanel._restyle")
    def _restyle(self):
        p = ds.p
        btn_base = (
            f"M3Button {{ border: none; border-radius: {ds.radius_lg}px; "
            f"padding: {ds.space_xs}px {ds.space_md}px; font-size: {ds.font_px_md}px; font-weight: bold; }}"
        )
        # Bouton « Chronologie » : tonal (distinct des sections) car il navigue
        # vers l'onglet du dialogue, il n'a pas d'état actif interne.
        # Paire M3 : secondary_container + text_strong (comme les badges) —
        # `on_secondary_container` n'existe que dans _LarcM3Colors (phibuilder),
        # pas dans la Palette de base.
        self._tl_btn.setStyleSheet(
            btn_base
            + f"M3Button {{ background: {p.secondary_container}; color: {p.text_strong}; }}"
            + f"M3Button:hover {{ background: {p.secondary}; color: {p.on_secondary}; }}"
        )
        for i, (k, _label) in enumerate(self._stack_info):
            if k == self._current_key:
                self._btns[i].setStyleSheet(btn_base + f"M3Button {{ background: {p.primary}; color: {p.on_primary}; }}")
            else:
                self._btns[i].setStyleSheet(
                    btn_base + f"M3Button {{ background: transparent; color: {p.text_strong}; }}" + f"M3Button:hover {{ background: {p.surface_variant}; }}"
                )

    def set_directory(self, base_dir: str):
        for page in self._pages:
            page.set_directory(base_dir)

    # ── Fiche santé (routée vers la section Médical) ──

    def set_health(self, data: dict):
        for (key, _label), page in zip(self._stack_info, self._pages):
            if key == "medicale":
                page.set_health(data)

    def get_health(self) -> dict:
        for (key, _label), page in zip(self._stack_info, self._pages):
            if key == "medicale":
                return page.get_health()
        return {}

    def set_data(self, data: dict):
        for (key, _label), page in zip(self._stack_info, self._pages):
            page.load_entries(data.get(key, {}).get("entries", []))
        self.refresh_timeline()

    def get_data(self) -> dict:
        result = {}
        for (key, _label), page in zip(self._stack_info, self._pages):
            result[key] = {"intro": "", "entries": page.get_entries()}
        return result

    def clear(self):
        for page in self._pages:
            page.load_entries([])
        self.refresh_timeline()
