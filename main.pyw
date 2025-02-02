import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QScrollArea,
                               QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QProgressBar,
                               QLabel, QFrame, QFileDialog, QMessageBox)

from content_database import get_archives, delete_archive
from helper import file_operations, updater
from helper.file_operations import is_file_archive
from installer import start_installer_gui

install_asset_list = []
remove_asset_list = []


def center_window_to_display(window: QWidget, width: int, height: int) -> None:
    """Centers the window on the main display."""
    screen_geometry = QApplication.primaryScreen().availableGeometry()
    x = (screen_geometry.width() - width) // 2
    y = (screen_geometry.height() - height) // 2
    window.setGeometry(x, y, width, height)


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncates a string with ellipsis if it exceeds the max length."""
    return text[:max_length - 3] + '...' if len(text) > max_length else text


class Worker(QObject):
    finished = Signal()
    progress = Signal(float)

    def __init__(self, target_function, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.target_function(*self.args, progress_callback=self.progress.emit, **self.kwargs)
        self.finished.emit()

class InstallTab(QWidget):
    """Custom widget for the Install tab with drag-and-drop support."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        self.setAcceptDrops(True)  # Enable drops for this widget

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Check All checkbox
        self.check_install = QCheckBox("Check all")
        self.check_install.stateChanged.connect(self.toggle_install_checkboxes)
        layout.addWidget(self.check_install)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.addStretch()
        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area)

        # Bottom buttons
        bottom_frame = QWidget()
        bottom_layout = QHBoxLayout(bottom_frame)

        self.del_archive_checkbox = QCheckBox("Delete Archive after Installation")
        self.del_archive_checkbox.stateChanged.connect(
            lambda state: setattr(self.parent().parent(), 'is_delete_archive', state == self.del_archive_checkbox.checkState())
        )
        bottom_layout.addWidget(self.del_archive_checkbox)

        self.remove_button = QPushButton("Remove selected")
        self.remove_button.clicked.connect(self.remove_selected)
        bottom_layout.addWidget(self.remove_button)

        self.add_asset_button = QPushButton("Add Asset")
        self.add_asset_button.clicked.connect(self.select_file)
        bottom_layout.addWidget(self.add_asset_button)

        self.install_button = QPushButton("Install selected")
        self.install_button.clicked.connect(self.install_assets)
        bottom_layout.addWidget(self.install_button)

        layout.addWidget(bottom_frame)

    @staticmethod
    def toggle_install_checkboxes(state):
        checked = state == 2  # 2 corresponds to Qt.Checked
        for asset in install_asset_list:
            asset.checkbox.setChecked(checked)

    def add_asset_widget(self, asset_name: str, asset_path: str):
        """Adds a new asset widget to the install scroll area."""
        asset = AssetWidget(self.scroll_content, "Install", asset_name, asset_path)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, asset)
        install_asset_list.append(asset)

    def select_file(self):
        """Prompts user to select a file and adds an asset widget."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Asset File")
        if file_path:
            file_name = Path(file_path).name
            if is_file_archive(file_name):
                asset_name = file_operations.get_file_name_without_extension(file_name)
                self.add_asset_widget(asset_name, file_path)
            else:
                QMessageBox.information(self, "Info", "The File is not an archive")

    @staticmethod
    def remove_selected():
        for asset in install_asset_list.copy():
            if asset.checkbox.isChecked():
                asset.remove_from_view()

    def install_assets(self):
        msg = QMessageBox.question(
            self,
            "Install?",
            "Do you want to install the selected assets?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if msg == QMessageBox.StandardButton.Yes:
            self.install_button.setEnabled(False)
            for asset in install_asset_list.copy():
                if asset.checkbox.isChecked():
                    asset.install_asset()
            self.install_button.setEnabled(True)
            self.check_install.setChecked(False)

    def dragEnterEvent(self, event):
        """Accept drag events if the dragged content contains files."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle dropped files."""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file_path in files:
            if is_file_archive(file_path):
                file_name = Path(file_path).name
                asset_name = file_operations.get_file_name_without_extension(file_name)
                self.add_asset_widget(asset_name, file_path)
            else:
                QMessageBox.information(self, "Info", "The File is not an archive")
        event.acceptProposedAction()

