"""Panel Thèmes — visualisation des 4 palettes."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout
from phibuilder.widgets import M3Label, M3Frame, M3ScrollArea
from phibuilder.phi.scale import SpacingToken
from larccommon.theme import theme_manager

_THEMES = {'blue': 'Bleu', 'dark': 'Dark', 'sobre': 'Sobre', 'contrast': 'Contraste'}
_FIELDS = ['primary', 'on_primary', 'primary_container', 'secondary', 'on_secondary',
           'tertiary', 'error', 'surface', 'background', 'outline', 'text_strong', 'text_soft']


class ThemesPanel(M3ScrollArea):
    def __init__(self, user: dict):
        super().__init__(theme=theme_manager.phi_theme)
        phi = theme_manager.phi_theme
        sp = phi.spacing.spacing
        c = phi.colors

        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(sp(SpacingToken.LG), sp(SpacingToken.LG),
                             sp(SpacingToken.LG), sp(SpacingToken.LG))
        l.setSpacing(sp(SpacingToken.MD))
        l.addWidget(M3Label("Themes", theme=phi, style="headline_small"))

        grid = QGridLayout()
        grid.setSpacing(sp(SpacingToken.MD))

        for col, (key, label) in enumerate(_THEMES.items()):
            pal = theme_manager.get_palette(key)
            card = M3Frame(theme=phi)
            card.setStyleSheet(
                f"M3Frame {{ background: {pal.surface}; border: 1px solid {pal.outline_variant}; "
                f"border-radius: 8px; }}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            cl.setSpacing(4)
            cl.addWidget(M3Label(label, theme=phi, style="title_small"))

            for field in _FIELDS:
                val = getattr(pal, field, '#000000')
                from PySide6.QtWidgets import QHBoxLayout
                from phibuilder.widgets import M3Button
                row = QHBoxLayout()
                row.setSpacing(8)
                box = M3Button(theme=phi)
                box.setFixedSize(24, 24)
                box.setStyleSheet(f"M3Button {{ background: {val}; border: 1px solid {pal.outline}; border-radius: 4px; }}")
                box.setToolTip(f"{field}: {val}")
                row.addWidget(box)
                row.addWidget(M3Label(field.replace('_', ' '), theme=phi, style="body_small"))
                row.addStretch()
                cl.addLayout(row)

            grid.addWidget(card, 0, col)

        l.addLayout(grid)
        l.addStretch()
        self.setWidget(container)
        self.setWidgetResizable(True)
