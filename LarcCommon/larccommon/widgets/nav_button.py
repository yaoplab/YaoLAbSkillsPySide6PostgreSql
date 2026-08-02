"""
NavButton — Bouton de navigation standardisé (Dashboard, Recherche, Parents, etc.)

Conforme au Sous-système K du skill design-system-larc pour les boutons de
navigation latérale. Utilise M3Button(variant=TONAL) avec une icône standardisée.

Usage:
    from larccommon.widgets.nav_button import NavButton

    nav = NavButton(
        text=_("sec_main.dashboard"),
        icon_name="dashboard",
        on_click=lambda: self._set_scope('school'),
    )
    sidebar_layout.addWidget(nav)
"""

from typing import Callable, Optional

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

from larccommon.icons import icon as md3_icon
from larccommon.theme import theme_manager
from phibuilder.widgets.button import ButtonVariant, M3Button


class NavButton(M3Button):
    """Bouton de navigation avec icône standardisée.

    Hérite de M3Button(variant=TONAL) et ajoute :
    - Icône Material Design avec taille et couleur standardisées
    - Curseur 'main' par défaut (via M3Button)
    - API concise : text + icon_name + on_click
    """

    def __init__(
        self,
        text: str = "",
        icon_name: str = "",
        on_click: Optional[Callable] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(text, variant=ButtonVariant.TONAL, parent=parent)

        if icon_name:
            icon_size = theme_manager.image.icon_btn  # 18px
            self.setIcon(
                md3_icon(
                    icon_name,
                    color=theme_manager.palette.text_soft,
                    size=icon_size,
                )
            )
            self.setIconSize(QSize(icon_size, icon_size))

        if on_click:
            self.clicked.connect(on_click)
