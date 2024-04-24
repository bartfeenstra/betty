"""
Provide error handling for the Graphical User Interface.
"""

from __future__ import annotations

import pickle
from asyncio import CancelledError
from logging import getLogger
from traceback import format_exception
from types import TracebackType
from typing import TypeVar, Generic, ParamSpec

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QFrame,
)

from betty.app import App
from betty.error import UserFacingError
from betty.gui.text import Code, Text
from betty.gui.window import BettyMainWindow
from betty.locale import Str, Localizable

T = TypeVar("T")
P = ParamSpec("P")

BaseExceptionT = TypeVar("BaseExceptionT", bound=BaseException)


class ExceptionCatcher(Generic[P, T]):
    """
    Catch any exception and show an error window instead.
    """

    _SUPPRESS_EXCEPTION_TYPES = (CancelledError,)

    def __init__(
        self,
        parent: QObject,
        *,
        close_parent: bool = False,
    ):
        self._parent = parent
        self._close_parent = close_parent

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._catch(exc_type, exc_val)

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self._catch(exc_type, exc_val)

    def _catch(
        self,
        exception_type: type[BaseExceptionT] | None,
        exception: BaseExceptionT | None,
    ) -> bool | None:
        from betty.gui import BettyApplication

        if exception_type is None or exception is None:
            return None

        if isinstance(exception, self._SUPPRESS_EXCEPTION_TYPES):
            return None

        if isinstance(exception, UserFacingError):
            QMetaObject.invokeMethod(
                BettyApplication.instance(),
                "_show_user_facing_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(type, exception_type),
                Q_ARG(bytes, pickle.dumps(exception)),
                Q_ARG(QObject, self._parent),
                Q_ARG(bool, self._close_parent),
            )
        else:
            getLogger(__name__).exception(exception)
            QMetaObject.invokeMethod(
                BettyApplication.instance(),
                "_show_unexpected_exception",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(type, exception_type),
                Q_ARG(str, str(exception)),
                Q_ARG(str, "".join(format_exception(exception))),
                Q_ARG(QObject, self._parent),
                Q_ARG(bool, self._close_parent),
            )
        return True


class Error(BettyMainWindow):
    window_height = 300
    window_width = 500

    def __init__(
        self,
        app: App,
        message: Localizable,
        *,
        parent: QObject,
        close_parent: bool = False,
    ):
        super().__init__(app, parent=parent)
        self._message_localizable = message
        if close_parent and not isinstance(parent, QWidget):
            raise ValueError("If `close_parent` is true, `parent` must be `QWidget`.")
        self._close_parent = close_parent
        self.setWindowModality(Qt.WindowModality.WindowModal)

        central_widget = QWidget()
        self._central_layout = QVBoxLayout()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._message = Text()
        self._central_layout.addWidget(self._message)

        self._controls = QHBoxLayout()
        self._central_layout.addLayout(self._controls)

        self._dismiss = QPushButton()
        self._dismiss.released.connect(self.close)
        self._controls.addWidget(self._dismiss)

    @property
    def window_title(self) -> Localizable:
        return Str.plain("{error} - Betty", error=Str._("Error"))

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._message.setText(self._message_localizable.localize(self._app.localizer))
        self._dismiss.setText(self._app.localizer._("Close"))

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._close_parent:
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.close()
        super().closeEvent(a0)


ErrorT = TypeVar("ErrorT", bound=Error)


class ExceptionError(Error):
    def __init__(
        self,
        app: App,
        message: Localizable,
        error_type: type[BaseException],
        *,
        parent: QObject,
        close_parent: bool = False,
    ):
        super().__init__(app, message, parent=parent, close_parent=close_parent)
        self.error_type = error_type


ExceptionErrorT = TypeVar("ExceptionErrorT", bound=ExceptionError)


class _UnexpectedExceptionError(ExceptionError):
    def __init__(
        self,
        app: App,
        error_type: type[Exception],
        error_message: str,
        error_traceback: str,
        *,
        parent: QObject,
        close_parent: bool = False,
    ):
        super().__init__(
            app,
            Str._(
                'An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.',
                report_url="https://github.com/bartfeenstra/betty/issues",
            ),
            error_type,
            parent=parent,
            close_parent=close_parent,
        )

        if error_message:
            self._exception_message = Code(error_message)
            self._central_layout.addWidget(self._exception_message)

        self._exception_details = QScrollArea()
        self._exception_details.setFrameShape(QFrame.Shape.NoFrame)
        self._exception_details.setWidget(
            Code(error_traceback + error_traceback + error_traceback + error_traceback)
        )
        self._exception_details.setWidgetResizable(True)
        self._central_layout.addWidget(self._exception_details)
