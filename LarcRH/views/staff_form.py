"""StaffFormDialog — édition/création d'un membre du personnel."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QDateEdit, QComboBox, QWidget,
)
from PySide6.QtCore import QDate

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


class StaffFormDialog(QDialog):
    """Dialogue d'édition d'un membre du personnel."""

    def __init__(self, id_lo: int, id_hi: int,
                 staff_data: dict | None = None, parent=None):
        super().__init__(parent)
        self._id_lo = id_lo
        self._id_hi = id_hi
        self._staff_data = staff_data
        self._is_new = staff_data is None

        self.setWindowTitle("Ajouter un membre" if self._is_new else "Modifier le membre")
        self.setMinimumSize(450, 400)
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

        # Rôles
        roles_widget = QWidget()
        roles_layout = QHBoxLayout(roles_widget)
        roles_layout.setContentsMargins(0, 0, 0, 0)

        self._cb_teacher = QCheckBox("Enseignant")
        self._cb_coord = QCheckBox("Coordinateur")
        self._cb_secr = QCheckBox("Secrétaire")
        self._cb_adm = QCheckBox("Admin")

        for cb in [self._cb_teacher, self._cb_coord, self._cb_secr, self._cb_adm]:
            cb.setStyleSheet(f"color: {theme_manager.palette.text_strong}; font-size: {theme_manager.font_size(12)}px;")
            roles_layout.addWidget(cb)

        layout.addWidget(roles_widget)

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
        self._cb_teacher.setChecked(d.get("is_teacher", False))
        self._cb_coord.setChecked(d.get("is_coordonator", False))
        self._cb_secr.setChecked(d.get("is_secretary", False))
        self._cb_adm.setChecked(d.get("is_adm", False))

    @safe_slot("StaffFormDialog._on_save")
    def _on_save(self):
        first = self._f_first.text().strip()
        last = self._f_last.text().strip()
        email = self._f_email.text().strip()
        phone = self._f_phone.text().strip()

        if not last or not first:
            return

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()

            if self._is_new:
                # Trouver un slot libre dans la plage d'IDs
                cur.execute("""
                    SELECT id FROM larcauth_aecuser
                    WHERE id BETWEEN %s AND %s AND is_active = FALSE
                    AND (last_name LIKE 'Name of %%' OR last_name IS NULL OR last_name = '')
                    ORDER BY id LIMIT 1
                """, (self._id_lo, self._id_hi))
                row = cur.fetchone()
                if not row:
                    # Créer un nouvel AECUser si aucun slot libre
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
                        email = %s, is_active = TRUE
                        WHERE id = %s
                    """, (first, last, email, new_id))

                self._new_id = new_id
            else:
                new_id = self._staff_data["id"]
                cur.execute("""
                    UPDATE larcauth_aecuser SET first_name = %s, last_name = %s,
                    email = %s WHERE id = %s
                """, (first, last, email, new_id))

            # Mise à jour teachadm ou staff
            if self._staff_data and self._staff_data.get("is_staff"):
                cur.execute("""
                    INSERT INTO larcauth_staff (aecuser_ptr_id, enabled, hire_date)
                    VALUES (%s, TRUE, %s)
                    ON CONFLICT (aecuser_ptr_id) DO UPDATE SET enabled = TRUE, hire_date = %s
                """, (new_id, self._f_hire.date().toPython(), self._f_hire.date().toPython()))
            else:
                cur.execute("""
                    INSERT INTO larcauth_teachadm (aecuser_ptr_id, is_teacher, is_coordonator,
                    is_secretary, is_adm, enabled)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (aecuser_ptr_id) DO UPDATE SET
                    is_teacher = %s, is_coordonator = %s, is_secretary = %s, is_adm = %s, enabled = TRUE
                """, (new_id, self._cb_teacher.isChecked(), self._cb_coord.isChecked(),
                      self._cb_secr.isChecked(), self._cb_adm.isChecked(),
                      self._cb_teacher.isChecked(), self._cb_coord.isChecked(),
                      self._cb_secr.isChecked(), self._cb_adm.isChecked()))

            self.accept()

        except Exception as e:
            import traceback
            traceback.print_exc()
