"""ClassPaymentPanel — grille vignettes avec statut hérité du parent payeur."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.widgets.card import StudentCard
from larccommon.widgets.card_config import DEFAULT_CONFIG
from larccommon.safe_slot import safe_slot


class ClassPaymentPanel(QWidget):

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

        # Pour chaque élève, calculer le statut hérité du/des parents payeurs
        cur.execute("""
            WITH parent_status AS (
                SELECT sp.student_id, par.id as parent_id,
                       COALESCE(SUM(sf.annual_fee), 0) as total_du,
                       COALESCE((
                           SELECT SUM(cp.amount) FROM compta_payment cp
                           WHERE cp.parent_id = par.id
                       ), 0) as total_paid
                FROM larcauth_student_parent sp
                JOIN larcauth_parent lp ON lp.aecuser_ptr_id = sp.parent_id AND lp.is_payer = TRUE
                JOIN larcauth_aecuser par ON par.id = sp.parent_id
                LEFT JOIN compta_student_fee sf ON sf.student_id = sp.student_id
                GROUP BY sp.student_id, par.id
            )
            SELECT s.aecuser_ptr_id, aec.last_name, aec.first_name,
                   COALESCE(MAX(ps.total_du), 0) as max_du,
                   COALESCE(MAX(ps.total_paid), 0) as max_paid,
                   COALESCE(STRING_AGG(DISTINCT par.first_name || ' ' || par.last_name, ', '), '—') as parents
            FROM larcauth_student s
            JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
            LEFT JOIN larcauth_student_parent sp ON sp.student_id = s.aecuser_ptr_id
            LEFT JOIN larcauth_parent lp ON lp.aecuser_ptr_id = sp.parent_id AND lp.is_payer = TRUE
            LEFT JOIN larcauth_aecuser par ON par.id = sp.parent_id
            LEFT JOIN parent_status ps ON ps.student_id = s.aecuser_ptr_id
            WHERE s.s_classroom_id = %s AND s.enabled = TRUE
            GROUP BY s.aecuser_ptr_id, aec.last_name, aec.first_name
            ORDER BY aec.last_name, aec.first_name
        """, (self._class_id,))

        students = []
        for row in cur.fetchall():
            sid, ln, fn, max_du, max_paid, parents_str = row

            # Déterminer le statut à partir du meilleur parent
            if max_du <= 0:
                status = "retard"       # pas de frais configurés
            elif max_paid >= max_du:
                status = "solde"         # tout payé
            elif max_paid > 0:
                status = "normal"        # en cours (payé mais pas tout)
            else:
                status = "retard"        # rien payé

            students.append({
                "id": sid, "last_name": ln, "first_name": fn,
                "du": max_du, "paid": max_paid, "status": status,
            })

        if not students:
            empty = QLabel("Aucun eleve dans cette classe")
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
            card.clicked.connect(lambda sid=s["id"]: self.student_selected.emit(sid))
            card.set_payment_status(s["status"])
            # Cacher les 4 badges D/M/P/E (spécifique secrétaire, inutile en compta)
            for j in range(card._badges_row.count()):
                w = card._badges_row.itemAt(j).widget()
                if w:
                    w.hide()
            self._grid_layout.addWidget(card, i // cols, i % cols, Qt.AlignCenter)

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
