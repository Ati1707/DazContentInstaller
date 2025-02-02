from PySide6.QtWidgets import QWidget, QApplication


def center_window_to_display(window: QWidget, width: int, height: int) -> None:
    """Centers the window on the main display"""
    screen_geometry = QApplication.primaryScreen().availableGeometry()
    x = (screen_geometry.width() - width) // 2
    y = (screen_geometry.height() - height) // 2
    window.setGeometry(x, y, width, height)


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncates strings with ellipsis"""
    return text[: max_length - 3] + "..." if len(text) > max_length else text
