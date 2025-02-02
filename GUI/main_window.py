import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMessageBox
from helper import file_operations, updater
from GUI.gui_utilities import center_window
from GUI.tab_view import MyTabView


class App(QMainWindow):
    local_version = "v0.9.2"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Daz Content Installer {self.local_version}")
        center_window(self, 1100, 650)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Initialize and place MyTabView
        self.tab_view = MyTabView(self)
        layout.addWidget(self.tab_view)

        # Initial setup checks
        self.initial_checks()

    def initial_checks(self):
        if file_operations.create_database_folder():
            msg = QMessageBox.information(
                self,
                "Info",
                "It seems like this is your first time opening the tool!\n\n"
                "You can use the default library which will be in this folder but you can also use a different path.\n"
                "Do you want to open the config file?\n",
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No,
            )
            if msg == QMessageBox.StandardButton.Yes:
                os.startfile("config.ini")

        if updater.is_new_update_available(self.local_version):
            msg = QMessageBox.question(
                self,
                "Info",
                "A new update is available! Do you want to open the GitHub repository?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if msg == QMessageBox.StandardButton.Yes:
                updater.open_release_page()
