"""Dashboard LarcCompta — KPIs, graphiques, encaissements."""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea,
)

from larccommon.database import db
from larccommon.design_system import ds
from larccommon.theme import theme_manager

# Frais par programme (FCFA)
COLLEGE_FEE = 2500000
LYCEE_FEE   = 3000000
COLLEGE_IDS = (11, 12, 21, 22)  # PYP, MYP, PP, PEI
LYCEE_IDS   = (13, 23)           # DPEn, DPFr


def _fmt_fcfa(amount: int) -> str:
    """Formate un montant en FCFA avec separateurs de milliers."""
    if amount >= 1000000:
        return f"{amount/1000000:.1f} M"
    if amount >= 1000:
        return f"{amount/1000:,.0f} K".replace(",", " ")
    return str(amount)


class _BarChart(QWidget):
    """Graphique a barres simple (encaissements par mois/programme)."""

    def __init__(self, title: str, data: list[tuple[str, int, int]], parent=None):
        """
        data: [(label, value, max_value), ...]
        """
        super().__init__(parent)
        self._title = title
        self._data = data
        self.setMinimumHeight(200)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if h < 60:
            p.end()
            return

        # Fond
        p.fillRect(0, 0, w, h, QColor(theme_manager.palette.surface))

        # Titre
        p.setPen(QColor(theme_manager.palette.text_strong))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(12, 22, self._title)

        if not self._data or not self._data[0][2]:
            p.end()
            return

        n = len(self._data)
        bar_w = max(20, min(80, (w - 80) // n - 10))
        chart_h = max(1, h - 60)
        x0 = 60
        y0 = h - 30
        max_val = max(v[2] for v in self._data) or 1

        # Grille
        p.setPen(QPen(QColor(theme_manager.palette.outline_variant), 1, Qt.DotLine))
        for frac in [0.25, 0.5, 0.75, 1.0]:
            y = y0 - int(frac * chart_h)
            p.drawLine(x0, y, w - 20, y)
            p.setPen(QColor(theme_manager.palette.text_soft))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(5, y + 4, _fmt_fcfa(int(frac * max_val)))
            p.setPen(QPen(QColor(theme_manager.palette.outline_variant), 1, Qt.DotLine))

        # Barres
        pal = theme_manager.palette
        colors = [QColor(pal.primary), QColor(pal.success), QColor(pal.secondary),
                  QColor(pal.error), QColor(pal.tertiary), QColor(pal.primary_container)]
        for i, (label, val, _max) in enumerate(self._data):
            x = x0 + i * (bar_w + 10)
            bar_h_val = int((val / max_val) * chart_h) if max_val > 0 else 0
            bar_h_max = int((_max / max_val) * chart_h) if max_val > 0 else 0

            if _max > val:
                p.fillRect(x, y0 - bar_h_max, bar_w, bar_h_max,
                           QColor(theme_manager.palette.outline_variant))
            if bar_h_val > 0:
                p.fillRect(x, y0 - bar_h_val, bar_w, bar_h_val, colors[i % len(colors)])

            p.setPen(QColor(theme_manager.palette.text_strong))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(x - 5, y0 + 14, bar_w + 10, 16, Qt.AlignCenter, label[:10])

            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.drawText(x - 5, y0 - bar_h_max - 16, bar_w + 10, 14,
                       Qt.AlignCenter, _fmt_fcfa(val))

        p.end()


class _DonutSlice:
    def __init__(self, label: str, value: int, color: QColor):
        self.label = label
        self.value = value
        self.color = color


class _DonutChart(QWidget):
    """Graphique en anneau (ex: encaisse vs reste a encaisser)."""

    def __init__(self, title: str, slices: list[_DonutSlice], parent=None):
        super().__init__(parent)
        self._title = title
        self._slices = slices
        self.setMinimumSize(260, 260)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor(theme_manager.palette.surface))

        # Titre
        p.setPen(QColor(theme_manager.palette.text_strong))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(12, 22, self._title)

        cx, cy = w // 2, h // 2 + 10
        outer_r = min(cx, cy) - 20
        inner_r = outer_r * 3 // 5
        total = sum(s.value for s in self._slices) or 1

        # Dessiner les tranches
        start_angle = 0
        for s in self._slices:
            span = int(s.value * 360 * 16 / total)
            if span > 0:
                p.setBrush(s.color)
                p.setPen(Qt.NoPen)
                p.drawPie(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2),
                          start_angle, span)
                start_angle += span

        # Trou central
        p.setBrush(QColor(theme_manager.palette.surface))
        p.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Total au centre
        p.setPen(QColor(theme_manager.palette.text_strong))
        p.setFont(QFont("Segoe UI", 13, QFont.Bold))
        p.drawText(QRectF(cx - 60, cy - 16, 120, 20), Qt.AlignCenter, _fmt_fcfa(total))
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(QColor(theme_manager.palette.text_soft))
        p.drawText(QRectF(cx - 60, cy + 4, 120, 16), Qt.AlignCenter, "Total du")

        # Legende
        lx = w - 160
        ly = 40
        p.setFont(QFont("Segoe UI", 9))
        for s in self._slices:
            p.setBrush(s.color)
            p.setPen(Qt.NoPen)
            p.drawRect(lx, ly, 12, 12)
            p.setPen(QColor(theme_manager.palette.text_strong))
            p.drawText(lx + 18, ly + 10, f"{s.label}: {_fmt_fcfa(s.value)}")
            ly += 20

        p.end()


