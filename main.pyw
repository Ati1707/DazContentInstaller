import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from GUI.main_window import App

if __name__ == "__main__":
    icon_file = str(Path(__file__).parent.absolute() / "icons") + "\\gui_icon.ico"
    app = QApplication(sys.argv)
    window = App()
    window.setWindowIcon(QIcon(icon_file))
    window.show()
    sys.exit(app.exec())