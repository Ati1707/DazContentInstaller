import sys
from PySide6.QtWidgets import QApplication
from GUI.main_window import App

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())