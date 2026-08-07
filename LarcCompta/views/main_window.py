"""MainWindow LarcCompta — conforme aux 6 skills design Larc."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QStackedWidget,
)

from larccommon.database import db
from larccommon.session import session
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.widgets.nav_button import NavButton
from larccommon.safe_slot import safe_slot


NAV_ITEMS = [
    ("dashboard", "Tableau de bord", "home"),
    ("payments",   "Paiements",      "check"),
    ("parents",    "Parents",         "person"),
    ("students",   "Eleves",          "school"),
    ("rappels",    "Rappels",         "schedule"),
]


class MainWindow(QWidget):

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
        p = theme_manager.palette
        s = theme_manager.font_size
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(ds.sidebar_width)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(ds.space_xs, ds.space_xl, ds.space_xs, ds.space_lg)
        sb.setSpacing(ds.space_xs)

        # User info
        user_lbl = QLabel(session.full_name or "Comptabilite")
        user_lbl.setStyleSheet(
            f"font-size: {s(ds.font_label_lg)}px; font-weight: bold; color: {p.text_strong}; "
            f"padding: 0 {ds.space_xs}px; border: none;")
        sb.addWidget(user_lbl)

        role_lbl = QLabel("Comptabilite")
        role_lbl.setStyleSheet(
            f"font-size: {s(ds.font_label_sm)}px; color: {p.text_strong}; "
            f"padding: 0 {ds.space_xs}px {ds.space_xs}px {ds.space_xs}px; border: none;")
        sb.addWidget(role_lbl)

        sep = QLabel()
        sep.setFixedHeight(ds.border_width)
        sep.setStyleSheet(f"background-color: {p.border};")
        sb.addWidget(sep)
        sb.addSpacing(ds.space_xs)

        # Navigation — NavButton standard (skill sidebar-spec K1-K25)
        self._buttons: dict[str, NavButton] = {}
        for key, label, icon_name in NAV_ITEMS:
            btn = NavButton(
                text=label,
                icon_name=icon_name,
                on_click=lambda checked=False, k=key: self._switch_to(k),
            )
            self._buttons[key] = btn
            sb.addWidget(btn)

        sb.addStretch()
        self._sidebar = sidebar
        layout.addWidget(sidebar)

        # ── Content ──
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        self._restyle()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    @safe_slot("MainWindow._switch_to")
    def _switch_to(self, key: str):
        if key == self._current_key:
            return
        self._current_key = key

        for k, btn in self._buttons.items():
            btn.setChecked(k == key)

        if key not in self._pages:
            mod_map = {
                "dashboard": ("LarcCompta.views.dashboard", "Dashboard"),
                "payments":   ("LarcCompta.views.payment_list", "PaymentList"),
                "parents":    ("LarcCompta.views.parents_list", "ParentsList"),
                "students":   ("LarcCompta.views.students_list", "StudentsList"),
                "rappels":    ("LarcCompta.views.reminders", "ReminderPanel"),
            }
            if key in mod_map:
                mod_name, cls_name = mod_map[key]
                mod = __import__(mod_name, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                self._pages[key] = cls()
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
        s = theme_manager.font_size
        try:
            self._sidebar.setStyleSheet(
                f"#sidebar {{ background-color: {p.surface_variant}; "
                f"border-right: {ds.border_width}px solid {p.border}; }}")
            self._stack.setStyleSheet(f"background: {p.background}; border: none;")
        except RuntimeError:
            pass
