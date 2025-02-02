from PySide6.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QCheckBox,
    QScrollArea,
    QWidget,
    QPushButton,
    QMessageBox,
)

from GUI.asset_widget import AssetWidget
from GUI.install_tab import InstallTab
from GUI.shared_data import remove_asset_list
from content_database import get_archives


class MyTabView(QTabWidget):
    """Custom tab view for managing install and uninstall tabs."""

    def __init__(self, parent):
        super().__init__(parent)
        self.is_delete_archive = False
        self.setup_ui()

    def setup_ui(self):
        self.install_tab = InstallTab(self)
        self.uninstall_tab = QTabWidget()
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
                widget = AssetWidget(
                    self.uninstall_scroll_content, "Uninstall", asset_name=asset[0]
                )
                self.uninstall_scroll_layout.insertWidget(0, widget)
                remove_asset_list.append(widget)
