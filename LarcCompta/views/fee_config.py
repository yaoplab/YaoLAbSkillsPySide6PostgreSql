"""FeeConfig — configuration des barèmes et échéanciers."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QComboBox, QFrame, QMessageBox, QGridLayout,
)
from PySide6.QtCore import QDate

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


def _fmt(amount: int) -> str:
    if amount >= 1000000:
        return f"{amount / 1000000:.1f} M"
    return f"{amount // 1000:,} K".replace(",", " ")


class FeeConfig(QScrollArea):
    """Configuration : barèmes, échéances, et gestion des parents."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setObjectName("fee_config")
        ds.theme_changed.connect(self._restyle)
        self._restyle()

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
        self._layout.setSpacing(ds.space_md)
        self.setWidget(self._container)
        self._setup_ui()
        self.refresh()

    @safe_slot("FeeConfig._restyle")
    def _restyle(self):
        self.setStyleSheet(
            f"#fee_config {{ background: {theme_manager.palette.background}; border: none; }}")

    def _setup_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        self._layout.addWidget(self._section_title("Bareme des frais par niveau"))

        sub = QLabel("Double-cliquez un montant pour le modifier. Changement immediat en base.")
        sub.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; border: none;")
        self._layout.addWidget(sub)

        self._fee_table = QVBoxLayout()
        self._fee_table.setSpacing(ds.space_xxs)
        self._layout.addLayout(self._fee_table)

        # ── Echeancier global ──
        self._layout.addWidget(self._section_title("Echeancier global (%)"))

        self._sched_table = QVBoxLayout()
        self._sched_table.setSpacing(ds.space_xxs)
        self._layout.addLayout(self._sched_table)

        # ── Echeances parents ──
        hdr2 = QHBoxLayout()
        hdr2.addWidget(self._section_title("Echeances personnalisees parents"))
        hdr2.addStretch()
        add_btn = QPushButton("+ Ajouter une echeance")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(ds.button_height)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {p.primary}; color: {p.on_primary}; border: none;
            border-radius: {ds.radius_sm}px; padding: {ds.space_xs}px {ds.space_md}px;
            font-size: {s(12)}px; font-weight: bold; }}
            QPushButton:hover {{ background: {p.primary}; }}
        """)
        add_btn.clicked.connect(self._add_milestone)
        hdr2.addWidget(add_btn)
        self._layout.addLayout(hdr2)

        self._milestone_table = QVBoxLayout()
        self._milestone_table.setSpacing(ds.space_xxs)
        self._layout.addLayout(self._milestone_table)

        self._layout.addStretch()

    def _section_title(self, text: str) -> QLabel:
        p = theme_manager.palette
        s = theme_manager.font_size
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: {s(16)}px; font-weight: bold; color: {p.text_strong}; "
            f"border: none; padding-top: {ds.space_sm}px;")
        return lbl

    def refresh(self):
        self._load_fees()
        self._load_schedule()
        self._load_milestones()

    # ── Barème ──
    def _load_fees(self):
        while self._fee_table.count():
            item = self._fee_table.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        p = theme_manager.palette
        s = theme_manager.font_size
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT cfl.id, l.label, p.sigle, cfl.annual_fee, cfl.monthly_amount, cfl.level_id
            FROM compta_fee_level cfl
            JOIN larcauth_level l ON l.id = cfl.level_id
            JOIN larcauth_program p ON p.id = l.fk_program_id
            WHERE cfl.academic_year = '2026-2027'
            ORDER BY p.sigle, l.label
        """)
        for row in cur.fetchall():
            fid, level, sigle, annual, monthly, lid = row
            rw = QWidget()
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(ds.space_sm, ds.space_xxs, ds.space_sm, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            for text, w in [(f"{sigle}", 50), (level, 130)]:
                lbl = QLabel(text)
                lbl.setFixedWidth(w)
                lbl.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_strong}; border: none;")
                rl.addWidget(lbl)

            # Montant annuel editable
            fee_edit = QLineEdit(str(annual))
            fee_edit.setFixedWidth(ds.space_xxl + ds.space_md)
            fee_edit.setFixedHeight(ds.table_row_min + ds.space_xs)
            fee_edit.setStyleSheet(
                f"background: {p.surface}; border: 1px solid {p.outline}; "
                f"border-radius: {ds.radius_xs}px; padding: {ds.space_xxs}px {ds.space_xs}px; "
                f"color: {p.text_strong}; font-size: {s(12)}px;")
            fee_edit.setToolTip(f"Modifier le montant annuel pour {level} ({sigle})")
            # Sauver au blur (perte de focus)
            fee_edit.editingFinished.connect(
                lambda le=fee_edit, f=fid: self._save_fee(f, le.text()))
            rl.addWidget(fee_edit)

            lbl_fcfa = QLabel("FCFA")
            lbl_fcfa.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; border: none;")
            rl.addWidget(lbl_fcfa)

            rl.addStretch()
            rw.setStyleSheet(
                f"QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}"
                f"QWidget:hover {{ background: {p.surface_variant}; }}")
            self._fee_table.addWidget(rw)

    def _save_fee(self, fee_id: int, text: str):
        try:
            amount = int(text.replace(" ", ""))
        except ValueError:
            return
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("UPDATE compta_fee_level SET annual_fee = %s, monthly_amount = %s WHERE id = %s",
                    (amount, amount // 10, fee_id))

    # ── Échéancier global ──
    def _load_schedule(self):
        while self._sched_table.count():
            item = self._sched_table.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        p = theme_manager.palette
        s = theme_manager.font_size
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT id, month_number, percentage_expected
            FROM compta_payment_schedule WHERE academic_year = '2026-2027'
            ORDER BY month_number
        """)
        months = ["Sept.", "Oct.", "Nov.", "Dec.", "Janv.", "Fev.", "Mars", "Avr.", "Mai", "Juin"]
        for row in cur.fetchall():
            sid, mn, pct = row
            rw = QWidget()
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(ds.space_sm, ds.space_xxs, ds.space_sm, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            lbl = QLabel(f"Mois {mn} — {months[mn-1] if mn <= 10 else 'Mois '+str(mn)}")
            lbl.setFixedWidth(150)
            lbl.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_strong}; border: none;")
            rl.addWidget(lbl)

            pct_edit = QLineEdit(str(pct))
            pct_edit.setFixedWidth(80)
            pct_edit.setFixedHeight(ds.table_row_min + ds.space_xs)
            pct_edit.setStyleSheet(
                f"background: {p.surface}; border: 1px solid {p.outline}; "
                f"border-radius: {ds.radius_xs}px; padding: {ds.space_xxs}px {ds.space_xs}px; "
                f"color: {p.text_strong}; font-size: {s(12)}px;")
            pct_edit.editingFinished.connect(
                lambda le=pct_edit, s=sid: self._save_schedule(s, le.text()))
            rl.addWidget(pct_edit)

            lbl_pct = QLabel("% attendu cumule")
            lbl_pct.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; border: none;")
            rl.addWidget(lbl_pct)

            rl.addStretch()
            rw.setStyleSheet(
                f"QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}"
                f"QWidget:hover {{ background: {p.surface_variant}; }}")
            self._sched_table.addWidget(rw)

    def _save_schedule(self, sid: int, text: str):
        try:
            pct = float(text)
            if pct < 0 or pct > 100:
                return
        except ValueError:
            return
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("UPDATE compta_payment_schedule SET percentage_expected = %s WHERE id = %s",
                    (pct, sid))

    # ── Échéances parents ──
    def _load_milestones(self):
        while self._milestone_table.count():
            item = self._milestone_table.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        p = theme_manager.palette
        s = theme_manager.font_size
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, a.first_name, a.last_name, m.due_date, m.amount_expected, m.notes
            FROM compta_parent_milestone m
            JOIN larcauth_aecuser a ON a.id = m.parent_id
            ORDER BY m.due_date DESC, a.last_name LIMIT 50
        """)
        for row in cur.fetchall():
            mid, fn, ln, due, amount, notes = row
            rw = QWidget()
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(ds.space_sm, ds.space_xxs, ds.space_sm, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            for text, w, color, bold in [
                (f"{fn} {ln}", 170, p.text_strong, True),
                (str(due), 110, p.text_soft, False),
                (_fmt(amount), 100, p.primary, True),
                (notes or "", 200, p.text_soft, False),
            ]:
                lbl = QLabel(text)
                lbl.setFixedWidth(w)
                lbl.setStyleSheet(
                    f"font-size: {s(11)}px; {'font-weight: bold;' if bold else ''} "
                    f"color: {color}; border: none;")
                rl.addWidget(lbl)

            del_btn = QPushButton("Suppr.")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedHeight(ds.space_lg)
            del_btn.setStyleSheet(
                f"QPushButton {{ background: {p.error}; color: white; border: none; "
                f"border-radius: {ds.radius_xs}px; padding: 2px 8px; "
                f"font-size: {s(10)}px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {p.error}; }}")
            del_btn.clicked.connect(lambda checked, m=mid: self._delete_milestone(m))
            rl.addWidget(del_btn)

            rl.addStretch()
            rw.setStyleSheet(
                f"QWidget {{ background: {p.surface}; border-radius: {ds.radius_xs}px; }}"
                f"QWidget:hover {{ background: {p.surface_variant}; }}")
            self._milestone_table.addWidget(rw)

    def _add_milestone(self):
        """Ajoute une échéance personnalisée pour un parent."""
        conn = db.server_conn
        if not conn:
            return
        # Dialogue rapide : recherche parent + date + montant
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDateEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("Nouvelle echeance parent")
        dlg.setMinimumSize(420, 250)
        dlg.setStyleSheet(f"background: {theme_manager.palette.surface};")
        lo = QFormLayout(dlg)
        lo.setSpacing(ds.space_sm)

        fstyle = (
            f"background: {theme_manager.palette.background}; "
            f"border: 1px solid {theme_manager.palette.outline}; "
            f"border-radius: {ds.radius_xs}px; padding: {ds.space_sm}px; "
            f"color: {theme_manager.palette.text_strong}; "
            f"font-size: {theme_manager.font_size(13)}px;")

        parent_name = QLineEdit()
        parent_name.setPlaceholderText("Nom du parent payeur...")
        parent_name.setFixedHeight(ds.field_height)
        parent_name.setStyleSheet(fstyle)
        lo.addRow("Parent :", parent_name)

        due_date = QDateEdit()
        due_date.setDate(QDate.currentDate())
        due_date.setCalendarPopup(True)
        due_date.setFixedHeight(ds.field_height)
        due_date.setStyleSheet(fstyle)
        lo.addRow("Date echeance :", due_date)

        amount = QLineEdit()
        amount.setPlaceholderText("Montant attendu (FCFA)")
        amount.setFixedHeight(ds.field_height)
        amount.setStyleSheet(fstyle)
        lo.addRow("Montant :", amount)

        note = QLineEdit()
        note.setPlaceholderText("Note (optionnel)")
        note.setFixedHeight(ds.field_height)
        note.setStyleSheet(fstyle)
        lo.addRow("Note :", note)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(ds.button_height)
        cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel)
        save = QPushButton("Ajouter")
        save.setCursor(Qt.PointingHandCursor)
        save.setFixedHeight(ds.button_height)
        save.setStyleSheet(
            f"QPushButton {{ background: {theme_manager.palette.primary}; color: white; "
            f"border: none; border-radius: {ds.radius_sm}px; "
            f"padding: {ds.space_xs}px {ds.space_md}px; font-weight: bold; }}")
        btn_row.addWidget(save)
        lo.addRow(btn_row)

        def on_save():
            name = parent_name.text().strip()
            try:
                amt = int(amount.text().replace(" ", ""))
            except ValueError:
                return
            if not name or amt <= 0:
                return
            cur = conn.cursor()
            # Chercher le parent
            cur.execute(
                "SELECT id FROM larcauth_aecuser WHERE "
                "(first_name || ' ' || last_name) ILIKE %s LIMIT 1",
                (f"%{name}%",))
            pr = cur.fetchone()
            if not pr:
                QMessageBox.warning(dlg, "Erreur", "Parent introuvable.")
                return
            cur.execute("""INSERT INTO compta_parent_milestone (parent_id, due_date, amount_expected, notes)
                VALUES (%s, %s, %s, %s)""",
                (pr[0], due_date.date().toPython(), amt, note.text().strip() or None))
            dlg.accept()

        save.clicked.connect(on_save)
        if dlg.exec():
            self.refresh()

    def _delete_milestone(self, mid: int):
        conn = db.server_conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("DELETE FROM compta_parent_milestone WHERE id = %s", (mid,))
        self.refresh()