class AssetWidget(QFrame):
    """Custom widget to represent an asset in the UI."""
    installation_finished = Signal()

    def __init__(self, parent, tab_name: str, asset_name: str = "", file_path: str = ""):
        super().__init__(parent)
        self.asset_name = asset_name
        self.file_path = file_path
        self.file_size = file_operations.get_file_size(self.file_path)
        self.tab_name = tab_name
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("AssetWidget { border: 1px solid #4A90E2; }")

        layout = QHBoxLayout(self)
        self.checkbox = QCheckBox(truncate_string(self.asset_name))
        self.checkbox.setToolTip(self.asset_name)
        layout.addWidget(self.checkbox)

        if tab_name == "Install":
            self._create_install_widgets(layout)
        else:
            self._create_uninstall_widgets(layout)

    def _create_install_widgets(self, layout):
        self.progressbar = QProgressBar()
        self.progressbar.setValue(0)
        layout.addWidget(self.progressbar)

        self.label = QLabel(self.file_size)
        layout.addWidget(self.label)

        self.button = QPushButton("Install")
        self.button.clicked.connect(self.install_asset)
        layout.addWidget(self.button)

    def _create_uninstall_widgets(self, layout):
        self.button = QPushButton("Remove")
        self.button.clicked.connect(self.remove_asset)
        layout.addWidget(self.button)

    def remove_from_view(self):
        """Removes the asset widget from the UI."""
        if self in install_asset_list:
            install_asset_list.remove(self)
        self.setParent(None)
        self.deleteLater()

    def install_asset(self):
        print("Start install")
        self.button.setEnabled(False)
        self.thread = QThread()  # Store reference
        self.worker = Worker(self._perform_installation)
        self.worker.progress.connect(self.progressbar.setValue)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.started.connect(self.worker.run)
        self.thread.start()
        self.worker.finished.connect(self.remove_from_view)

    def _perform_installation(self, progress_callback):
        try:
            print("Finish install")  # This should be before running the installer
            archive_imported = start_installer_gui(
                self.file_path,
                progress_callback=progress_callback,
                is_delete_archive=self.window().tab_view.is_delete_archive
            )
            if not archive_imported:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"The archive '{self.asset_name}' was not imported. Check the log for more info."
                )
            self.remove_from_view()
        except Exception as e:
            print(f"Error during installation: {e}")
        finally:
            self.installation_finished.emit()

    def remove_asset(self):
        """Removes the asset from the database and the uninstall list."""
        delete_archive(self.asset_name)
        if self in remove_asset_list:
            remove_asset_list.remove(self)
        self.remove_from_view()


class MyTabView(QTabWidget):
    """Custom tab view for managing install and uninstall tabs."""

    def __init__(self, parent):
        super().__init__(parent)
        self.is_delete_archive = False
        self.setup_ui()

    def setup_ui(self):
        self.install_tab = InstallTab(self)
        self.uninstall_tab = QWidget()
        self.addTab(self.install_tab, "Install")
        self.addTab(self.uninstall_tab, "Uninstall")

        self.setup_uninstall_tab()
        self.currentChanged.connect(self.refresh_tab)

    def setup_uninstall_tab(self):
        layout = QVBoxLayout(self.uninstall_tab)

        # Check All checkbox
        self.check_uninstall = QCheckBox("Check all")
        self.check_uninstall.stateChanged.connect(self.toggle_uninstall_checkboxes)
        layout.addWidget(self.check_uninstall)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.uninstall_scroll_content = QWidget()
        self.uninstall_scroll_layout = QVBoxLayout(self.uninstall_scroll_content)
        self.uninstall_scroll_layout.addStretch()
        scroll_area.setWidget(self.uninstall_scroll_content)
        layout.addWidget(scroll_area)

        # Remove button
        self.uninstall_button = QPushButton("Remove selected")
        self.uninstall_button.clicked.connect(self.remove_assets)
        layout.addWidget(self.uninstall_button)

    @staticmethod
    def toggle_uninstall_checkboxes(state):
        checked = state == 2  # 2 corresponds to Qt.Checked
        for asset in remove_asset_list:
            asset.checkbox.setChecked(checked)

    def remove_assets(self):
        msg = QMessageBox.question(
            self,
            "Remove?",
            "Do you want to remove the selected assets?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if msg == QMessageBox.StandardButton.Yes:
            for asset in remove_asset_list.copy():
                if asset.checkbox.isChecked():
                    asset.remove_asset()

    def refresh_tab(self, index):
        if self.tabText(index) == "Uninstall":
            # Clear existing widgets
            while self.uninstall_scroll_layout.count() > 1:
                item = self.uninstall_scroll_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Add new assets
            assets = get_archives()
            remove_asset_list.clear()
            for asset in assets:
                widget = AssetWidget(self.uninstall_scroll_content, "Uninstall", asset_name=asset[0])
                self.uninstall_scroll_layout.insertWidget(0, widget)
                remove_asset_list.append(widget)


class App(QMainWindow):
    local_version = "v0.9.1"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Daz Content Installer {self.local_version}")
        self.resize(1100, 650)
        center_window_to_display(self, 1100, 650)

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
                QMessageBox.StandardButton.No
            )
            if msg == QMessageBox.StandardButton.Yes:
                os.startfile("config.ini")

        if updater.is_new_update_available(self.local_version):
            msg = QMessageBox.question(
                self,
                "Info",
                "A new update is available! Do you want to open the GitHub repository?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if msg == QMessageBox.StandardButton.Yes:
                updater.open_release_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())