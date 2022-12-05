from __future__ import annotations

import functools
import traceback
from typing import Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from betty.builtins import _

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QWidget, QMessageBox

from betty.app import App


class _ExceptionCatcher:
    def __init__(
            self,
            f: Optional[Callable] = None,
            parent: Optional[QWidget] = None,
            close_parent: bool = False,
            instance: Optional[QWidget] = None,
    ):
        if f:
            functools.update_wrapper(self, f)
        self._f = f
        if close_parent and not parent:
            raise ValueError('No parent was given to close.')
        self._parent = instance if parent is None else parent
        self._close_parent = close_parent
        self._instance = instance

    def __get__(self, instance, owner=None) -> Any:
        if instance is None:
            return self
        assert isinstance(instance, QWidget)
        return type(self)(self._f, instance, self._close_parent, instance)

    def __call__(self, *args, **kwargs):
        if not self._f:
            raise RuntimeError('This exception catcher is not callable, but you can use it as a context manager instead using a `with` statement.')
        if self._instance:
            args = (self._instance, *args)
        with self:
            return self._f(*args, **kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        from betty.gui import BettyApplication

        if exc_val is None:
            return
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


class Error(QMessageBox):
    def __init__(
            self,
            message: str,
            *args,
            close_parent: bool = False,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._close_parent = close_parent
        with App():
            self.setWindowTitle('{error} - Betty'.format(error=_("Error")))
        self.setText(message)

        standard_button = QMessageBox.StandardButton.Close
        self.setStandardButtons(standard_button)
        self.button(QMessageBox.StandardButton.Close).setIcon(QIcon())
        self.setDefaultButton(QMessageBox.StandardButton.Close)
        self.setEscapeButton(QMessageBox.StandardButton.Close)
        self.button(QMessageBox.StandardButton.Close).clicked.connect(self.close)  # type: ignore

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._close_parent:
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.close()
        super().closeEvent(event)


class ExceptionError(Error):
    def __init__(self, exception: Exception, *args, **kwargs):
        super().__init__(str(exception), *args, **kwargs)
        self.exception = exception


class UnexpectedExceptionError(ExceptionError):
    def __init__(self, exception: Exception, *args, **kwargs):
        super().__init__(exception, *args, **kwargs)
        with App():
            self.setText(_('An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.').format(report_url='https://github.com/bartfeenstra/betty/issues'))
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
