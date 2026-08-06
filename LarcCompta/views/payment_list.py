"""PaymentList — liste et ajout de paiements."""
from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot


def _fmt_fcfa(amount: int) -> str:
    if amount >= 1000000:
        return f"{amount/1000000:.1f} M"
    if amount >= 1000:
        return f"{amount/1000:,.0f} K".replace(",", " ")
    return str(amount)


class _PaymentForm(QDialog):
    """Dialogue d'ajout de paiement avec recherche eleve."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumSize(480, 380)
        self._student_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        p = theme_manager.palette
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        fstyle = f"""
            QLineEdit, QComboBox {{
                background: {p.background}; border: 1px solid {p.outline};
                border-radius: {ds.radius_xs}px; padding: {ds.space_sm}px;
                color: {p.text_strong}; font-size: {theme_manager.font_size(13)}px;
            }}
        """

        # Recherche eleve
        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Nom, prenom ou email de l'eleve...")
        self._search_input.setFixedHeight(ds.field_height)
        self._search_input.setStyleSheet(fstyle)
        self._search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_input, 1)

        layout.addLayout(search_layout)

        # Resultats recherche
        self._results = QWidget()
        self._results_layout = QVBoxLayout(self._results)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(2)
        self._results.setVisible(False)
        layout.addWidget(self._results)

        # Eleve selectionne
        self._selected_lbl = QLabel("Aucun eleve selectionne")
        self._selected_lbl.setStyleSheet(f"font-weight: bold; color: {p.primary}; font-size: {theme_manager.font_size(13)}px;")
        layout.addWidget(self._selected_lbl)

        # Formulaire
        form = QFormLayout()
        form.setSpacing(ds.space_sm)

        self._f_amount = QLineEdit()
        self._f_amount.setPlaceholderText("Montant en FCFA")
        self._f_amount.setFixedHeight(ds.field_height)
        self._f_amount.setStyleSheet(fstyle)
        form.addRow("Montant (FCFA) :", self._f_amount)

        self._f_date = QDateEdit()
        self._f_date.setDate(QDate.currentDate())
        self._f_date.setCalendarPopup(True)
        self._f_date.setFixedHeight(ds.field_height)
        self._f_date.setStyleSheet(fstyle)
        form.addRow("Date :", self._f_date)

        self._f_method = QComboBox()
        self._f_method.addItems(["especes", "cheque", "virement", "mobile_money"])
        self._f_method.setFixedHeight(ds.field_height)
        self._f_method.setStyleSheet(fstyle)
        form.addRow("Mode :", self._f_method)

        self._f_ref = QLineEdit()
        self._f_ref.setPlaceholderText("Reference (cheque/virement)")
        self._f_ref.setFixedHeight(ds.field_height)
        self._f_ref.setStyleSheet(fstyle)
        form.addRow("Reference :", self._f_ref)

        self._f_note = QLineEdit()
        self._f_note.setPlaceholderText("Note (optionnel)")
        self._f_note.setFixedHeight(ds.field_height)
        self._f_note.setStyleSheet(fstyle)
        form.addRow("Note :", self._f_note)

        layout.addLayout(form)
        layout.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(ds.button_height)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)

        save = QPushButton("Enregistrer")
        save.setCursor(Qt.PointingHandCursor)
        save.setFixedHeight(ds.button_height)
        save.setStyleSheet(f"""
            QPushButton {{ background: {p.primary}; color: white; border: none;
            border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
            font-size: {theme_manager.font_size(13)}px; font-weight: bold; }}
        """)
        save.clicked.connect(self._on_save)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    @safe_slot("_PaymentForm._on_search")
    def _on_search(self):
        query = self._search_input.text().strip()
        # Clear
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if len(query) < 2:
            self._results.setVisible(False)
            return

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.first_name, a.last_name, a.email, c.label as class_label
            FROM larcauth_aecuser a
            JOIN larcauth_student s ON s.aecuser_ptr_id = a.id
            LEFT JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            WHERE s.enabled = true AND (
                a.last_name ILIKE %s OR a.first_name ILIKE %s OR a.email ILIKE %s
            )
            ORDER BY a.last_name LIMIT 8
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        rows = cur.fetchall()
        if not rows:
            self._results.setVisible(False)
            return

        for row in rows:
            sid, fn, ln, email, cls = row
            btn = QPushButton(f"{ln} {fn}  —  {cls or ''}")
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ text-align: left; padding: 4px 8px; color: {theme_manager.palette.text_strong}; }}
                QPushButton:hover {{ background: {theme_manager.palette.surface_variant}; }}
            """)
            btn.clicked.connect(lambda checked, i=sid, t=f"{ln} {fn}": self._select_student(i, t))
            self._results_layout.addWidget(btn)

        self._results.setVisible(True)

    def _select_student(self, sid: int, name: str):
        self._student_id = sid
        self._selected_lbl.setText(f"Eleve : {name}")
        self._results.setVisible(False)
        self._search_input.setText(name)

    @safe_slot("_PaymentForm._on_save")
    def _on_save(self):
        if not self._student_id:
            QMessageBox.warning(self, "Erreur", "Selectionnez un eleve.")
            return
        try:
            amount = int(self._f_amount.text().replace(" ", ""))
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide.")
            return

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compta_payment (student_id, amount, payment_date, payment_method, reference, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (self._student_id, amount,
              self._f_date.date().toPython(),
              self._f_method.currentText(),
              self._f_ref.text().strip() or None,
              self._f_note.text().strip() or None))
        self.accept()


