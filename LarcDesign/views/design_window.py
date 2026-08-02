"""Fenêtre principale LarcDesign — navigation + panels chargés à la demande."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QSize
from phibuilder.widgets import M3Button, M3Label, M3Frame
from phibuilder.widgets.button import ButtonVariant
from phibuilder.phi.scale import SpacingToken
from larccommon.theme import theme_manager
from larccommon.icons import icon as md3_icon

_SECTIONS = [
    ('i18n', 'Langues', 'translate'),
    ('themes', 'Themes', 'tonality'),
    ('roles', 'Roles', 'person'),
    ('logs', 'Logs', 'description'),
    ('types', "Types d'evenements", 'event'),
    ('lieux', 'Lieux', 'location_on'),
]


class DesignWindow(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self._user = user
        self._panels = {}
        self._current = None
        self._btns = {}

        phi = theme_manager.phi_theme
        c = phi.colors
        sp = phi.spacing.spacing

        self.setWindowTitle(f"LarcDesign — {user.get('first_name','')} {user.get('last_name','')}")
        self.setObjectName("root")
        self.setMinimumSize(987, 610)
        self.setStyleSheet(f"QWidget#root {{ background: {c.background}; }}")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar
        side = M3Frame(theme=phi)
        side.setFixedWidth(233)
        side.setStyleSheet(f"background: {c.surface}; border-right: 1px solid {c.outline_variant};")
        sl = QVBoxLayout(side)
        sl.setContentsMargins(sp(SpacingToken.SM), sp(SpacingToken.MD),
                              sp(SpacingToken.SM), sp(SpacingToken.MD))
        sl.setSpacing(sp(SpacingToken.XS))

        sl.addWidget(M3Label("LarcDesign", theme=phi, style="headline_small"))
        sl.addWidget(M3Label(f"{user.get('first_name','')} {user.get('last_name','')}",
                             theme=phi, style="body_small"))
        sl.addSpacing(sp(SpacingToken.MD))

        for key, label, icon_name in _SECTIONS:
            btn = M3Button(label, theme=phi, variant=ButtonVariant.TEXT)
            btn.setIcon(md3_icon(icon_name, color=c.on_surface, size=theme_manager.image.icon_btn))
            btn.setIconSize(QSize(theme_manager.image.icon_btn, theme_manager.image.icon_btn))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch(k))
            self._btns[key] = btn
            sl.addWidget(btn)

        sl.addStretch()

        # Stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {c.background};")

        outer.addWidget(side)
        outer.addWidget(self._stack, 1)

        self._switch('i18n')

    def _switch(self, section: str):
        if self._current == section:
            return
        self._current = section
        c = theme_manager.phi_theme.colors
        for k, btn in self._btns.items():
            bg = c.primary_container if k == section else 'transparent'
            btn.setStyleSheet(
                f"M3Button {{ background: {bg}; text-align: left; padding-left: 8px; "
                f"border-radius: 4px; }}")
        if section not in self._panels:
            panel = self._create(section)
            if panel:
                self._panels[section] = panel
                self._stack.addWidget(panel)
        if section in self._panels:
            self._stack.setCurrentWidget(self._panels[section])

    def _create(self, section: str):
        from LarcDesign.views.panel_i18n import I18nPanel
        from LarcDesign.views.panel_themes import ThemesPanel
        from LarcDesign.views.panel_roles import RolesPanel
        from LarcDesign.views.panel_logs import LogsPanel
        from LarcDesign.views.panel_types import TypesPanel
        from LarcDesign.views.panel_lieux import LieuxPanel
        return {
            'i18n': I18nPanel,
            'themes': ThemesPanel,
            'roles': RolesPanel,
            'logs': LogsPanel,
            'types': TypesPanel,
            'lieux': LieuxPanel,
        }[section](self._user)
