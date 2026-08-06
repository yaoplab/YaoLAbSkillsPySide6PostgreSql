"""MainWindow LarcRH — sidebar 4 catégories + grille photos."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QScrollArea, QStackedWidget, QSizePolicy,
)

from larccommon.database import db
from larccommon.session import session
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon
from larccommon.safe_slot import safe_slot


CATEGORIES = [
    ('college',   'Collège / Lycée',     1001, 2000, 'school'),
    ('primaire',  'Primaire',            2001, 3000, 'school'),
    ('maternelle','Maternelle',          3001, 4000, 'child_care'),
    ('staff',     'Staff non enseignant', 4001, 5000, 'person'),
]


class _CategoryButton(QPushButton):
    """Bouton de catégorie avec icône + compteur."""

    def __init__(self, key: str, label: str, icon_name: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._label = label
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(theme_manager.image.theme_btn)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        if icon_name:
            try:
                self.setIcon(md3_icon(icon_name, color=theme_manager.palette.text_strong, size=18))
            except Exception:
                pass

        self._update_text(0)

    def _update_text(self, count: int):
        self.setText(f"{self._label} ({count})")

    @property
    def key(self) -> str:
        return self._key


class MainWindow(QWidget):

    SIDEBAR_WIDTH = 233

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LarcRH — Ressources Humaines")
        self._current_key: str | None = None
        self._grids: dict[str, QWidget] = {}

        self._setup_ui()
        self._load_counts()
        ds.theme_changed.connect(self._restyle)

        QTimer.singleShot(100, self._select_first)

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

        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(ds.space_xs, theme_manager.image.theme_btn,
                                     ds.space_xs, ds.space_lg)
        sb_layout.setSpacing(ds.space_xs)

        # User info
        self._user_label = QLabel(session.full_name or "Utilisateur")
        self._user_label.setStyleSheet(f"""
            font-size: {theme_manager.font_size(13)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
            padding: 0 5px;
        """)
        sb_layout.addWidget(self._user_label)

        role_label = QLabel("Ressources Humaines")
        role_label.setStyleSheet(f"""
            font-size: {theme_manager.font_size(10)}px;
            color: {theme_manager.palette.text_strong};
            padding: 0 5px 8px 5px;
        """)
        sb_layout.addWidget(role_label)

        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {theme_manager.palette.border};")
        sb_layout.addWidget(sep)
        sb_layout.addSpacing(8)

        # Category buttons
        self._buttons: dict[str, _CategoryButton] = {}
        for key, label, _lo, _hi, icon_name in CATEGORIES:
            btn = _CategoryButton(key, label, icon_name)
            btn.clicked.connect(lambda checked, k=key: self._switch_to(k))
            self._buttons[key] = btn
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        layout.addWidget(sidebar)
        self._sidebar = sidebar

        # ── Content ──
        content = QWidget()
        content.setStyleSheet(f"background-color: {theme_manager.palette.background};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {theme_manager.palette.surface};
            border-bottom: 1px solid {theme_manager.palette.border};
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(ds.space_md, ds.space_sm, ds.space_md, ds.space_sm)

        self._section_title = QLabel()
        self._section_title.setStyleSheet(f"""
            font-size: {theme_manager.font_size(16)}px; font-weight: bold;
            color: {theme_manager.palette.text_strong};
        """)
        hl.addWidget(self._section_title)
        hl.addStretch()

        add_btn = QPushButton("+ Ajouter")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme_manager.palette.primary}; color: white;
                border: none; border-radius: {ds.radius_sm}px;
                font-size: {theme_manager.font_size(12)}px; font-weight: bold;
                padding: {ds.space_xs}px {ds.space_md}px;
            }}
            QPushButton:hover {{ background: {theme_manager.palette.primary}; }}
        """)
        add_btn.clicked.connect(self._on_add)
        self._add_btn = add_btn
        hl.addWidget(add_btn)

        cl.addWidget(header)

        # Stack
        self._stack = QStackedWidget()
        cl.addWidget(self._stack, 1)

        layout.addWidget(content, 1)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _load_counts(self):
        conn = db.server_conn
        if not conn:
            QTimer.singleShot(1000, self._load_counts)
            return
        try:
            cur = conn.cursor()
            for key, _label, lo, hi, _icon in CATEGORIES:
                if key == 'staff':
                    cur.execute(
                        "SELECT COUNT(*) FROM larcauth_staff "
                        "WHERE aecuser_ptr_id BETWEEN %s AND %s AND enabled = true",
                        (lo, hi)
                    )
                else:
                    cur.execute(
                        "SELECT COUNT(*) FROM larcauth_aecuser a "
                        "JOIN larcauth_teachadm t ON t.aecuser_ptr_id = a.id "
                        "WHERE a.id BETWEEN %s AND %s AND t.enabled = true",
                        (lo, hi)
                    )
                cnt = cur.fetchone()[0]
                btn = self._buttons.get(key)
                if btn:
                    btn._update_text(cnt)
        except Exception:
            pass

    def _select_first(self):
        for key, _label, _lo, _hi, _icon in CATEGORIES:
            if key in self._buttons:
                self._switch_to(key)
                break

    @safe_slot("MainWindow._switch_to")
    def _switch_to(self, key: str):
        if key == self._current_key:
            return
        self._current_key = key

        for btn in self._buttons.values():
            btn.setChecked(False)
        btn = self._buttons.get(key)
        if btn:
            btn.setChecked(True)
            self._section_title.setText(btn._label)

        if key not in self._grids:
            from LarcRH.views.staff_grid import StaffGrid
            from PySide6.QtWidgets import QScrollArea
            cat = next((c for c in CATEGORIES if c[0] == key), None)
            grid = StaffGrid(key, cat[2], cat[3], is_staff=(key == 'staff'))
            # Wrapper dans un QScrollArea pour le scroll vertical
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setWidget(grid)
            scroll.setStyleSheet(f"background: {theme_manager.palette.background}; border: none;")
            self._grids[key] = scroll
            self._stack.addWidget(scroll)

        self._stack.setCurrentWidget(self._grids[key])

    @safe_slot("MainWindow._on_add")
    def _on_add(self):
        from LarcRH.views.staff_form import StaffFormDialog
        cat = next((c for c in CATEGORIES if c[0] == self._current_key), None)
        lo = cat[2] if cat else 1001
        hi = cat[3] if cat else 5000
        dlg = StaffFormDialog(lo, hi, parent=self)
        if dlg.exec():
            self._load_counts()
            if self._current_key in self._grids:
                scroll = self._grids[self._current_key]
                scroll.widget().refresh()

    @safe_slot("MainWindow._restyle")
    def _restyle(self):
        p = theme_manager.palette
        try:
            self._sidebar.setStyleSheet(f"""
                #sidebar {{
                    background-color: {p.surface_variant};
                    border-right: 1px solid {p.border};
                }}
            """)
            self._user_label.setStyleSheet(f"""
                font-size: {theme_manager.font_size(13)}px; font-weight: bold;
                color: {p.text_strong};
                padding: 0 5px;
            """)
            self._section_title.setStyleSheet(f"""
                font-size: {theme_manager.font_size(16)}px; font-weight: bold;
                color: {p.text_strong};
            """)
        except RuntimeError:
            pass
