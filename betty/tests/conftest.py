"""
Integrate Betty with pytest.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Iterator, TypeVar, cast, Any
from warnings import filterwarnings

import pytest
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu, QWidget
from _pytest.logging import LogCaptureFixture
from pytestqt.qtbot import QtBot

from betty.app import AppConfiguration, App, _BackwardsCompatiblePickledFileCache
from betty.cache import Cache, FileCache
from betty.cache.file import BinaryFileCache
from betty.gui import BettyApplication
from betty.gui.app import BettyPrimaryWindow
from betty.gui.error import ErrorT
from betty.locale import DEFAULT_LOCALIZER
from betty.warnings import BettyDeprecationWarning


@pytest.fixture(autouse=True)
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


@pytest.fixture(autouse=True)
def set_logging(caplog: LogCaptureFixture) -> Iterator[None]:
    """
    Reduce noisy logging output during tests.
    """
    with caplog.at_level(logging.CRITICAL):
        yield


@pytest.fixture(scope='function')
async def app_cache(tmp_path: Path) -> Cache[Any] & FileCache:
    """
    Create a temporary cache to replace ``App.cache``.
    """
    return _BackwardsCompatiblePickledFileCache(DEFAULT_LOCALIZER, tmp_path)


@pytest.fixture
async def binary_file_cache(tmp_path: Path) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(DEFAULT_LOCALIZER, tmp_path)


@pytest.fixture(scope='session')
def qapp_cls() -> type[BettyApplication]:
    """
    Override pytest-qt's fixture of the same name to provide the Betty QApplication class.
    """
    return BettyApplication


@pytest.fixture
async def new_temporary_app(app_cache: Cache[Any] & FileCache, binary_file_cache: BinaryFileCache) -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    yield App(
        cache=app_cache,
        binary_file_cache=binary_file_cache,
    )


QObjectT = TypeVar('QObjectT', bound=QObject)
QMainWindowT = TypeVar('QMainWindowT', bound=QMainWindow)


class BettyQtBot:
    def __init__(self, qtbot: QtBot, qapp: BettyApplication):
        self.qtbot = qtbot
        self.qapp = qapp
        self.app = qapp.app

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
async def betty_qtbot(qtbot: QtBot, qapp: BettyApplication, new_temporary_app: App) -> AsyncIterator[BettyQtBot]:
    """
    Provide utilities to control Betty's Qt implementations.
    """
    async with qapp.with_app(new_temporary_app):
        yield BettyQtBot(qtbot, qapp)
