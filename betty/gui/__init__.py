from __future__ import annotations

from logging import getLogger
from os import path
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSlot, QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QWidget

from betty.app import App
from betty.config import APP_CONFIGURATION_FORMATS
from betty.error import UserFacingError
from betty.gui.error import ExceptionError, UnexpectedExceptionError
from betty.gui.locale import LocalizedWindow

if TYPE_CHECKING:
    from betty.builtins import _


def get_configuration_file_filter() -> str:
    return _('Betty project configuration ({extensions})').format(extensions=' '.join(map(lambda format: f'*{format}', APP_CONFIGURATION_FORMATS)))


class GuiBuilder:
    def gui_build(self) -> QWidget:
        raise NotImplementedError


def mark_valid(widget: QWidget) -> None:
    widget.setProperty('invalid', 'false')
    widget.setStyle(widget.style())
    widget.setToolTip('')


def mark_invalid(widget: QWidget, reason: str) -> None:
    widget.setProperty('invalid', 'true')
    widget.setStyle(widget.style())
    widget.setToolTip(reason)


class BettyWindow(LocalizedWindow):
    window_width = 800
    window_height = 600

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.resize(self.window_width, self.window_height)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        geometry = self.frameGeometry()
        geometry.moveCenter(QApplication.primaryScreen().availableGeometry().center())
        self.move(geometry.topLeft())

    def _do_set_translatables(self) -> None:
        self.setWindowTitle(f'{self.title} - Betty')

    @property
    def title(self) -> str:
        raise NotImplementedError


class BettyApplication(QApplication):
    _STYLESHEET = """
        Caption {
            color: #333333;
            margin-bottom: 0.3em;
        }

        QLineEdit[invalid="true"] {
            border: 1px solid red;
            color: red;
        }

        QPushButton[pane-selector="true"] {
            padding: 10px;
        }

        LogRecord[level="50"],
        LogRecord[level="40"] {
            color: red;
        }

        LogRecord[level="30"] {
            color: yellow;
        }

        LogRecord[level="20"] {
            color: green;
        }

        LogRecord[level="10"],
        LogRecord[level="0"] {
            color: white;
        }

        _WelcomeText {
            padding: 10px;
        }

        _WelcomeTitle {
            font-size: 20px;
            padding: 10px;
        }

        _WelcomeHeading {
            font-size: 16px;
            margin-top: 50px;
        }

        _WelcomeAction {
            padding: 10px;
        }
        """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setApplicationName('Betty')
        self.setStyleSheet(self._STYLESHEET)

    @pyqtSlot(Exception, QObject, bool)
    def _catch_exception(
        self,
        e: Exception,
        parent: QObject,
        close_parent: bool,
    ) -> None:
        if isinstance(e, UserFacingError):
            window = ExceptionError(e, parent, close_parent=close_parent)
        else:
            getLogger().exception(e)
            window = UnexpectedExceptionError(e, parent, close_parent=close_parent)
        window.show()
