"""EventGenerator adapté pour le personnel (staff_event).

Réutilise les types d'événements de larcauth_type_event.
Écrit dans la table staff_event (pas student_event).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QDateTimeEdit,
)
from PySide6.QtCore import QDateTime

from larccommon.database import db
from larccommon.session import session
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


def open_staff_event_generator(staff_data: dict, parent=None):
    """Ouvre le dialogue d'ajout d'événement pour un membre du personnel."""
    dlg = StaffEventDialog(staff_data, parent)
    dlg.exec()


class StaffEventDialog(QDialog):
    """Dialogue d'ajout d'événement (absence, retard, sortie) pour le personnel."""

    MODES = [
        ("Absence", "Ab"),
        ("Retard", "Re"),
        ("Événement", "Ev"),
    ]

    def __init__(self, staff_data: dict, parent=None):
        super().__init__(parent)
        self._staff = staff_data
        self._selected_type: str | None = None

        name = staff_data.get("full_name", staff_data.get("last_name", ""))
        self.setWindowTitle(f"Événement — {name}")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"background: {theme_manager.palette.surface};")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # En-tête
        header = QLabel(f"Événement pour {self._staff.get('full_name', '—')}")
        header.setStyleSheet(f"""
            font-size: {theme_manager.font_size(16)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
        """)
        layout.addWidget(header)

        # Breadcrumb / sélecteur de mode
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(ds.space_xs)

        for label, prefix in self.MODES:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(ds.button_height)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {theme_manager.palette.surface_variant};
                    color: {theme_manager.palette.text_strong};
                    border: 1px solid {theme_manager.palette.outline};
                    border-radius: {ds.radius_sm}px;
                    padding: {ds.space_xs}px {ds.space_md}px;
                    font-size: {theme_manager.font_size(13)}px;
                }}
                QPushButton:checked {{
                    background: {theme_manager.palette.primary};
                    color: white; border-color: {theme_manager.palette.primary};
                }}
                QPushButton:hover {{ border-color: {theme_manager.palette.primary}; }}
            """)
            btn.clicked.connect(lambda checked, p=prefix: self._select_mode(p))
            mode_layout.addWidget(btn)
            self.__dict__[f"_btn_{prefix}"] = btn

        layout.addLayout(mode_layout)

        # Type d'événement
        self._type_combo = QComboBox()
        self._type_combo.setFixedHeight(ds.field_height)
        self._type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {theme_manager.palette.background};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_xs}px;
                padding: {ds.space_sm}px; color: {theme_manager.palette.text_strong};
                font-size: {theme_manager.font_size(13)}px;
            }}
        """)
        self._type_combo.setVisible(False)
        layout.addWidget(self._type_combo)

        # Date/Heure
        self._date_edit = QDateTimeEdit()
        self._date_edit.setDateTime(QDateTime.currentDateTime())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setFixedHeight(ds.field_height)
        self._date_edit.setStyleSheet(f"""
            QDateTimeEdit {{
                background: {theme_manager.palette.background};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_xs}px;
                padding: {ds.space_sm}px; color: {theme_manager.palette.text_strong};
                font-size: {theme_manager.font_size(13)}px;
            }}
        """)
        layout.addWidget(QLabel("Date / Heure :"))
        layout.addWidget(self._date_edit)

        # Note
        layout.addWidget(QLabel("Note :"))
        self._note = QTextEdit()
        self._note.setFixedHeight(100)
        self._note.setStyleSheet(f"""
            QTextEdit {{
                background: {theme_manager.palette.background};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_xs}px;
                padding: {ds.space_sm}px; color: {theme_manager.palette.text_strong};
                font-size: {theme_manager.font_size(13)}px;
            }}
        """)
        layout.addWidget(self._note)

        layout.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel = QPushButton("Annuler")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(ds.button_height)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {theme_manager.palette.text_strong};
                border: 1px solid {theme_manager.palette.outline};
                border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
            }}
            QPushButton:hover {{ background: {theme_manager.palette.surface_variant}; }}
        """)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Enregistrer")
        save.setCursor(Qt.PointingHandCursor)
        save.setFixedHeight(ds.button_height)
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

    def _select_mode(self, prefix: str):
        self._selected_type = prefix
        self._type_combo.clear()
        self._type_combo.setVisible(True)

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()
            if prefix == "Ab":
                cur.execute("""
                    SELECT idtypeevent, type_event FROM larcauth_type_event
                    WHERE type_event ILIKE 'Absence%%' AND enabled = true AND fk_language = 2
                    ORDER BY idtypeevent
                """)
            elif prefix == "Re":
                cur.execute("""
                    SELECT idtypeevent, type_event FROM larcauth_type_event
                    WHERE type_event ILIKE 'Retard%%' AND enabled = true AND fk_language = 2
                    ORDER BY idtypeevent
                """)
            else:
                cur.execute("""
                    SELECT idtypeevent, type_event FROM larcauth_type_event
                    WHERE type_event NOT ILIKE 'Absence%%' AND type_event NOT ILIKE 'Retard%%'
                    AND enabled = true AND fk_language = 2
                    ORDER BY idtypeevent
                """)

            for type_id, type_label in cur.fetchall():
                self._type_combo.addItem(type_label, type_id)

        except Exception:
            pass

    @safe_slot("StaffEventDialog._on_save")
    def _on_save(self):
        conn = db.server_conn
        if not conn:
            return

        event_type = self._type_combo.currentText()
        if not event_type:
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO staff_event (staff_id, event_type, event_at, note, source, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self._staff["id"],
                event_type,
                self._date_edit.dateTime().toPython(),
                self._note.toPlainText().strip(),
                "RH",
                session.user_id,
            ))
            self.accept()

        except Exception as e:
            import traceback
            traceback.print_exc()
