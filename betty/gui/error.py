"""
Provide error handling for the Graphical User Interface.
"""
from __future__ import annotations

import functools
from asyncio import CancelledError
from logging import getLogger
from traceback import format_exception
from types import TracebackType
from typing import Callable, Any, TypeVar, Generic, TYPE_CHECKING, ParamSpec

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame

from betty.app import App
from betty.error import UserFacingError
from betty.gui.text import Text, Code
from betty.gui.window import BettyMainWindow
from betty.locale import Localizable, Str

if TYPE_CHECKING:
    from betty.gui import QWidgetT

T = TypeVar('T')
P = ParamSpec('P')


class _ExceptionCatcher(Generic[P, T]):
    _IGNORE_EXCEPTION_TYPES = (
        CancelledError,
    )

    def __init__(
            self,
            f: Callable[P, T] | None = None,
            parent: QObject | None = None,
            close_parent: bool = False,
            instance: QWidget | None = None,
    ):
        if f:
            functools.update_wrapper(self, f)
        self._f = f
        if close_parent and not parent:
            raise ValueError('No parent was given to close.')
        self._parent = instance if parent is None else parent
        self._close_parent = close_parent
        self._instance = instance

    def __get__(self, instance: QWidgetT | None, owner: type[QWidgetT] | None = None) -> Any:
        if instance is None:
            return self
        assert isinstance(instance, QWidget)
        return type(self)(self._f, instance, self._close_parent, instance)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if not self._f:
            raise RuntimeError('This exception catcher is not callable, but you can use it as a context manager instead using a `with` statement.')
        if self._instance is not None:
            args = (self._instance, *args)  # type: ignore[assignment]
        with self:
            return self._f(*args, **kwargs)

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool | None:
        from betty.gui import BettyApplication

        if exc_val is None:
            return None

        if isinstance(exc_val, self._IGNORE_EXCEPTION_TYPES):
            return None

        if isinstance(exc_val, UserFacingError):
            QMetaObject.invokeMethod(
                BettyApplication.instance(),
                '_show_user_facing_error',
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(type, exc_type),
                Q_ARG(Localizable, exc_val.message),
                Q_ARG(QObject, self._parent),
                Q_ARG(bool, self._close_parent),
            )
        else:
            getLogger(__name__).exception(exc_val)
            QMetaObject.invokeMethod(
                BettyApplication.instance(),
                '_show_unexpected_exception',
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(type, exc_type),
                Q_ARG(str, str(exc_val)),
                Q_ARG(str, ''.join(format_exception(exc_val))),
                Q_ARG(QObject, self._parent),
                Q_ARG(bool, self._close_parent),
            )
        return True


# Alias the class so it can be camel case while its aliased decorator can be snake case,
# allowing both to conform to the PEP rules.
catch_exceptions = _ExceptionCatcher


class Error(BettyMainWindow):
    window_height = 300
    window_width = 500

    def __init__(
        self,
        app: App,
        message: Localizable,
        *,
        parent: QObject | None = None,
        close_parent: bool = False,
    ):
        super().__init__(app, parent=parent)
        self._message_localizable = message
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
        return Str.plain('{error} - Betty', error=Str._('Error'))

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._message.setText(self._message_localizable.localize(self._app.localizer))
        self._dismiss.setText(self._app.localizer._('Close'))

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._close_parent:
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.close()
        super().closeEvent(a0)


ErrorT = TypeVar('ErrorT', bound=Error)


class ExceptionError(Error):
    def __init__(
        self,
        app: App,
        message: Localizable,
        error_type: type[BaseException],
        *,
        parent: QObject | None = None,
        close_parent: bool = False,
    ):
        super().__init__(app, message, parent=parent, close_parent=close_parent)
        self.error_type = error_type


class _UnexpectedExceptionError(ExceptionError):
    def __init__(
        self,
        app: App,
        error_type: type[Exception],
        error_message: str,
        error_traceback: str,
        *,
        parent: QObject | None = None,
        close_parent: bool = False,
    ):
        super().__init__(
            app,
            Str._(
                'An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.',
                report_url='https://github.com/bartfeenstra/betty/issues',
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
        self._exception_details.setWidget(Code(error_traceback + error_traceback + error_traceback + error_traceback))
        self._exception_details.setWidgetResizable(True)
        self._central_layout.addWidget(self._exception_details)
