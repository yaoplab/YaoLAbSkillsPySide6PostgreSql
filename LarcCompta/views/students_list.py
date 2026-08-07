"""StudentsList — liste des eleves avec classe et statut herite du parent."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager


COLLEGE = 2500000
LYCEE = 3000000


def _fmt(amount: int) -> str:
    if amount >= 1000000:
        return f"{amount/1000000:.1f} M"
    if amount >= 1000:
        return f"{amount/1000:,.0f} K".replace(",", " ")
    return str(amount)


class StudentsList(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")

        self._container = QWidget()
        self._setup_ui()
        self.setWidget(self._container)

    def _setup_ui(self):
        p = theme_manager.palette
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        self._layout.setSpacing(ds.space_md)

        title = QLabel("Eleves — Statut des frais")
        title.setStyleSheet(f"font-size: {theme_manager.font_size(18)}px; font-weight: bold; color: {p.text_strong};")
        self._layout.addWidget(title)

        sub = QLabel("Statut herite du parent. Solde = frais - paiements recus.")
        sub.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; color: {p.text_soft};")
        self._layout.addWidget(sub)

        # Header
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs)
        hl.setSpacing(ds.space_md)
        for lbl, w in [("Eleve", 200), ("Classe", 110), ("Parent(s)", 200),
                        ("Frais", 100), ("Encaisses", 100), ("Solde", 100),
                        ("Progression", 150), ("Statut", 90)]:
            l = QLabel(lbl)
            l.setFixedWidth(w)
            l.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; font-weight: bold; color: {p.text_soft};")
            hl.addWidget(l)
        hl.addStretch()
        self._layout.addWidget(hdr)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(2)
        self._layout.addLayout(self._rows_layout)
        self._layout.addStretch()

    def refresh(self):
        self._load()

    def _load(self):
        p = theme_manager.palette
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()

        # Eleves avec leur classe, parents, et statut de paiement
        cur.execute(f"""
            SELECT stu.id, stu.first_name, stu.last_name,
                   COALESCE(cl.label, '') as class_label,
                   COALESCE(STRING_AGG(DISTINCT par.first_name || ' ' || par.last_name, ', '), '—') as parents,
                   CASE WHEN prog.id IN (13,23) THEN {LYCEE} ELSE {COLLEGE} END as fee,
                   COALESCE(pay.paid_amount, 0) as paid,
                   COALESCE(sch.payment_mode, 'inconnu') as mode
            FROM larcauth_aecuser stu
            JOIN larcauth_student s ON s.aecuser_ptr_id = stu.id
            LEFT JOIN larcauth_classroom cl ON cl.id = s.s_classroom_id
            LEFT JOIN larcauth_level l ON l.id = cl.fk_level_id
            LEFT JOIN larcauth_program prog ON prog.id = l.fk_program_id
            LEFT JOIN larcauth_student_parent sp ON sp.student_id = stu.id
            LEFT JOIN larcauth_aecuser par ON par.id = sp.parent_id
            LEFT JOIN compta_payment_schedule sch ON sch.student_id = stu.id
            LEFT JOIN LATERAL (
                SELECT COALESCE(SUM(cp.amount), 0) as paid_amount
                FROM compta_payment cp WHERE cp.student_id = stu.id
            ) pay ON true
            WHERE s.enabled = true
            GROUP BY stu.id, stu.first_name, stu.last_name, cl.label, prog.id, pay.paid_amount, sch.payment_mode
            ORDER BY (CASE WHEN prog.id IN (13,23) THEN {LYCEE} ELSE {COLLEGE} END - COALESCE(pay.paid_amount, 0)) DESC
        """)

        for row in cur.fetchall():
            sid, fn, ln, cls, parents, fee, paid, mode = row
            remaining = max(0, fee - paid)
            pct = (paid / fee * 100) if fee > 0 else 0

            if pct >= 100:
                status = "Solde"
                sc = p.success
            elif pct >= 40:
                status = "En cours"
                sc = p.primary
            elif paid > 0:
                status = "En retard"
                sc = p.error + "80"
            else:
                status = "Non solde"
                sc = p.error

            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(ds.space_sm, ds.space_xxs, ds.space_sm, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            # Nom eleve
            n = QLabel(f"{fn} {ln}")
            n.setFixedWidth(200)
            n.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; font-weight: bold; color: {p.text_strong};")
            rl.addWidget(n)

            # Classe
            cl = QLabel(cls)
            cl.setFixedWidth(110)
            cl.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
            rl.addWidget(cl)

            # Parents
            par = QLabel(parents[:35])
            par.setFixedWidth(200)
            par.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
            rl.addWidget(par)

            # Frais
            fee_l = QLabel(_fmt(fee))
            fee_l.setFixedWidth(100)
            fee_l.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; color: {p.text_strong};")
            rl.addWidget(fee_l)

            # Paye
            paid_l = QLabel(_fmt(paid))
            paid_l.setFixedWidth(100)
            paid_l.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; color: {p.success};")
            rl.addWidget(paid_l)

            # Solde
            solde = QLabel(_fmt(remaining))
            solde.setFixedWidth(100)
            solde.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; font-weight: bold; color: {sc};")
            rl.addWidget(solde)

            # Barre
            bar_bg = QFrame()
            bar_bg.setFixedSize(150, 10)
            bar_bg.setStyleSheet(f"background: {p.outline_variant}; border-radius: 5px;")
            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedSize(max(2, int(150 * pct / 100)), 10)
            bar_fill.setStyleSheet(f"background: {p.success if pct >= 100 else p.primary if pct >= 40 else p.error}; border-radius: 5px;")
            rl.addWidget(bar_bg)

            # Statut
            st = QLabel(status)
            st.setFixedWidth(90)
            st.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; font-weight: bold; color: {sc};")
            rl.addWidget(st)

            rl.addStretch()
            row_w.setStyleSheet(f"""
                QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}
                QWidget:hover {{ background: {p.surface_variant}; }}
            """)
            self._rows_layout.addWidget(row_w)

        self._rows_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
