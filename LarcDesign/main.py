"""Point d'entrée LarcDesign."""
import sys
from PySide6.QtWidgets import QApplication
from larccommon.safe_slot import set_debug
from LarcDesign.views.login import LoginWindow

def main():
    set_debug(True)  # Dev: affiche les erreurs dans les slots
    app = QApplication(sys.argv)
    app.setApplicationName('LarcDesign')
    app.setOrganizationName('Arc-en-Ciel')
    app.setStyle('Fusion')
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
