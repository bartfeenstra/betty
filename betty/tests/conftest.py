"""
Integrate Betty with pytest.
"""

from __future__ import annotations

import logging
from typing import TypeVar, cast, TypeGuard, TYPE_CHECKING
from warnings import filterwarnings

import pytest
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QMenu,
    QWidget,
    QLineEdit,
    QTextEdit,
    QAbstractButton,
    QGroupBox,
)

from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.gui import BettyApplication
from betty.gui.error import ExceptionError
from betty.locale import DEFAULT_LOCALIZER
from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from pytestqt.qtbot import QtBot
    from pathlib import Path
    from collections.abc import AsyncIterator, Iterator


@pytest.fixture(autouse=True)
def _raise_deprecation_warnings_as_errors() -> None:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        "error",
        category=BettyDeprecationWarning,
    )


# @todo Do we need this, and when and how?
@pytest.fixture(autouse=True)
def _set_logging(caplog: LogCaptureFixture) -> Iterator[None]:
    """
    Reduce noisy logging output during tests.
    """
    with caplog.at_level(logging.CRITICAL):
        yield


@pytest.fixture()
async def binary_file_cache(tmp_path: Path) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(DEFAULT_LOCALIZER, tmp_path)


@pytest.fixture(scope="session")
def qapp_cls() -> type[BettyApplication]:
    """
    Override pytest-qt's fixture of the same name to provide the Betty QApplication class.
    """
    return BettyApplication


@pytest.fixture()
async def new_temporary_app() -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    async with App.new_temporary() as app, app:
        yield app


QObjectT = TypeVar("QObjectT", bound=QObject)
QMainWindowT = TypeVar("QMainWindowT", bound=QMainWindow)


class BettyQtBot:
    def __init__(self, qtbot: QtBot, qapp: BettyApplication):
        self.qtbot = qtbot
        self.qapp = qapp
        self.app = qapp.app

    def _is_interactive(self, item: QAction | QWidget | None) -> bool:
        if item is None:
            return False
        if not item.isEnabled():
            return False
        if not item.isVisible():
            return False
        return True

    def assert_interactive(
        self, item: QAction | QWidget | None
    ) -> TypeGuard[QAction | QWidget]:
        self.qtbot.wait_until(lambda: self._is_interactive(item))
        return True

    def assert_not_interactive(self, item: QAction | QWidget | None) -> None:
        self.qtbot.wait_until(lambda: not self._is_interactive(item))

    def navigate(
        self, item: QMainWindow | QMenu | QAction, attributes: list[str]
    ) -> None:
        """
        Navigate a window's menus and actions.
        """
        if attributes:
            attribute = attributes.pop(0)
            item = getattr(item, attribute)
            if isinstance(item, QMenu):
                self.mouse_click(item)
            elif isinstance(item, QAction):
                self.assert_interactive(item)
                item.trigger()
            else:
                raise RuntimeError(
                    'Can only navigate to menus and actions, but attribute "%s" contains %s.'
                    % (attribute, type(item))
                )

            self.navigate(item, attributes)

    def assert_window(
        self, window_type: type[QMainWindowT] | QMainWindowT
    ) -> QMainWindowT:
        """
        Assert that a window is shown.
        """
        windows = []

        def _assert_window() -> None:
            nonlocal windows
            windows = [
                window
                for window in self.qapp.topLevelWidgets()
                if window.isVisible()
                and (
                    isinstance(window, window_type)
                    if isinstance(window_type, type)
                    else window is window_type
                )
            ]
            assert len(windows) == 1

        self.qtbot.waitUntil(_assert_window)
        window = windows[0]
        if isinstance(window, QMainWindow):
            self.qtbot.addWidget(window)
        return cast(QMainWindowT, window)

    def assert_not_window(self, window_type: type[QMainWindow] | QMainWindow) -> None:
        """
        Assert that a window is not shown.
        """

        def _assert_not_window() -> None:
            if isinstance(window_type, QMainWindow):
                assert not window_type.isVisible()
            windows = [
                window
                for window in self.qapp.topLevelWidgets()
                if window.isVisible()
                and (
                    isinstance(window, window_type)
                    if isinstance(window_type, type)
                    else window is window_type
                )
            ]
            assert len(windows) == 0

        self.qtbot.waitUntil(_assert_not_window)

    def assert_exception_error(
        self,
        *,
        contained_error_type: type[BaseException] | None = None,
    ) -> ExceptionError:
        """
        Assert that an exception error is shown.
        """
        exception_error: ExceptionError | None = None

        def _assert_error_modal() -> None:
            nonlocal exception_error
            widget = self.qapp.activeModalWidget()
            assert isinstance(
                widget, ExceptionError
            ), f"Failed asserting that an error window of type {ExceptionError} is shown. Instead, {type(widget)} was found."
            if contained_error_type is not None:
                assert issubclass(
                    widget.error_type, contained_error_type
                ), f"Failed asserting that an error window is shown for a raised error of type {contained_error_type}. Instead the following error was raised:\n{widget.error_type}\n{widget._message.text()}"
            exception_error = widget

        self.qtbot.waitUntil(_assert_error_modal)
        assert exception_error is not None
        return exception_error

    def assert_valid(self, widget: QWidget) -> None:
        """
        Assert that the given widget contains valid input.
        """
        assert widget.property("invalid") in {"false", None}

    def assert_invalid(self, widget: QWidget) -> None:
        """
        Assert that the given widget contains invalid input.
        """
        assert widget.property("invalid") == "true"

    def mouse_click(
        self, widget: QWidget | None, button: Qt.MouseButton = Qt.MouseButton.LeftButton
    ) -> None:
        """
        Assert that the given widget can be clicked.
        """
        self.assert_interactive(widget)
        self.qtbot.mouseClick(widget, button)

    def set_text(self, widget: QLineEdit | QTextEdit | None, text: str) -> None:
        """
        Set (input) text for a form widget.
        """
        if self.assert_interactive(widget):
            widget.setText(text)

    def set_checked(
        self, widget: QAbstractButton | QGroupBox | None, checked: bool
    ) -> None:
        """
        Check or uncheck a form widget.
        """
        if self.assert_interactive(widget):
            widget.setChecked(checked)


@pytest.fixture()
async def betty_qtbot(
    qtbot: QtBot, qapp: BettyApplication, new_temporary_app: App
) -> AsyncIterator[BettyQtBot]:
    """
    Provide utilities to control Betty's Qt implementations.
    """
    async with qapp.with_app(new_temporary_app):
        yield BettyQtBot(qtbot, qapp)
