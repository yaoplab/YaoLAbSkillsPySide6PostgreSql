"""StaffFormDialog — édition/création d'un membre du personnel."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QDateEdit, QComboBox, QWidget, QGridLayout,
)
from PySide6.QtCore import QDate

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot

# Labels pour les colonnes métier staff (4 rôles non enseignant)
STAFF_ROLES = [
    ('type_DRH', 'DRH'),
    ('type_Comptable', 'Comptable'),
    ('type_ressources_Humaines', 'Ress. Humaines'),
    ('type_Bulletin_Releves', 'Bulletins / Relevés'),
]

TEACHADM_ROLES = [
    ('is_teacher', 'Enseignant'),
    ('is_coordonator', 'Coordinateur'),
    ('is_adm', 'Admin'),
]


class StaffFormDialog(QDialog):
    """Dialogue d'édition d'un membre du personnel."""

    def __init__(self, id_lo: int, id_hi: int,
                 staff_data: dict | None = None, parent=None):
        super().__init__(parent)
        self._id_lo = id_lo
        self._id_hi = id_hi
        self._staff_data = staff_data
        self._is_new = staff_data is None
        # Déterminer si staff (4001+) ou teachadm (1001-4000)
        self._is_staff = (staff_data.get("is_staff") if staff_data else id_lo >= 4001)
        self._checkboxes: dict[str, QCheckBox] = {}

        self.setWindowTitle("Ajouter un membre" if self._is_new else "Modifier le membre")
        self.setMinimumSize(500, 420 if self._is_staff else 350)
        self.setStyleSheet(f"background: {theme_manager.palette.surface};")
        self._setup_ui()

        if not self._is_new:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        form = QFormLayout()
        form.setSpacing(ds.space_sm)

        fstyle = f"""
            QLineEdit {{
                background: {theme_manager.palette.background};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_xs}px;
                padding: {ds.space_sm}px; color: {theme_manager.palette.text_strong};
                font-size: {theme_manager.font_size(13)}px;
            }}
            QLineEdit:focus {{ border-color: {theme_manager.palette.primary}; }}
        """

        self._f_first = QLineEdit()
        self._f_first.setPlaceholderText("Prénom")
        self._f_first.setFixedHeight(ds.field_height)
        self._f_first.setStyleSheet(fstyle)
        form.addRow("Prénom :", self._f_first)

        self._f_last = QLineEdit()
        self._f_last.setPlaceholderText("Nom")
        self._f_last.setFixedHeight(ds.field_height)
        self._f_last.setStyleSheet(fstyle)
        form.addRow("Nom :", self._f_last)

        self._f_email = QLineEdit()
        self._f_email.setPlaceholderText("email@arc-en-ciel.org")
        self._f_email.setFixedHeight(ds.field_height)
        self._f_email.setStyleSheet(fstyle)
        form.addRow("Email :", self._f_email)

        self._f_phone = QLineEdit()
        self._f_phone.setPlaceholderText("Téléphone")
        self._f_phone.setFixedHeight(ds.field_height)
        self._f_phone.setStyleSheet(fstyle)
        form.addRow("Téléphone :", self._f_phone)

        self._f_hire = QDateEdit()
        self._f_hire.setCalendarPopup(True)
        self._f_hire.setDate(QDate.currentDate())
        self._f_hire.setFixedHeight(ds.field_height)
        self._f_hire.setStyleSheet(fstyle)
        form.addRow("Date d'embauche :", self._f_hire)

        layout.addLayout(form)

        # Rôles — dynamique selon staff vs teachadm
        cb_style = f"color: {theme_manager.palette.text_strong}; font-size: {theme_manager.font_size(12)}px;"
        role_set = STAFF_ROLES if self._is_staff else TEACHADM_ROLES

        role_label = QLabel("Postes / Rôles :")
        role_label.setStyleSheet(f"font-weight: bold; color: {theme_manager.palette.text_strong};")
        layout.addWidget(role_label)

        grid = QGridLayout()
        grid.setSpacing(ds.space_xs)
        cols = 3
        for i, (key, label) in enumerate(role_set):
            cb = QCheckBox(label)
            cb.setStyleSheet(cb_style)
            grid.addWidget(cb, i // cols, i % cols)
            self._checkboxes[key] = cb
        layout.addLayout(grid)

        layout.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel = QPushButton("Annuler")
        cancel.setFixedHeight(ds.button_height)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {theme_manager.palette.text_strong};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
                font-size: {theme_manager.font_size(13)}px;
            }}
            QPushButton:hover {{ background: {theme_manager.palette.surface_variant}; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Enregistrer")
        save.setFixedHeight(ds.button_height)
        save.setCursor(Qt.PointingHandCursor)
        save.setStyleSheet(f"""
            QPushButton {{
                background: {theme_manager.palette.primary}; color: white;
                border: none; border-radius: {ds.radius_sm}px;
                padding: {ds.space_xs}px {ds.space_md}px;
                font-size: {theme_manager.font_size(13)}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {theme_manager.palette.primary}; }}
        """)
        save.clicked.connect(self._on_save)
        btn_layout.addWidget(save)

        layout.addLayout(btn_layout)

    def _load_data(self):
        d = self._staff_data
        self._f_first.setText(d.get("first_name", ""))
        self._f_last.setText(d.get("last_name", ""))
        self._f_email.setText(d.get("email", ""))
        # Cocher les cases correspondantes
        for key, cb in self._checkboxes.items():
            cb.setChecked(d.get(key, False))

    @safe_slot("StaffFormDialog._on_save")
    def _on_save(self):
        first = self._f_first.text().strip()
        last = self._f_last.text().strip()
        email = self._f_email.text().strip()

        if not last or not first:
            return

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()

            if self._is_new:
                cur.execute("""
                    SELECT id FROM larcauth_aecuser
                    WHERE id BETWEEN %s AND %s AND is_active = FALSE
                    AND (last_name LIKE 'Name of %%' OR last_name IS NULL OR last_name = '')
                    ORDER BY id LIMIT 1
                """, (self._id_lo, self._id_hi))
                row = cur.fetchone()
                if not row:
                    cur.execute("SELECT COALESCE(MAX(id), %s) + 1 FROM larcauth_aecuser WHERE id BETWEEN %s AND %s",
                                (self._id_lo - 1, self._id_lo, self._id_hi))
                    new_id = cur.fetchone()[0]
                    if new_id > self._id_hi:
                        raise ValueError("Plus de slots disponibles dans cette catégorie")
                    cur.execute("""
                        INSERT INTO larcauth_aecuser (id, first_name, last_name, email, is_active, password)
                        VALUES (%s, %s, %s, %s, TRUE, '')
                    """, (new_id, first, last, email))
                else:
                    new_id = row[0]
                    cur.execute("""
                        UPDATE larcauth_aecuser SET first_name = %s, last_name = %s,
                        email = %s, is_active = TRUE WHERE id = %s
                    """, (first, last, email, new_id))
                self._new_id = new_id
            else:
                new_id = self._staff_data["id"]
                cur.execute("""
                    UPDATE larcauth_aecuser SET first_name = %s, last_name = %s,
                    email = %s WHERE id = %s
                """, (first, last, email, new_id))

            # INSERT/UPDATE la table de liaison (staff ou teachadm)
            hire_date = self._f_hire.date().toPython()
            if self._is_staff:
                cols = ", ".join(f"{k} = %s" for k, _ in STAFF_ROLES)
                vals = [self._checkboxes[k].isChecked() if k in self._checkboxes else False for k, _ in STAFF_ROLES]
                cur.execute(f"""
                    INSERT INTO larcauth_staff (aecuser_ptr_id, enabled, hire_date, {', '.join(k for k, _ in STAFF_ROLES)})
                    VALUES (%s, TRUE, %s, {', '.join('%s' for _ in STAFF_ROLES)})
                    ON CONFLICT (aecuser_ptr_id) DO UPDATE SET enabled = TRUE, hire_date = %s, {cols}
                """, [new_id, hire_date] + vals + [hire_date] + vals)
            else:
                cols = ", ".join(f"{k} = %s" for k, _ in TEACHADM_ROLES)
                vals = [self._checkboxes[k].isChecked() if k in self._checkboxes else False for k, _ in TEACHADM_ROLES]
                cur.execute(f"""
                    INSERT INTO larcauth_teachadm (aecuser_ptr_id, enabled, {', '.join(k for k, _ in TEACHADM_ROLES)})
                    VALUES (%s, TRUE, {', '.join('%s' for _ in TEACHADM_ROLES)})
                    ON CONFLICT (aecuser_ptr_id) DO UPDATE SET enabled = TRUE, {cols}
                """, [new_id] + vals + vals)

            self.accept()

        except Exception:
            import traceback
            traceback.print_exc()
