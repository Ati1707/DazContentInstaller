import sys

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from GUI.main_window import App
from PySide6.QtCore import Qt

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())