class Dashboard(QScrollArea):
    """Tableau de bord comptable avec KPIs et graphiques."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")

        self._container = QWidget()
        self._setup_ui()
        self.setWidget(self._container)
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # Titre
        title = QLabel("Tableau de bord — Scolarite 2026-2027")
        title.setStyleSheet(f"""
            font-size: {theme_manager.font_size(18)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
        """)
        layout.addWidget(title)

        # ── KPI Row ──
        self._kpi_layout = QHBoxLayout()
        self._kpi_layout.setSpacing(ds.space_md)
        layout.addLayout(self._kpi_layout)

        # ── Charts Row ──
        charts = QHBoxLayout()
        charts.setSpacing(ds.space_md)
        self._donut = QWidget()
        self._bar = QWidget()
        charts.addWidget(self._donut, 3)
        charts.addWidget(self._bar, 5)
        layout.addLayout(charts)

        # ── Table detail par niveau ──
        self._table_layout = QVBoxLayout()
        layout.addLayout(self._table_layout)

        layout.addStretch()

    def refresh(self):
        self._load_kpis()
        self._load_charts()
        self._load_table()

    def _make_kpi_card(self, label: str, value: str, color: str) -> QFrame:
        p = theme_manager.palette
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: {ds.radius_sm}px; border-left: 4px solid {color};
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm)
        l.setSpacing(ds.space_xxs)

        vl = QLabel(value)
        vl.setStyleSheet(f"font-size: {theme_manager.font_size(24)}px; font-weight: bold; color: {color};")
        l.addWidget(vl)

        ll = QLabel(label)
        ll.setStyleSheet(f"font-size: {theme_manager.font_size(11)}px; color: {p.text_soft};")
        l.addWidget(ll)
        return card

    def _load_kpis(self):
        # Clear
        while self._kpi_layout.count():
            item = self._kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p = theme_manager.palette
        conn = db.server_conn
        if not conn:
            return

        cur = conn.cursor()

        # Total du (tous les eleves)
        cur.execute("""
            SELECT COUNT(*) FROM larcauth_student WHERE enabled = true
        """)
        total_students = cur.fetchone()[0]

        # Estimation total du
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE p.id IN (11,12,21,22)),
                COUNT(*) FILTER (WHERE p.id IN (13,23))
            FROM larcauth_student s
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program p ON p.id = l.fk_program_id
            WHERE s.enabled = true
        """)
        n_college, n_lycee = cur.fetchone()
        total_du = n_college * COLLEGE_FEE + n_lycee * LYCEE_FEE

        # Total encaisse
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM compta_payment")
        total_paid = cur.fetchone()[0]

        # Reste a encaisser
        remaining = total_du - total_paid
        taux = (total_paid / total_du * 100) if total_du > 0 else 0

        # Nombre de payeurs
        cur.execute("SELECT COUNT(DISTINCT student_id) FROM compta_payment")
        n_payers = cur.fetchone()[0]

        # Ajouter les KPIs
        self._kpi_layout.addWidget(self._make_kpi_card("Total du", _fmt_fcfa(total_du), p.primary))
        self._kpi_layout.addWidget(self._make_kpi_card("Encaisses", _fmt_fcfa(total_paid), p.success))
        self._kpi_layout.addWidget(self._make_kpi_card("Reste a encaisser", _fmt_fcfa(remaining), p.error))
        self._kpi_layout.addWidget(self._make_kpi_card("Taux encaissement", f"{taux:.0f} %", p.secondary))
        self._kpi_layout.addWidget(self._make_kpi_card("Eleves payeurs", f"{n_payers}/{total_students}", p.tertiary))

    def _load_charts(self):
        p = theme_manager.palette
        conn = db.server_conn
        if not conn:
            return

        cur = conn.cursor()

        # Donut: encaisse / reste
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM compta_payment")
        total_paid = cur.fetchone()[0]
        total_du = 0
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE p.id IN (11,12,21,22)) * %s +
                COUNT(*) FILTER (WHERE p.id IN (13,23)) * %s
            FROM larcauth_student s
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program p ON p.id = l.fk_program_id
            WHERE s.enabled = true
        """, (COLLEGE_FEE, LYCEE_FEE))
        total_du = cur.fetchone()[0]
        remaining = max(0, total_du - total_paid)

        donut = _DonutChart("Repartition des frais", [
            _DonutSlice("Encaisses", total_paid, QColor(p.success)),
            _DonutSlice("Reste a encaisser", remaining, QColor(p.error)),
        ])

        # Bar chart: encaissements par categorie
        cur.execute("""
            SELECT
                CASE WHEN p.id IN (11,12,21,22) THEN 'College (2.5M)'
                     ELSE 'Lycee (3M)' END as cat,
                COUNT(*),
                CASE WHEN bool_or(p.id IN (11,12,21,22)) THEN %s ELSE %s END as fee
            FROM larcauth_student s
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program p ON p.id = l.fk_program_id
            WHERE s.enabled = true
            GROUP BY 1
        """, (COLLEGE_FEE, LYCEE_FEE))
        rows = cur.fetchall()

        bar_data = []
        for cat, count, fee in rows:
            cur.execute("""
                SELECT COALESCE(SUM(cp.amount), 0)
                FROM compta_payment cp
                JOIN larcauth_student s2 ON s2.aecuser_ptr_id = cp.student_id
                JOIN larcauth_classroom c2 ON c2.id = s2.s_classroom_id
                JOIN larcauth_level l2 ON l2.id = c2.fk_level_id
                JOIN larcauth_program p2 ON p2.id = l2.fk_program_id
                WHERE p2.id IN ({}) AND s2.enabled = true
            """.format(
                ','.join(str(i) for i in COLLEGE_IDS) if 'College' in cat
                else ','.join(str(i) for i in LYCEE_IDS)
            ))
            paid = cur.fetchone()[0]
            total = count * fee
            bar_data.append((cat, paid, total))

        bar = _BarChart("Encaissements par categorie", bar_data)

        # Remplacer les widgets
        old_layout = self._container.layout()
        if self._donut:
            old_layout.replaceWidget(self._donut, donut)
            self._donut.deleteLater()
            self._donut = donut
        if self._bar:
            old_layout.replaceWidget(self._bar, bar)
            self._bar.deleteLater()
            self._bar = bar

    def _load_table(self):
        # Clear
        while self._table_layout.count():
            item = self._table_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p = theme_manager.palette
        conn = db.server_conn
        if not conn:
            return

        cur = conn.cursor()

        # Detail par programme
        cur.execute("""
            SELECT p.sigle, COUNT(*),
                   CASE WHEN p.id IN (11,12,21,22) THEN %s ELSE %s END as fee
            FROM larcauth_student s
            JOIN larcauth_classroom c ON c.id = s.s_classroom_id
            JOIN larcauth_level l ON l.id = c.fk_level_id
            JOIN larcauth_program p ON p.id = l.fk_program_id
            WHERE s.enabled = true
            GROUP BY p.sigle, p.id
            ORDER BY p.sigle
        """, (COLLEGE_FEE, LYCEE_FEE))

        # Table header
        hdr = QLabel("Detail par programme")
        hdr.setStyleSheet(f"font-size: {theme_manager.font_size(14)}px; font-weight: bold; color: {p.text_strong};")
        self._table_layout.addWidget(hdr)

        for sigle, count, fee in cur.fetchall():
            total = count * fee
            # Paiements pour ce programme
            cur.execute("""
                SELECT COALESCE(SUM(cp.amount), 0)
                FROM compta_payment cp
                JOIN larcauth_student s2 ON s2.aecuser_ptr_id = cp.student_id
                JOIN larcauth_classroom c2 ON c2.id = s2.s_classroom_id
                JOIN larcauth_level l2 ON l2.id = c2.fk_level_id
                JOIN larcauth_program p2 ON p2.id = l2.fk_program_id
                WHERE p2.sigle = %s AND s2.enabled = true
            """, (sigle,))
            paid = cur.fetchone()[0]
            pct = (paid / total * 100) if total > 0 else 0

            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, ds.space_xxs, 0, ds.space_xxs)
            rl.setSpacing(ds.space_md)

            for text, w, color in [
                (sigle, 80, p.text_strong),
                (f"{count} eleves", 80, p.text_soft),
                (_fmt_fcfa(total), 100, p.text_strong),
                (_fmt_fcfa(paid), 100, p.success),
                (f"{pct:.0f}%", 60, p.primary if pct > 50 else p.error),
            ]:
                lbl = QLabel(text)
                lbl.setFixedWidth(w)
                lbl.setStyleSheet(f"font-size: {theme_manager.font_size(12)}px; color: {color};")
                rl.addWidget(lbl)

            # Barre de progression
            bar_bg = QFrame()
            bar_bg.setFixedSize(150, 10)
            bar_bg.setStyleSheet(f"background: {p.outline_variant}; border-radius: 5px;")
            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedSize(max(2, int(150 * pct / 100)), 10)
            bar_fill.setStyleSheet(f"background: {p.success if pct > 50 else p.error}; border-radius: 5px;")
            rl.addWidget(bar_bg)

            rl.addStretch()
            self._table_layout.addWidget(row)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
