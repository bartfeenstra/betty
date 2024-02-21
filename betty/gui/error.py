"""
Provide error handling for the Graphical User Interface.
"""
from __future__ import annotations

import traceback
from asyncio import CancelledError
from types import TracebackType
from typing import Any, TypeVar, Generic, ParamSpec

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QWidget, QMessageBox

from betty.app import App
from betty.gui.locale import LocalizedObject

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
            '_catch_exception',
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(Exception, exception),
            Q_ARG(QObject, self._parent),
            Q_ARG(bool, self._close_parent),
        )
        return True


class Error(LocalizedObject, QMessageBox):
    def __init__(
        self,
        app: App,
        message: str,
        *args: Any,
        close_parent: bool = False,
        **kwargs: Any,
    ):
        super().__init__(app, *args, **kwargs)
        self._close_parent = close_parent
        self.setWindowTitle('{error} - Betty'.format(error=self._app.localizer._("Error")))
        self.setText(message)

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


ErrorT = TypeVar('ErrorT', bound=Error)


class ExceptionError(Error):
    def __init__(self, app: App, exception: Exception, *args: Any, **kwargs: Any):
        super().__init__(app, str(exception), *args, **kwargs)
        self.exception = exception


class UnexpectedExceptionError(ExceptionError):
    def __init__(self, app: App, exception: Exception, *args: Any, **kwargs: Any):
        super().__init__(app, exception, *args, **kwargs)
        self.setText(self._app.localizer._('An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.').format(
            report_url='https://github.com/bartfeenstra/betty/issues',
        ))
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
