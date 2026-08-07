"""ClassPaymentPanel — grille vignettes élèves colorées par statut de paiement."""
from __future__ import annotations

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget
from PySide6.QtGui import QPixmap

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.widgets.card import StudentCard
from larccommon.widgets.card_config import DEFAULT_CONFIG
from larccommon.photos import get_photo_path
from larccommon.safe_slot import safe_slot

COLLEGE = 2500000
LYCEE = 3000000
COLLEGE_IDS = (11, 12, 21, 22)


class ClassPaymentPanel(QWidget):
    """Grille de vignettes élèves avec statut de paiement (bordure verte/rouge)."""

    student_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._students: list[dict] = []
        self._class_id = 0
        self._class_label = ""
        self._setup_ui()

    def _setup_ui(self):
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(
            ds.font_label_lg, ds.font_label_lg, ds.font_label_lg, ds.font_label_lg)
        self._grid_layout.setSpacing(DEFAULT_CONFIG.spacing)

    def load(self, class_id: int, class_label: str = ""):
        self._class_id = class_id
        self._class_label = class_label
        self._load_data()

    def _load_data(self):
        self._clear_grid()

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()

        cur.execute(f"""
            SELECT s.aecuser_ptr_id, aec.last_name, aec.first_name,
                   CASE WHEN prog.id IN (13,23) THEN {LYCEE} ELSE {COLLEGE} END as fee,
                   COALESCE(pay.paid, 0) as paid
            FROM larcauth_student s
            JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program prog ON prog.id = l.fk_program_id
            LEFT JOIN LATERAL (
                SELECT COALESCE(SUM(cp.amount), 0) as paid
                FROM compta_payment cp WHERE cp.student_id = s.aecuser_ptr_id
            ) pay ON true
            WHERE s.s_classroom_id = %s AND s.enabled = TRUE
            ORDER BY aec.last_name, aec.first_name
        """, (self._class_id,))

        students = []
        for row in cur.fetchall():
            sid, ln, fn, fee, paid = row
            overdue = paid < fee
            students.append({
                "id": sid,
                "last_name": ln,
                "first_name": fn,
                "fee": fee,
                "paid": paid,
                "overdue": overdue,
            })

        if not students:
            empty = QLabel("Aucun élève dans cette classe")
            empty.setAlignment(Qt.AlignCenter)
            p = theme_manager.palette
            empty.setStyleSheet(f"color: {p.text_soft}; font-size: {theme_manager.font_size(13)}px;")
            self._grid_layout.addWidget(empty, 0, 0)
            return

        self._students = students
        avail_w = self.width()
        cols = max(1, (avail_w + DEFAULT_CONFIG.spacing) // (DEFAULT_CONFIG.card_w + DEFAULT_CONFIG.spacing)) if avail_w > 100 else 3

        for i, s in enumerate(students):
            card = StudentCard(s["id"], s["last_name"], s["first_name"], DEFAULT_CONFIG)
            card.setCursor(Qt.PointingHandCursor)
            card.clicked.connect(lambda sid=s["id"]: self.student_selected.emit(sid))
            card.set_payment_overdue(s["overdue"])
            card.mousePressEvent = self._wrap_click(card, s["id"])
            self._grid_layout.addWidget(card, i // cols, i % cols, Qt.AlignCenter)

    def _wrap_click(self, card, sid):
        orig = card.mousePressEvent
        def handler(event):
            self.student_selected.emit(sid)
            return orig(event)
        return handler

    def _clear_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def refresh(self):
        if self._class_id:
            self._load_data()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self):
        if not self._students:
            return
        avail_w = self.width()
        cols = max(1, (avail_w + DEFAULT_CONFIG.spacing) // (DEFAULT_CONFIG.card_w + DEFAULT_CONFIG.spacing)) if avail_w > 100 else 3
        cards = []
        for i in reversed(range(self._grid_layout.count())):
            item = self._grid_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                self._grid_layout.removeWidget(w)
                if isinstance(w, StudentCard):
                    cards.insert(0, w)
                else:
                    w.deleteLater()
        for idx, card in enumerate(cards):
            self._grid_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)
