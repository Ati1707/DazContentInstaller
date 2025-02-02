from PySide6.QtWidgets import (
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import QThread, Signal

from GUI.gui_utilities import truncate_string
from GUI.worker import Worker
from GUI.shared_data import install_asset_list, remove_asset_list
from helper import file_operations
from content_database import delete_archive
from installer import start_installer_gui


class AssetWidget(QFrame):
    """Custom widget to represent an asset in the UI."""

    installation_finished = Signal()

    def __init__(
        self, parent, tab_name: str, asset_name: str = "", file_path: str = ""
    ):
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
            archive_imported = start_installer_gui(
                self.file_path,
                progress_callback=progress_callback,
                is_delete_archive=self.window().tab_view.is_delete_archive,
            )
            if not archive_imported:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"The archive '{self.asset_name}' was not imported. Check the log for more info.",
                    QMessageBox.StandardButton.Ok,
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
