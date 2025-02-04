import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from GUI.main_window import App
from helper.file_operations import create_logger

if __name__ == "__main__":
    logger = create_logger()
    icon_file = str(Path(__file__).parent.absolute() / "icons") + "\\favicon.ico"
    logger.info(icon_file)
    app = QApplication(sys.argv)
    window = App()
    window.setWindowIcon(QIcon(icon_file))
    window.show()
    sys.exit(app.exec())