from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QScrollArea,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from GUI.asset_widget import AssetWidget
from helper import file_operations
from helper.file_operations import is_file_archive
from GUI.shared_data import install_asset_list


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
            lambda state: setattr(
                self.parent().parent(),
                "is_delete_archive",
                state == self.del_archive_checkbox.checkState(),
            )
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
