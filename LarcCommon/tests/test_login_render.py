#!/usr/bin/env python
"""Test de rendu — BaseLoginWindow (LarcCommon).
Vérifie que la fenêtre de login est correctement construite."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from larccommon.login import BaseLoginWindow
from larccommon.theme import theme_manager
from phibuilder.widgets import M3Button, M3Label, M3TabWidget, M3TextField


def main():
    app = QApplication(sys.argv)
    theme_manager.bind(app)

    errors = []

    win = BaseLoginWindow(
        app_title="TEST",
        app_subtitle="Ceci est un test",
        intranet=True,
        google=False,
    )
    win.show()

    def check():
        w, h = win.width(), win.height()
        if w != 420:
            errors.append(f"Largeur: {w} (attendu 420)")
        if h != int(420 * 1.618033988749895):
            errors.append(f"Hauteur: {h} (attendu {int(420 * 1.618)}")

        tabs = win.findChildren(M3TabWidget)
        if not tabs:
            errors.append("M3TabWidget manquant")

        fields = win.findChildren(M3TextField)
        if len(fields) < 2:
            errors.append(f"M3TextField: {len(fields)} (attendu >= 2)")

        btns = win.findChildren(M3Button)
        if not btns:
            errors.append("M3Button manquant")

        logo = win.findChild(M3Label)
        if logo and not logo.pixmap():
            errors.append("Logo non chargé")

        if errors:
            print("\n".join(errors))
            sys.exit(1)
        else:
            print("OK BaseLoginWindow OK")

        app.quit()

    QTimer.singleShot(500, check)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
