"""StaffGrid — grille photos responsive (largeur adaptative)."""
from __future__ import annotations

import math
import os

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QSizePolicy,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot

# Dimensions Fibonacci : 136×220 = ratio d'or (220/136 ≈ 1.618 = φ)
CARD_W = ds.space_xxxl  # 136
CARD_H = 220             # Fibonacci F(11) — golden pair avec 136


def _make_avatar(name: str, size: int = 100) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    hue = (hash(name) % 360 + 360) % 360
    p.setBrush(QColor.fromHsl(hue, 160, 120))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, size, size, size // 4, size // 4)
    initials = "".join(part[0].upper() for part in name.split()[:2]) or "?"
    p.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", size // 3, QFont.Bold)
    p.setFont(font)
    p.drawText(0, 0, size, size, Qt.AlignCenter, initials)
    p.end()
    return pix


class _StaffCard(QFrame):
    """Carte photo d'un membre du personnel."""

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._data = data
        self.setObjectName("staff_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(CARD_W, CARD_H)
        self.setStyleSheet(self._style())
        self._setup_ui()
        ds.theme_changed.connect(self._restyle)

    def _style(self) -> str:
        p = theme_manager.palette
        s = theme_manager.font_size
        return f"""
            #staff_card {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: {ds.radius_sm}px;
            }}
            #staff_card:hover {{ border-color: {p.primary}; }}
        """

    def _setup_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_xs, ds.space_xs, ds.space_xs, ds.space_xs)  # 8px = F6, comme student card
        layout.setSpacing(ds.space_xs)

        # Photo
        photo_id = self._data.get("id", 0)
        photo_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..",
                         "LarcSuperviseur", "photos", f"{photo_id}.png"))
        photo_lbl = QLabel()
        photo_lbl.setFixedSize(ds.space_xxl, ds.space_xxl)
        photo_lbl.setAlignment(Qt.AlignCenter)
        pix = None
        if os.path.exists(photo_path):
            pix = QPixmap(photo_path).scaled(ds.space_xxl, ds.space_xxl, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if pix is None or pix.isNull():
            pix = _make_avatar(self._data.get("full_name", ""), ds.space_xxl)
        photo_lbl.setPixmap(pix)
        photo_lbl.setStyleSheet(f"QLabel {{ border-radius: {ds.space_xxl // 2}px; background: transparent; }}")
        layout.addWidget(photo_lbl, 0, Qt.AlignCenter)

        # Nom
        name = QLabel(self._data.get("full_name", "—"))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet(f"font-size: {s(13)}px; font-weight: bold; color: {p.text_strong}; border: none;")
        layout.addWidget(name)

        # Email
        email = QLabel(self._data.get("email", ""))
        email.setAlignment(Qt.AlignCenter)
        email.setStyleSheet(f"font-size: {s(8)}px; color: {p.text_soft}; border: none;")
        layout.addWidget(email)

        # Roles
        roles = []
        if self._data.get("is_adm"):       roles.append("Admin")
        if self._data.get("is_coordonator"): roles.append("Coord")
        if self._data.get("is_secretary"):   roles.append("Secr")
        if self._data.get("is_teacher"):     roles.append("Ens.")
        role_lbl = QLabel(" · ".join(roles) if roles else "")
        role_lbl.setAlignment(Qt.AlignCenter)
        role_lbl.setStyleSheet(f"font-size: {s(8)}px; color: {p.primary}; border: none;")
        layout.addWidget(role_lbl)

        layout.addStretch()

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(ds.space_xs)

        event_btn = QPushButton()
        event_btn.setIcon(md3_icon("event", color=p.primary, size=16))
        event_btn.setFixedSize(ds.space_lg, ds.space_lg)
        event_btn.setCursor(Qt.PointingHandCursor)
        event_btn.setToolTip("Événements")
        event_btn.clicked.connect(lambda: self._on_event())
        event_btn.setStyleSheet(f"QPushButton {{ border: 1px solid {p.outline}; border-radius: {ds.radius_xs}px; background: transparent; }} QPushButton:hover {{ background: {p.surface_variant}; }}")
        btn_row.addWidget(event_btn)

        edit_btn = QPushButton()
        edit_btn.setIcon(md3_icon("edit", color=p.primary, size=16))
        edit_btn.setFixedSize(ds.space_lg, ds.space_lg)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setToolTip("Modifier")
        edit_btn.clicked.connect(lambda: self._on_edit())
        edit_btn.setStyleSheet(f"QPushButton {{ border: 1px solid {p.outline}; border-radius: {ds.radius_xs}px; background: transparent; }} QPushButton:hover {{ background: {p.surface_variant}; }}")
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
            self._refresh_grid()

    def _refresh_grid(self):
        w = self.parent()
        while w:
            if isinstance(w, StaffGrid):
                w.refresh()
                return
            w = w.parent()

    @safe_slot("_StaffCard._restyle")
    def _restyle(self):
        self.setStyleSheet(self._style())


class StaffGrid(QWidget):
    """Grille de photos responsive — s'adapte à la largeur, scroll vertical."""

    def __init__(self, cat_key: str, id_lo: int, id_hi: int,
                 is_staff: bool = False, parent=None):
        super().__init__(parent)
        self._cat_key = cat_key
        self._id_lo = id_lo
        self._id_hi = id_hi
        self._is_staff = is_staff
        self._cards: list[QWidget] = []
        self._cols = 1
        self._margin = ds.space_md

        self.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")

    def refresh(self):
        self._load_data()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def _relayout(self):
        if not self._cards:
            return
        avail = self.width() - self._margin * 2
        self._cols = max(1, (avail + ds.space_sm) // (CARD_W + ds.space_sm))
        total_w = self._cols * CARD_W + (self._cols - 1) * ds.space_sm
        x0 = max(self._margin, (self.width() - total_w) // 2)

        for i, card in enumerate(self._cards):
            col = i % self._cols
            row = i // self._cols
            x = x0 + col * (CARD_W + ds.space_sm)
            y = self._margin + row * (CARD_H + ds.space_sm)
            card.move(x, y)

        rows = math.ceil(len(self._cards) / self._cols)
        needed_h = self._margin + rows * CARD_H + (rows - 1) * ds.space_sm + self._margin
        self.setMinimumHeight(needed_h)

    def _load_data(self):
        for c in self._cards:
            c.deleteLater()
        self._cards.clear()

        conn = db.server_conn
        if not conn:
            lbl = QLabel("Base de données non disponible", self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {theme_manager.palette.error}; font-size: {theme_manager.font_size(13)}px;")
            lbl.setGeometry(0, 60, self.width(), 30)
            self._cards.append(lbl)
            self._relayout()
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
            if not rows:
                lbl = QLabel("Aucun membre trouvé dans cette catégorie", self)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"color: {theme_manager.palette.text_soft}; font-size: {theme_manager.font_size(13)}px;")
                lbl.setGeometry(0, 60, self.width(), 30)
                self._cards.append(lbl)
                self._relayout()
                return

            for row in rows:
                data = {
                    "id": row[0],
                    "full_name": f"{row[2]} {row[1]}",
                    "first_name": row[1],
                    "last_name": row[2],
                    "email": row[3],
                    "is_teacher": row[4],
                    "is_coordonator": row[5],
                    "is_secretary": row[6],
                    "is_adm": row[7],
                    "is_staff": self._is_staff,
                }
                card = _StaffCard(data, self)
                card.show()
                self._cards.append(card)

            self._relayout()

        except Exception as e:
            lbl = QLabel(f"Erreur : {e}", self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {theme_manager.palette.error}; font-size: {theme_manager.font_size(11)}px;")
            lbl.setGeometry(self._margin, 60, self.width() - self._margin * 2, 40)
            self._cards.append(lbl)
            self._relayout()
