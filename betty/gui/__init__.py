"""Provide the Graphical User Interface (GUI) for Betty Desktop."""
from __future__ import annotations

from logging import getLogger
from typing import Any, TypeVar

from PyQt6.QtCore import pyqtSlot, QObject
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QWidget

from betty.app import App
from betty.error import UserFacingError
from betty.gui.error import ExceptionError, UnexpectedExceptionError
from betty.locale import Str
from betty.serde.format import FormatRepository, FormatStr

QWidgetT = TypeVar('QWidgetT', bound=QWidget)


def get_configuration_file_filter() -> Str:
    """
    Get the Qt file filter for project configuration files.
    """
    formats = FormatRepository()
    return Str._(
        'Betty project configuration ({supported_formats})',
        supported_formats=FormatStr(formats.formats),
    )


class GuiBuilder:
    def gui_build(self) -> QWidget:
        raise NotImplementedError(repr(self))


def mark_valid(widget: QWidget) -> None:
    """
    Mark a widget as currently containing valid input.
    """
    widget.setProperty('invalid', 'false')
    widget.setStyle(widget.style())
    widget.setToolTip('')


def mark_invalid(widget: QWidget, reason: str) -> None:
    """
    Mark a widget as currently containing invalid input.
    """
    widget.setProperty('invalid', 'true')
    widget.setStyle(widget.style())
    widget.setToolTip(reason)


class BettyApplication(QApplication):
    def _is_dark_mode(self) -> bool:
        palette = self.palette()
        window_lightness = palette.color(QPalette.ColorRole.Window).lightness()
        window_text_lightness = palette.color(QPalette.ColorRole.WindowText).lightness()
        return window_lightness < window_text_lightness

    def _stylesheet(self) -> str:
        if self._is_dark_mode():
            caption_color = '#eeeeee'
        else:
            caption_color = '#333333'
        return f"""
            Caption {{
                color: {caption_color};
                font-size: 14px;
                margin-bottom: 0.3em;
            }}

            QLineEdit[invalid="true"] {{
                border: 1px solid red;
                color: red;
            }}

            QPushButton[pane-selector="true"] {{
                padding: 10px;
            }}

            LogRecord[level="50"],
            LogRecord[level="40"] {{
                color: red;
            }}

            LogRecord[level="30"] {{
                color: yellow;
            }}

            LogRecord[level="20"] {{
                color: green;
            }}

            LogRecord[level="10"],
            LogRecord[level="0"] {{
                color: white;
            }}

            _WelcomeText {{
                padding: 10px;
            }}

            _WelcomeTitle {{
                font-size: 20px;
                padding: 10px;
            }}

            _WelcomeHeading {{
                font-size: 16px;
                margin-top: 50px;
            }}

            _WelcomeAction {{
                padding: 10px;
            }}
            """

    def __init__(self, *args: Any, app: App, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.setApplicationName('Betty')
        self.setStyleSheet(self._stylesheet())
        self._app = app

    @pyqtSlot(
        Exception,
        QObject,
        bool,
    )
    def _catch_exception(
        self,
        e: Exception,
        parent: QObject,
        close_parent: bool,
    ) -> None:
        if isinstance(e, UserFacingError):
            window = ExceptionError(self._app, e, parent, close_parent=close_parent)
        else:
            getLogger(__name__).exception(e)
            window = UnexpectedExceptionError(self._app, e, parent, close_parent=close_parent)
        window.show()