class PaymentList(QScrollArea):
    """Liste des paiements avec filtre et recherche."""

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

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Paiements enregistres")
        title.setStyleSheet(f"font-size: {theme_manager.font_size(18)}px; font-weight: bold; color: {p.text_strong};")
        hdr.addWidget(title)
        hdr.addStretch()

        add_btn = QPushButton("+ Nouveau paiement")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(ds.button_height)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {p.primary}; color: white; border: none;
            border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
            font-size: {theme_manager.font_size(12)}px; font-weight: bold; }}
            QPushButton:hover {{ background: {p.primary}; }}
        """)
        add_btn.clicked.connect(self._on_add)
        hdr.addWidget(add_btn)
        self._layout.addLayout(hdr)

        # Liste
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(ds.space_xs)
        self._layout.addLayout(self._list_layout)

    def refresh(self):
        self._load()

    def _load(self):
        p = theme_manager.palette
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT cp.id, a.first_name, a.last_name, cp.amount, cp.payment_date,
                   cp.payment_method, cp.reference
            FROM compta_payment cp
            JOIN larcauth_aecuser a ON a.id = cp.student_id
            ORDER BY cp.payment_date DESC, cp.id DESC LIMIT 100
        """)

        for row in cur.fetchall():
            pid, fn, ln, amount, date, method, ref = row
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(ds.space_sm, ds.space_xs, ds.space_sm, ds.space_xs)
            rl.setSpacing(ds.space_md)

            # Date
            d = QLabel(str(date))
            d.setFixedWidth(90)
            d.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
            rl.addWidget(d)

            # Nom
            n = QLabel(f"{ln} {fn}")
            n.setFixedWidth(180)
            n.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; font-weight: bold; color: {p.text_strong};")
            rl.addWidget(n)

            # Montant
            m = QLabel(_fmt_fcfa(amount))
            m.setFixedWidth(100)
            m.setStyleSheet(f"font-size: {theme_manager.font_size(13)}px; font-weight: bold; color: {p.success};")
            rl.addWidget(m)

            # Mode
            mode_lbl = QLabel(method)
            mode_lbl.setFixedWidth(100)
            mode_lbl.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
            rl.addWidget(mode_lbl)

            # Reference
            if ref:
                ref_lbl = QLabel(ref)
                ref_lbl.setStyleSheet(f"font-size: {theme_manager.font_size(10)}px; color: {p.text_soft};")
                rl.addWidget(ref_lbl)

            rl.addStretch()
            row_w.setStyleSheet(f"""
                QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}
                QWidget:hover {{ background: {p.surface_variant}; }}
            """)
            self._list_layout.addWidget(row_w)

        self._list_layout.addStretch()

    @safe_slot("PaymentList._on_add")
    def _on_add(self):
        dlg = _PaymentForm(self)
        if dlg.exec():
            self.refresh()
