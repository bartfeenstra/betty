"""
Provide error handling for the Graphical User Interface.
"""
from __future__ import annotations

import pickle
import traceback
from asyncio import CancelledError
from types import TracebackType
from typing import TypeVar, Generic, ParamSpec

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMessageBox, QWidget

from betty.app import App
from betty.error import UserFacingError
from betty.gui.locale import LocalizedObject
from betty.locale import Str, Localizable

T = TypeVar('T')
P = ParamSpec('P')

BaseExceptionT = TypeVar('BaseExceptionT', bound=BaseException)


class ExceptionCatcher(Generic[P, T]):
    """
    Catch any exception and show an error window instead.
    """

    _SUPPRESS_EXCEPTION_TYPES = (
        CancelledError,
    )

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

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool | None:
        return self._catch(exc_type, exc_val)

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool | None:
        return self._catch(exc_type, exc_val)

    def _catch(self, exception_type: type[BaseExceptionT] | None, exception: BaseExceptionT | None) -> bool | None:
        from betty.gui import BettyApplication

        if exception_type is None or exception is None:
            return None

        if isinstance(exception, self._SUPPRESS_EXCEPTION_TYPES):
            return None

        QMetaObject.invokeMethod(
            BettyApplication.instance(),
            '_catch_error',
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(type, type(exception)),
            Q_ARG(bytes, pickle.dumps(exception if isinstance(exception, UserFacingError) else Str.plain(str(exception)))),
            Q_ARG(str, ''.join(traceback.format_exception(exception))),
            Q_ARG(QObject, self._parent),
            Q_ARG(bool, self._close_parent),
        )
        return True


class Error(LocalizedObject, QMessageBox):
    def __init__(
        self,
        parent: QObject,
        app: App,
        message: Localizable,
        *,
        close_parent: bool = False,
    ):
        super().__init__(app, parent)
        self._message = message
        if close_parent and not isinstance(parent, QWidget):
            raise ValueError('If `close_parent` is true, `parent` must be `QWidget`.')
        self._close_parent = close_parent

        standard_button_type = QMessageBox.StandardButton.Close
        self.setStandardButtons(standard_button_type)
        close_button = self.button(standard_button_type)
        assert close_button is not None
        close_button.setIcon(QIcon())
        self.setDefaultButton(standard_button_type)
        self.setEscapeButton(standard_button_type)
        close_button.clicked.connect(self.close)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._close_parent:
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.close()
        super().closeEvent(a0)

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self.setWindowTitle('{error} - Betty'.format(error=self._app.localizer._("Error")))
        self.setText(self._message.localize(self._app.localizer))


ErrorT = TypeVar('ErrorT', bound=Error)


class ExceptionError(Error):
    def __init__(
        self,
        parent: QWidget,
        app: App,
        error_type: type[BaseException],
        error_message: Localizable,
        *,
        close_parent: bool = False,
    ):
        super().__init__(parent, app, error_message, close_parent=close_parent)
        self.error_type = error_type


class UnexpectedExceptionError(ExceptionError):
    def __init__(
        self,
        parent: QWidget,
        app: App,
        error_type: type[BaseException],
        error_message: Localizable,
        error_traceback: str | None,
        *,
        close_parent: bool = False,
    ):
        super().__init__(parent, app, error_type, error_message, close_parent=close_parent)
        self.setText(self._app.localizer._('An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.').format(
            report_url='https://github.com/bartfeenstra/betty/issues',
        ))
        self.setTextFormat(Qt.TextFormat.RichText)
        if error_traceback:
            self.setDetailedText(error_traceback)
