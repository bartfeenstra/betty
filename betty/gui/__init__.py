"""Provide the Graphical User Interface (GUI) for Betty Desktop."""

from __future__ import annotations

import pickle
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypeVar, Self

from PyQt6.QtCore import pyqtSlot, QObject, QCoreApplication
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QWidget

from betty.app import App
from betty.gui.error import ExceptionError, _UnexpectedExceptionError
from betty.locale import Str
from betty.serde.format import FormatRepository

QWidgetT = TypeVar("QWidgetT", bound=QWidget)


def get_configuration_file_filter() -> Str:
    """
    Get the Qt file filter for project configuration files.
    """
    formats = FormatRepository()
    return Str._(
        "Betty project configuration ({supported_formats})",
        supported_formats=" ".join(
            f"*.{extension}"
            for format in formats.formats
            for extension in format.extensions
        ),
    )


class GuiBuilder:
    def gui_build(self) -> QWidget:
        raise NotImplementedError(repr(self))


def mark_valid(widget: QWidget) -> None:
    """
    Mark a widget as currently containing valid input.
    """
    widget.setProperty("invalid", "false")
    widget.setStyle(widget.style())
    widget.setToolTip("")


def mark_invalid(widget: QWidget, reason: str) -> None:
    """
    Mark a widget as currently containing invalid input.
    """
    widget.setProperty("invalid", "true")
    widget.setStyle(widget.style())
    widget.setToolTip(reason)


class BettyApplication(QApplication):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._app: App | None = None
        self.setApplicationName("Betty")
        self.setStyleSheet(self._stylesheet())

    def _is_dark_mode(self) -> bool:
        palette = self.palette()
        window_lightness = palette.color(QPalette.ColorRole.Window).lightness()
        window_text_lightness = palette.color(QPalette.ColorRole.WindowText).lightness()
        return window_lightness < window_text_lightness

    def _stylesheet(self) -> str:
        if self._is_dark_mode():
            caption_color = "#eeeeee"
        else:
            caption_color = "#333333"
        return f"""
            Caption {{
                color: {caption_color};
                font-size: 14px;
                margin-bottom: 0.3em;
            }}

            Code {{
                font-family: monospace;
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

    @pyqtSlot(
        type,
        bytes,
        QObject,
        bool,
    )
    def _show_user_facing_error(
        self,
        error_type: type[Exception],
        pickled_error_message: bytes,
        parent: QObject,
        close_parent: bool,
    ) -> None:
        error_message = pickle.loads(pickled_error_message)
        window = ExceptionError(
            self.app,
            error_message,
            error_type,
            parent=parent,
            close_parent=close_parent,
        )
        window.show()

    @pyqtSlot(
        type,
        str,
        str,
        QObject,
        bool,
    )
    def _show_unexpected_exception(
        self,
        error_type: type[Exception],
        error_message: str,
        error_traceback: str,
        parent: QObject,
        close_parent: bool,
    ) -> None:
        window = _UnexpectedExceptionError(
            self.app,
            error_type,
            error_message,
            error_traceback,
            parent=parent,
            close_parent=close_parent,
        )
        window.show()

    @classmethod
    def instance(cls) -> Self:
        qapp = QCoreApplication.instance()
        assert isinstance(qapp, cls)
        return qapp

    @asynccontextmanager
    async def with_app(self, app: App) -> AsyncIterator[Self]:
        if self._app is not None:
            raise RuntimeError(f"This {type(self)} already has an {App}.")
        self._app = app
        yield self
        self._app = None

    @property
    def app(self) -> App:
        if self._app is None:
            raise RuntimeError(f"This {type(self)} does not have an {App} yet.")
        return self._app
