from __future__ import annotations

import functools
import traceback
from types import TracebackType
from typing import Callable, Any, TypeVar, Generic, TYPE_CHECKING, ParamSpec

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QWidget, QMessageBox

from betty.app import App
from betty.gui.locale import LocalizedMessageBox

if TYPE_CHECKING:
    from betty.gui import QWidgetT


T = TypeVar('T')
P = ParamSpec('P')


class _ExceptionCatcher(Generic[P, T]):
    def __init__(
            self,
            f: Callable[P, T] | None = None,
            parent: QWidget | None = None,
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
        QMetaObject.invokeMethod(
            BettyApplication.instance(),
            '_catch_exception',
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(Exception, exc_val),
            Q_ARG(QObject, self._parent),
            Q_ARG(bool, self._close_parent),
        )
        return True


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
catch_exceptions = _ExceptionCatcher


class Error(LocalizedMessageBox):
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
