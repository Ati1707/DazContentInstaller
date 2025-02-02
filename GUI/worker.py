from PySide6.QtCore import QObject, Signal


class Worker(QObject):
    finished = Signal()
    progress = Signal(float)

    def __init__(self, target_function, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.target_function(
            *self.args, progress_callback=self.progress.emit, **self.kwargs
            )
        finally:
            self.finished.emit()
