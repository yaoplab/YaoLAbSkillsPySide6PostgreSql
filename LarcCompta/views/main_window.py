"""MainWindow LarcCompta — dashboard frais de scolarite."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QScrollArea,
)

from larccommon.database import db
from larccommon.session import session
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot


class MainWindow(QWidget):

    SIDEBAR_WIDTH = 233

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LarcCompta — Scolarite")
        self._current_key: str | None = None
        self._pages: dict[str, QWidget] = {}

        self._setup_ui()
        ds.theme_changed.connect(self._restyle)
        QTimer.singleShot(100, lambda: self._switch_to("dashboard"))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(self.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"""
            #sidebar {{
                background-color: {theme_manager.palette.surface_variant};
                border-right: 1px solid {theme_manager.palette.border};
            }}
        """)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(ds.space_xs, theme_manager.image.theme_btn,
                              ds.space_xs, ds.space_lg)
        sb.setSpacing(ds.space_xs)

        self._user_label = QLabel(session.full_name or "Comptabilite")
        self._user_label.setStyleSheet(f"""
            font-size: {theme_manager.font_size(13)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong}; padding: 0 5px;
        """)
        sb.addWidget(self._user_label)

        role = QLabel("Comptabilite")
        role.setStyleSheet(f"""
            font-size: {theme_manager.font_size(10)}px;
            color: {theme_manager.palette.text_strong}; padding: 0 5px 8px 5px;
        """)
        sb.addWidget(role)

        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {theme_manager.palette.border};")
        sb.addWidget(sep)
        sb.addSpacing(8)

        # Navigation
        nav_items = [
            ("dashboard", "Tableau de bord", "home"),
            ("payments",   "Paiements",      "check"),
            ("rappels",    "Rappels",         "schedule"),
        ]
        self._buttons: dict[str, QPushButton] = {}
        for key, label, icon_name in nav_items:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(theme_manager.image.theme_btn)
            btn.setFont(QFont("Segoe UI", 10))
            if icon_name:
                try:
                    btn.setIcon(md3_icon(icon_name, color=theme_manager.palette.text_strong, size=18))
                except Exception:
                    pass
            btn.clicked.connect(lambda checked, k=key: self._switch_to(k))
            self._buttons[key] = btn
            sb.addWidget(btn)

        sb.addStretch()
        self._sidebar = sidebar
        layout.addWidget(sidebar)

        # ── Content ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {theme_manager.palette.background};")
        layout.addWidget(self._stack, 1)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    @safe_slot("MainWindow._switch_to")
    def _switch_to(self, key: str):
        if key == self._current_key:
            return
        self._current_key = key
        for btn in self._buttons.values():
            btn.setChecked(False)
        if key in self._buttons:
            self._buttons[key].setChecked(True)

        if key not in self._pages:
            if key == "dashboard":
                from LarcCompta.views.dashboard import Dashboard
                self._pages[key] = Dashboard()
            elif key == "payments":
                from LarcCompta.views.payment_list import PaymentList
                self._pages[key] = PaymentList()
            elif key == "rappels":
                from LarcCompta.views.reminders import ReminderPanel
                self._pages[key] = ReminderPanel()
            else:
                return
            self._stack.addWidget(self._pages[key])
        w = self._pages[key]
        if hasattr(w, 'refresh'):
            w.refresh()
        self._stack.setCurrentWidget(w)

    @safe_slot("MainWindow._restyle")
    def _restyle(self):
        p = theme_manager.palette
        try:
            self._sidebar.setStyleSheet(f"""
                #sidebar {{ background-color: {p.surface_variant}; border-right: 1px solid {p.border}; }}
            """)
            self._user_label.setStyleSheet(f"""
                font-size: {theme_manager.font_size(13)}px; font-weight: bold;
                color: {p.text_strong}; padding: 0 5px;
            """)
        except RuntimeError:
            pass
