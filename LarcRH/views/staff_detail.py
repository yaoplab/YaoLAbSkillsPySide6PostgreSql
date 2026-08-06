"""StaffDetail — panneau détail enseignant/staff avec timeline événements."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot


class StaffDetail(QWidget):
    """Panneau de détail d'un membre du personnel avec événements."""

    def __init__(self, staff_data: dict, on_back=None, parent=None):
        super().__init__(parent)
        self._staff = staff_data
        self._on_back = on_back

        self._setup_ui()
        self._load_events()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # Bouton retour
        if self._on_back:
            back = QPushButton("← Retour")
            back.setCursor(Qt.PointingHandCursor)
            back.setFlat(True)
            back.setStyleSheet(f"""
                QPushButton {{ color: {theme_manager.palette.primary}; font-size: {theme_manager.font_size(13)}px; }}
                QPushButton:hover {{ text-decoration: underline; }}
            """)
            back.clicked.connect(self._on_back)
            layout.addWidget(back)

        # Photo + Infos
        top_row = QHBoxLayout()
        top_row.setSpacing(ds.space_md)

        # Photo
        photo_id = self._staff.get("id", 0)
        photo_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..",
                         "LarcSuperviseur", "photos", f"{photo_id}.png"))
        photo = QLabel()
        photo.setFixedSize(120, 120)
        photo.setAlignment(Qt.AlignCenter)
        pix = QPixmap(photo_path) if os.path.exists(photo_path) else None
        if pix is None or pix.isNull():
            from LarcRH.views.staff_grid import _make_avatar
            pix = _make_avatar(self._staff.get("full_name", ""), 120)
        else:
            pix = pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        photo.setPixmap(pix)
        photo.setStyleSheet("border-radius: 60px;")
        top_row.addWidget(photo)

        # Infos
        info = QVBoxLayout()
        info.setSpacing(ds.space_xs)

        name_lbl = QLabel(self._staff.get("full_name", "—"))
        name_lbl.setStyleSheet(f"""
            font-size: {theme_manager.font_size(18)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
        """)
        info.addWidget(name_lbl)

        email_lbl = QLabel(self._staff.get("email", ""))
        email_lbl.setStyleSheet(f"font-size: {theme_manager.font_size(13)}px; color: {theme_manager.palette.text_soft};")
        info.addWidget(email_lbl)

        # Rôles
        roles = []
        if self._staff.get("is_adm"): roles.append("Administrateur")
        if self._staff.get("is_coordonator"): roles.append("Coordinateur")
        if self._staff.get("is_secretary"): roles.append("Secrétaire")
        if self._staff.get("is_teacher"): roles.append("Enseignant")
        role_text = " · ".join(roles) if roles else "Staff non enseignant"
        role_lbl = QLabel(role_text)
        role_lbl.setStyleSheet(f"""
            font-size: {theme_manager.font_size(12)}px;
            color: {theme_manager.palette.primary}; font-weight: bold;
        """)
        info.addWidget(role_lbl)

        info.addStretch()
        top_row.addLayout(info, 1)

        layout.addLayout(top_row)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {theme_manager.palette.outline_variant};")
        layout.addWidget(sep)

        # Titre événements
        evt_header = QHBoxLayout()
        evt_title = QLabel("Événements")
        evt_title.setStyleSheet(f"""
            font-size: {theme_manager.font_size(16)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
        """)
        evt_header.addWidget(evt_title)
        evt_header.addStretch()

        add_evt = QPushButton("+ Ajouter")
        add_evt.setCursor(Qt.PointingHandCursor)
        add_evt.setStyleSheet(f"""
            QPushButton {{
                background: {theme_manager.palette.primary}; color: white;
                border: none; border-radius: {ds.radius_sm}px;
                padding: {ds.space_xs}px {ds.space_md}px;
                font-size: {theme_manager.font_size(12)}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {theme_manager.palette.primary}; }}
        """)
        add_evt.clicked.connect(self._add_event)
        evt_header.addWidget(add_evt)
        layout.addLayout(evt_header)

        # Timeline scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self._event_container = QWidget()
        self._event_layout = QVBoxLayout(self._event_container)
        self._event_layout.setContentsMargins(0, 0, 0, 0)
        self._event_layout.setSpacing(ds.space_xs)
        self._event_layout.addStretch()
        scroll.setWidget(self._event_container)
        layout.addWidget(scroll, 1)

    def _load_events(self):
        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT event_type, event_at, note, source, validated_by
                FROM staff_event WHERE staff_id = %s
                ORDER BY event_at DESC LIMIT 50
            """, (self._staff["id"],))
            rows = cur.fetchall()

            if not rows:
                empty = QLabel("Aucun événement enregistré")
                empty.setStyleSheet(f"color: {theme_manager.palette.text_soft}; font-size: {theme_manager.font_size(12)}px;")
                self._event_layout.insertWidget(0, empty)
                return

            for row in rows:
                evt_type, evt_at, note, source, validated = row
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {theme_manager.palette.surface};
                        border: 1px solid {theme_manager.palette.outline_variant};
                        border-radius: {ds.radius_sm}px;
                    }}
                """)
                cl = QVBoxLayout(card)
                cl.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
                cl.setSpacing(ds.space_xxs)

                top = QHBoxLayout()
                tlabel = QLabel(evt_type or "—")
                tlabel.setStyleSheet(f"font-weight: bold; color: {theme_manager.palette.primary}; font-size: {theme_manager.font_size(12)}px;")
                top.addWidget(tlabel)
                top.addStretch()
                if validated:
                    val = QLabel("✓ Validé")
                    val.setStyleSheet(f"color: {theme_manager.palette.success}; font-size: {theme_manager.font_size(10)}px;")
                    top.addWidget(val)
                cl.addLayout(top)

                date_lbl = QLabel(str(evt_at)[:16] if evt_at else "")
                date_lbl.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {theme_manager.palette.text_soft};")
                cl.addWidget(date_lbl)

                if note:
                    n = QLabel(note[:200])
                    n.setWordWrap(True)
                    n.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {theme_manager.palette.text_strong};")
                    cl.addWidget(n)

                pos = self._event_layout.count() - 1  # avant le stretch
                self._event_layout.insertWidget(max(0, pos), card)

        except Exception:
            pass

    def _add_event(self):
        from LarcRH.views.staff_events import StaffEventDialog
        dlg = StaffEventDialog(self._staff, self)
        if dlg.exec():
            # Recharger les événements
            while self._event_layout.count():
                item = self._event_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._event_layout.addStretch()
            self._load_events()
