import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from betty.gui.text import Text


class LogRecord(Text):
    _LEVELS = [
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        logging.NOTSET,
    ]

    _formatter = logging.Formatter()

    def __init__(self, record: logging.LogRecord, *args: Any, **kwargs: Any):
        super().__init__(self._formatter.format(record), *args, **kwargs)
        self.setProperty('level', self._normalize_level(record.levelno))

    def _normalize_level(self, record_level: int) -> int:
        for level in self._LEVELS:
            if record_level >= level:
                return level
        return logging.NOTSET


class LogRecordViewer(QWidget):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._log_record_layout = QVBoxLayout()
        self.setLayout(self._log_record_layout)

    def log(self, record: logging.LogRecord) -> None:
        self._log_record_layout.addWidget(LogRecord(record))


class _LogRecordViewerHandlerObject(QObject):
    """
    Provide a signal for logging handlers to log records to a LogRecordViewer in the main (GUI) thread.
    """
    log = pyqtSignal(logging.LogRecord)

    def __init__(self, viewer: LogRecordViewer):
        super().__init__()
        self.log.connect(  # type: ignore[call-arg]
            viewer.log,
            Qt.ConnectionType.QueuedConnection,
        )


class LogRecordViewerHandler(logging.Handler):
    log = pyqtSignal(logging.LogRecord)

    def __init__(self, viewer: LogRecordViewer):
        super().__init__()
        self._object = _LogRecordViewerHandlerObject(viewer)

    def emit(self, record: logging.LogRecord) -> None:
        self._object.log.emit(record)
