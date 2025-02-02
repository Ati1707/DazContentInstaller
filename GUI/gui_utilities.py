from PySide6.QtWidgets import QWidget, QApplication


def center_window(window: QWidget, width: int, height: int) -> None:
    """Centers and resizes the window to the center of the screen, adjusted for OS scaling."""
    screen = QApplication.primaryScreen()
    # Get the OS scaling factor
    scaling_factor = screen.devicePixelRatio()
    # Scale the width and height
    scaled_width = int(width / scaling_factor)
    scaled_height = int(height / scaling_factor)
    # Resize the window with scaled dimensions
    window.resize(scaled_width, scaled_height)
    # Center the window
    available_geometry = screen.availableGeometry()
    frame = window.frameGeometry()
    frame.moveCenter(available_geometry.center())
    window.move(frame.topLeft())


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncates strings with ellipsis"""
    return text[: max_length - 3] + "..." if len(text) > max_length else text
