"""
Integrate Betty with pytest.
"""
from __future__ import annotations

import gc
import logging
from typing import Iterator, TypeVar, cast, AsyncIterator
from warnings import filterwarnings

import pytest
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu, QWidget
from _pytest.logging import LogCaptureFixture
from pytestqt.qtbot import QtBot

from betty.app import AppConfiguration, App
from betty.gui import BettyApplication
from betty.gui.app import BettyPrimaryWindow
from betty.gui.error import ErrorT
from betty.warnings import BettyDeprecationWarning

_qapp_instance: BettyApplication | None = None


@pytest.fixture(scope='function', autouse=True)
def raise_deprecation_warnings_as_errors() -> Iterator[None]:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        'error',
        category=BettyDeprecationWarning,
    )
    yield


async def _mock_app_configuration_read(self: AppConfiguration) -> None:
    return None


@pytest.fixture(scope='session', autouse=True)
def mock_app_configuration() -> Iterator[None]:
    """
    Prevent App from loading its application configuration from the current user session, as it would pollute the tests.
    """
    AppConfiguration._read = AppConfiguration.read  # type: ignore[attr-defined]
    AppConfiguration.read = _mock_app_configuration_read  # type: ignore[assignment, method-assign]
    yield
    AppConfiguration.read = AppConfiguration._read  # type: ignore[attr-defined, method-assign]
    del AppConfiguration._read  # type: ignore[attr-defined]


@pytest.fixture(scope='function', autouse=True)
def set_logging(caplog: LogCaptureFixture) -> Iterator[None]:
    """
    Reduce noisy logging output during tests.
    """
    with caplog.at_level(logging.CRITICAL):
        yield


@pytest.fixture(scope='function')
async def qapp(qapp_args: list[str]) -> AsyncIterator[BettyApplication]:
    """
    Instantiate the BettyApplication instance that will be used by the tests.

    You can use the ``qapp`` fixture in tests which require a ``BettyApplication``
    to run, but where you don't need full ``qtbot`` functionality.

    This overrides pytest-qt's built-in qapp fixture and adds forced garbage collection after each function.
    """
    qapp_instance = cast(BettyApplication | None, BettyApplication.instance())
    if qapp_instance is None:
        global _qapp_instance
        async with App() as app:
            _qapp_instance = BettyApplication(qapp_args, app=app)
        yield _qapp_instance
    else:
        yield qapp_instance
    gc.collect()


QObjectT = TypeVar('QObjectT', bound=QObject)
QMainWindowT = TypeVar('QMainWindowT', bound=QMainWindow)


class BettyQtBot:
    def __init__(self, qtbot: QtBot, qapp: BettyApplication):
        self.qtbot = qtbot
        self.qapp = qapp

    def assert_interactive(self, item: QAction | QWidget | None) -> None:
        def _assert_interactive() -> None:
            assert item is not None
            assert item.isEnabled()
            assert item.isVisible()
        self.qtbot.wait_until(_assert_interactive)

    def navigate(self, item: QMainWindow | QMenu | QAction, attributes: list[str]) -> None:
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
                raise RuntimeError('Can only navigate to menus and actions, but attribute "%s" contains %s.' % (attribute, type(item)))

            self.navigate(item, attributes)

    def assert_window(self, window_type: type[QMainWindowT] | QMainWindowT) -> QMainWindowT:
        """
        Assert that a window is shown.
        """
        windows = []

        def _assert_window() -> None:
            nonlocal windows
            windows = [
                window
                for window
                in self.qapp.topLevelWidgets()
                if window.isVisible() and (isinstance(window, window_type) if isinstance(window_type, type) else window is window_type)
            ]
            assert len(windows) == 1
        self.qtbot.waitUntil(_assert_window)
        window = windows[0]
        if isinstance(window, BettyPrimaryWindow):
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
                for window
                in self.qapp.topLevelWidgets()
                if window.isVisible() and (isinstance(window, window_type) if isinstance(window_type, type) else window is window_type)
            ]
            assert len(windows) == 0
        self.qtbot.waitUntil(_assert_not_window)

    def assert_error(self, error_type: type[ErrorT]) -> ErrorT:
        """
        Assert that an error is shown.
        """
        widget = None

        def _assert_error_modal() -> None:
            nonlocal widget
            widget = self.qapp.activeModalWidget()
            assert isinstance(widget, error_type)
        self.qtbot.waitUntil(_assert_error_modal)
        return cast(ErrorT, widget)

    def assert_valid(self, widget: QWidget) -> None:
        """
        Assert that the given widget contains valid input.
        """
        assert widget.property('invalid') in {'false', None}

    def assert_invalid(self, widget: QWidget) -> None:
        """
        Assert that the given widget contains invalid input.
        """
        assert 'true' == widget.property('invalid')

    def mouse_click(self, widget: QWidget | None, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
        """
        Assert that the given widget can be clicked.
        """
        self.assert_interactive(widget)
        self.qtbot.mouseClick(widget, button)


@pytest.fixture
def betty_qtbot(qtbot: QtBot, qapp: BettyApplication) -> BettyQtBot:
    """
    Provide utilities to control Betty's Qt implementations.
    """
    return BettyQtBot(qtbot, qapp)
