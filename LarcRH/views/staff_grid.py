"""StaffGrid — grille photos enseignants/staff avec filtrage par plage d'IDs."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QSizePolicy,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot


def _make_avatar(name: str, size: int = 100) -> QPixmap:
    """Génère un avatar avec initiales sur fond coloré."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    # Fond
    hue = (hash(name) % 360 + 360) % 360
    p.setBrush(QColor.fromHsl(hue, 160, 120))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, size, size, size // 4, size // 4)
    # Initiales
    initials = "".join(part[0].upper() for part in name.split()[:2]) or "?"
    p.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", size // 3, QFont.Bold)
    p.setFont(font)
    p.drawText(0, 0, size, size, Qt.AlignCenter, initials)
    p.end()
    return pix


class _StaffCard(QFrame):
    """Carte photo d'un membre du personnel."""

    clicked_event = None

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._data = data
        self.setObjectName("staff_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(200, 240)
        self.setStyleSheet(self._style())
        self._setup_ui()
        ds.theme_changed.connect(self._restyle)

    def _style(self) -> str:
        p = theme_manager.palette
        return f"""
            #staff_card {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: {ds.radius_md}px;
            }}
            #staff_card:hover {{ border-color: {p.primary}; }}
        """

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
        layout.setSpacing(ds.space_xs)

        # Photo
        photo_id = self._data.get("id", 0)
        photo_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..",
                         "LarcSuperviseur", "photos", f"{photo_id}.png"))
        photo_lbl = QLabel()
        photo_lbl.setFixedSize(80, 80)
        photo_lbl.setAlignment(Qt.AlignCenter)

        pix = None
        if os.path.exists(photo_path):
            pix = QPixmap(photo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if pix is None or pix.isNull():
            pix = _make_avatar(self._data.get("full_name", ""), 80)
        # Crop to circle with QSS mask
        photo_lbl.setPixmap(pix)
        photo_lbl.setStyleSheet(f"""
            QLabel {{ border-radius: 40px; background: transparent; }}
        """)
        layout.addWidget(photo_lbl, 0, Qt.AlignCenter)

        # Nom
        name = QLabel(self._data.get("full_name", "—"))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet(f"""
            font-size: {theme_manager.font_size(12)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong}; border: none;
        """)
        layout.addWidget(name)

        # Email
        email = QLabel(self._data.get("email", ""))
        email.setAlignment(Qt.AlignCenter)
        email.setStyleSheet(f"""
            font-size: {theme_manager.font_size(10)}px;
            color: {theme_manager.palette.text_soft}; border: none;
        """)
        layout.addWidget(email)

        # Rôles
        roles = []
        if self._data.get("is_adm"):
            roles.append("Admin")
        if self._data.get("is_coordonator"):
            roles.append("Coord")
        if self._data.get("is_secretary"):
            roles.append("Secr")
        if self._data.get("is_teacher") is not False:  # peut être None pour staff
            if self._data.get("is_teacher"):
                roles.append("Ens.")
        role_text = " · ".join(roles) if roles else ""
        role_lbl = QLabel(role_text)
        role_lbl.setAlignment(Qt.AlignCenter)
        role_lbl.setStyleSheet(f"""
            font-size: {theme_manager.font_size(10)}px;
            color: {theme_manager.palette.primary}; border: none;
        """)
        layout.addWidget(role_lbl)

        layout.addStretch()

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(ds.space_xs)

        event_btn = QPushButton()
        event_btn.setIcon(md3_icon("event", color=theme_manager.palette.primary, size=16))
        event_btn.setFixedSize(ds.space_lg, ds.space_lg)
        event_btn.setCursor(Qt.PointingHandCursor)
        event_btn.setToolTip("Événements (absences, retards...)")
        event_btn.clicked.connect(lambda: self._on_event())
        event_btn.setStyleSheet(f"""
            QPushButton {{ border: 1px solid {theme_manager.palette.outline}; border-radius: {ds.radius_xs}px; background: transparent; }}
            QPushButton:hover {{ background: {theme_manager.palette.surface_variant}; }}
        """)
        btn_row.addWidget(event_btn)

        edit_btn = QPushButton()
        edit_btn.setIcon(md3_icon("edit", color=theme_manager.palette.primary, size=16))
        edit_btn.setFixedSize(ds.space_lg, ds.space_lg)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setToolTip("Modifier")
        edit_btn.clicked.connect(lambda: self._on_edit())
        edit_btn.setStyleSheet(f"""
            QPushButton {{ border: 1px solid {theme_manager.palette.outline}; border-radius: {ds.radius_xs}px; background: transparent; }}
            QPushButton:hover {{ background: {theme_manager.palette.surface_variant}; }}
        """)
        btn_row.addWidget(edit_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_event(self):
        from LarcRH.views.staff_events import open_staff_event_generator
        open_staff_event_generator(self._data, self)

    def _on_edit(self):
        from LarcRH.views.staff_form import StaffFormDialog
        cat_lo = (self._data["id"] // 1000) * 1000 + 1
        cat_hi = ((self._data["id"] // 1000) + 1) * 1000
        dlg = StaffFormDialog(cat_lo, cat_hi, staff_data=self._data, parent=self)
        if dlg.exec():
            parent_grid = self._find_grid()
            if parent_grid:
                parent_grid.refresh()

    def _find_grid(self):
        w = self.parent()
        while w:
            if hasattr(w, 'refresh') and isinstance(w, StaffGrid):
                return w
            w = w.parent()
        return None

    @safe_slot("_StaffCard._restyle")
    def _restyle(self):
        self.setStyleSheet(self._style())


class StaffGrid(QScrollArea):
    """Grille de photos filtrable par plage d'IDs."""

    def __init__(self, cat_key: str, id_lo: int, id_hi: int,
                 is_staff: bool = False, parent=None):
        super().__init__(parent)
        self._cat_key = cat_key
        self._id_lo = id_lo
        self._id_hi = id_hi
        self._is_staff = is_staff

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")

        container = QWidget()
        self._layout = QGridLayout(container)
        self._layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        self._layout.setSpacing(ds.space_sm)
        self.setWidget(container)

        self.refresh()

    def refresh(self):
        self._load_data()

    def _load_data(self):
        # Nettoyer la grille
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = db.server_conn
        if not conn:
            lbl = QLabel("Base de données non disponible")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {theme_manager.palette.error}; font-size: {theme_manager.font_size(13)}px;")
            self._layout.addWidget(lbl, 0, 0)
            return

        try:
            cur = conn.cursor()
            if self._is_staff:
                cur.execute("""
                    SELECT a.id, a.first_name, a.last_name, a.email,
                           FALSE, FALSE, FALSE, FALSE
                    FROM larcauth_aecuser a
                    JOIN larcauth_staff s ON s.aecuser_ptr_id = a.id
                    WHERE a.id BETWEEN %s AND %s AND s.enabled = true
                    ORDER BY a.last_name, a.first_name
                """, (self._id_lo, self._id_hi))
            else:
                cur.execute("""
                    SELECT a.id, a.first_name, a.last_name, a.email,
                           t.is_teacher, t.is_coordonator, t.is_secretary, t.is_adm
                    FROM larcauth_aecuser a
                    JOIN larcauth_teachadm t ON t.aecuser_ptr_id = a.id
                    WHERE a.id BETWEEN %s AND %s AND t.enabled = true
                    ORDER BY a.last_name, a.first_name
                """, (self._id_lo, self._id_hi))

            rows = cur.fetchall()
            cols = max(1, (self.width() - ds.space_md * 2) // (200 + ds.space_sm))

            if not rows:
                lbl = QLabel("Aucun membre trouvé dans cette catégorie")
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"color: {theme_manager.palette.text_soft}; font-size: {theme_manager.font_size(13)}px;")
                self._layout.addWidget(lbl, 0, 0)
                return

            for i, row in enumerate(rows):
                data = {
                    "id": row[0],
                    "full_name": f"{row[2]} {row[1]}",  # last_name + first_name
                    "first_name": row[1],
                    "last_name": row[2],
                    "email": row[3],
                    "is_teacher": row[4],
                    "is_coordonator": row[5],
                    "is_secretary": row[6],
                    "is_adm": row[7],
                    "is_staff": self._is_staff,
                }
                card = _StaffCard(data)
                self._layout.addWidget(card, i // cols, i % cols)

        except Exception as e:
            lbl = QLabel(f"Erreur : {e}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {theme_manager.palette.error}; font-size: {theme_manager.font_size(11)}px;")
            self._layout.addWidget(lbl, 0, 0)
