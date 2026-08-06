"""ReminderPanel — gestion des rappels de paiement."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QDialog, QFormLayout, QTextEdit, QComboBox,
    QMessageBox,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


def _fmt_fcfa(amount: int) -> str:
    if amount >= 1000000:
        return f"{amount/1000000:.1f} M"
    if amount >= 1000:
        return f"{amount/1000:,.0f} K".replace(",", " ")
    return str(amount)


class _ReminderForm(QDialog):
    """Dialogue d'envoi de rappel."""

    def __init__(self, student_id: int, student_name: str, due_amount: int, parent=None):
        super().__init__(parent)
        self._student_id = student_id
        self._student_name = student_name
        self._due_amount = due_amount
        self.setWindowTitle(f"Rappel — {student_name}")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        p = theme_manager.palette
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        info = QLabel(f"Eleve : {self._student_name}\n"
                      f"Montant du : {_fmt_fcfa(self._due_amount)} FCFA")
        info.setStyleSheet(f"font-size: {theme_manager.font_size(14)}px; color: {p.text_strong}; font-weight: bold;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(ds.space_sm)

        fstyle = f"""
            QComboBox, QTextEdit {{
                background: {p.background}; border: 1px solid {p.outline};
                border-radius: {ds.radius_xs}px; padding: {ds.space_sm}px;
                color: {p.text_strong}; font-size: {theme_manager.font_size(13)}px;
            }}
        """

        self._f_type = QComboBox()
        self._f_type.addItems(["email", "sms", "whatsapp", "courrier"])
        self._f_type.setFixedHeight(ds.field_height)
        self._f_type.setStyleSheet(fstyle)
        form.addRow("Type de rappel :", self._f_type)

        self._f_message = QTextEdit()
        self._f_message.setFixedHeight(120)
        self._f_message.setStyleSheet(fstyle)
        self._f_message.setPlainText(
            f"Madame, Monsieur,\n\n"
            f"Nous vous informons que la scolarite de votre enfant "
            f"{self._student_name} presente un solde de "
            f"{_fmt_fcfa(self._due_amount)} FCFA.\n\n"
            f"Merci de bien vouloir regulariser la situation dans les meilleurs delais.\n\n"
            f"Cordialement,\nLe service comptabilite"
        )
        form.addRow("Message :", self._f_message)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(ds.button_height)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        send = QPushButton("Envoyer le rappel")
        send.setCursor(Qt.PointingHandCursor)
        send.setFixedHeight(ds.button_height)
        send.setStyleSheet(f"""
            QPushButton {{ background: {p.primary}; color: white; border: none;
            border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
            font-weight: bold; }}
        """)
        send.clicked.connect(self._on_send)
        btn_layout.addWidget(send)
        layout.addLayout(btn_layout)

    @safe_slot("_ReminderForm._on_send")
    def _on_send(self):
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        # Trouver un parent lie
        cur.execute("""
            SELECT p.id FROM larcauth_aecuser p
            JOIN larcauth_student_parent sp ON sp.parent_id = p.id
            WHERE sp.student_id = %s LIMIT 1
        """, (self._student_id,))
        parent_row = cur.fetchone()
        parent_id = parent_row[0] if parent_row else None

        cur.execute("""
            INSERT INTO compta_reminder (student_id, parent_id, reminder_type, message)
            VALUES (%s, %s, %s, %s)
        """, (self._student_id, parent_id, self._f_type.currentText(),
              self._f_message.toPlainText().strip()))
        self.accept()


class ReminderPanel(QScrollArea):
    """Panneau des rappels : liste et envoi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        self._layout.setSpacing(ds.space_md)
        self.setWidget(self._container)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        p = theme_manager.palette

        # Titre
        title = QLabel("Rappels de paiement")
        title.setStyleSheet(f"font-size: {theme_manager.font_size(18)}px; font-weight: bold; color: {p.text_strong};")
        self._layout.addWidget(title)

        # Sous-titre
        sub = QLabel("Eleves avec solde impaye. Cliquez sur un eleve pour envoyer un rappel.")
        sub.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; color: {p.text_soft};")
        self._layout.addWidget(sub)

        # Liste des eleves en retard
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(ds.space_xs)
        self._layout.addLayout(self._list_layout)

        # Historique des rappels
        hist_title = QLabel("Historique des rappels envoyes")
        hist_title.setStyleSheet(f"font-size: {theme_manager.font_size(14)}px; font-weight: bold; color: {p.text_strong};")
        self._layout.addWidget(hist_title)

        self._history_layout = QVBoxLayout()
        self._history_layout.setSpacing(ds.space_xs)
        self._layout.addLayout(self._history_layout)

    def refresh(self):
        self._load_due()
        self._load_history()

    def _load_due(self):
        p = theme_manager.palette
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()

        # Eleves avec solde : total du - paiements
        COLLEGE_FEE = 2500000
        LYCEE_FEE = 3000000
        cur.execute(f"""
            SELECT a.id, a.first_name, a.last_name,
                   CASE WHEN prog.id IN (11,12,21,22) THEN {COLLEGE_FEE} ELSE {LYCEE_FEE} END as fee,
                   COALESCE((SELECT SUM(cp.amount) FROM compta_payment cp WHERE cp.student_id = a.id), 0) as paid,
                   c.label as class_label,
                   a.tel_smartphone_1, a.email
            FROM larcauth_aecuser a
            JOIN larcauth_student s ON s.aecuser_ptr_id = a.id
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program prog ON prog.id = l.fk_program_id
            WHERE s.enabled = true
            ORDER BY (fee - COALESCE((SELECT SUM(cp2.amount) FROM compta_payment cp2 WHERE cp2.student_id = a.id), 0)) DESC
        """)

        for row in cur.fetchall():
            sid, fn, ln, fee, paid, cls, phone, email = row
            remaining = fee - paid
            pct = (paid / fee * 100) if fee > 0 else 0

            if remaining <= 0:
                continue  # Deja paye

            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs)
            rl.setSpacing(ds.space_md)

            n = QLabel(f"{ln} {fn}")
            n.setFixedWidth(180)
            n.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; font-weight: bold; color: {p.text_strong};")
            rl.addWidget(n)

            c = QLabel(cls or "")
            c.setFixedWidth(100)
            c.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
            rl.addWidget(c)

            fee_lbl = QLabel(f"{_fmt_fcfa(fee)} → du {_fmt_fcfa(remaining)}")
            fee_lbl.setFixedWidth(200)
            fee_lbl.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.error}; font-weight: bold;")
            rl.addWidget(fee_lbl)

            # Barre
            bar_bg = QWidget()
            bar_bg.setFixedSize(120, 8)
            bar_bg.setStyleSheet(f"background: {p.outline_variant}; border-radius: 4px;")
            bar_fill = QWidget(bar_bg)
            bar_fill.setFixedSize(max(2, int(120 * pct / 100)), 8)
            bar_fill.setStyleSheet(f"background: {p.error if pct < 50 else p.primary}; border-radius: 4px;")
            rl.addWidget(bar_bg)

            # Contact
            contact = []
            if phone: contact.append(phone)
            if email: contact.append(email)
            if contact:
                cl = QLabel(" · ".join(contact[:2]))
                cl.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {p.text_soft};")
                rl.addWidget(cl)

            rl.addStretch()

            # Bouton rappel
            remind_btn = QPushButton("Rappel")
            remind_btn.setCursor(Qt.PointingHandCursor)
            remind_btn.setFixedHeight(30)
            remind_btn.setStyleSheet(f"""
                QPushButton {{ background: {p.error}; color: white; border: none;
                border-radius: {ds.radius_xs}px; padding: 2px 12px;
                font-size: {theme_manager.font_size(11)}px; font-weight: bold; }}
                QPushButton:hover {{ background: {p.error}; }}
            """)
            remind_btn.clicked.connect(lambda checked, sid2=sid, fn2=fn, ln2=ln, rem2=remaining:
                                      self._send_reminder(sid2, f"{ln2} {fn2}", rem2))
            rl.addWidget(remind_btn)

            row_w.setStyleSheet(f"""
                QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}
                QWidget:hover {{ background: {p.surface_variant}; }}
            """)
            self._list_layout.addWidget(row_w)

        self._list_layout.addStretch()

    def _load_history(self):
        p = theme_manager.palette
        while self._history_layout.count():
            item = self._history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT r.sent_at, r.reminder_type, a.first_name, a.last_name, r.status,
                   LEFT(r.message, 80)
            FROM compta_reminder r
            JOIN larcauth_aecuser a ON a.id = r.student_id
            ORDER BY r.sent_at DESC LIMIT 30
        """)

        for row in cur.fetchall():
            sent_at, rtype, fn, ln, status, msg = row
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(ds.space_sm, ds.space_xxs, ds.space_sm, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            d = QLabel(str(sent_at)[:16])
            d.setFixedWidth(130)
            d.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {p.text_soft};")
            rl.addWidget(d)

            t = QLabel(rtype)
            t.setFixedWidth(80)
            t.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {p.primary}; font-weight: bold;")
            rl.addWidget(t)

            n = QLabel(f"{ln} {fn}")
            n.setFixedWidth(160)
            n.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_strong};")
            rl.addWidget(n)

            ms = QLabel(msg or "")
            ms.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {p.text_soft};")
            rl.addWidget(ms, 1)

            row_w.setStyleSheet(f"QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}")
            self._history_layout.addWidget(row_w)

        self._history_layout.addStretch()

    @safe_slot("ReminderPanel._send_reminder")
    def _send_reminder(self, sid: int, name: str, amount: int):
        dlg = _ReminderForm(sid, name, amount, self)
        if dlg.exec():
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
