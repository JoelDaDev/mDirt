from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QDropEvent, QDragEnterEvent


class DropHandler(QObject):
    def __init__(self, button, filetype, func):
        super().__init__()
        self.button = button
        self.filetype = filetype
        self.func = func
        self.png_path = None
        self.button.setAcceptDrops(True)
        self.button.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.button:
            if event.type() == QEvent.DragEnter:
                return self.dragEnter(event)
            elif event.type() == QEvent.Drop:
                return self.dropEvent(event)
        return False

    def dragEnter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(self.filetype):
                    event.acceptProposedAction()
                    return True
        event.ignore()
        return True

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(self.filetype):
                self.png_path = path
                self.func(path)
                break
        return True
