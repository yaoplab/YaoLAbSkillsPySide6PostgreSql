"""Point d'entrée LarcDesign."""
import sys
from PySide6.QtWidgets import QApplication
from LarcDesign.views.login import LoginWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('LarcDesign')
    app.setOrganizationName('Arc-en-Ciel')
    app.setStyle('Fusion')
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
