from __future__ import annotations

import gc
import logging
from typing import Callable, Iterator, TypeVar, cast, Union, AsyncIterator

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu, QWidget
from _pytest.logging import LogCaptureFixture
from pytestqt.qtbot import QtBot
from typing_extensions import TypeAlias

from betty.app import AppConfiguration, App
from betty.gui import BettyApplication
from betty.gui.error import ErrorT

_qapp_instance: BettyApplication | None = None


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
    with caplog.at_level(logging.CRITICAL):
        yield


@pytest.fixture(scope='function')
async def qapp(qapp_args: list[str]) -> AsyncIterator[BettyApplication]:
    """
    Fixture that instantiates the BettyApplication instance that will be used by
    the tests.

    You can use the ``qapp`` fixture in tests which require a ``BettyApplication``
    to run, but where you don't need full ``qtbot`` functionality.

    This overrides pytest-qt's built-in qapp fixture and adds forced garbage collection after each function.
    """
    qapp_instance = cast(BettyApplication, BettyApplication.instance())
    if qapp_instance is None:
        global _qapp_instance
        async with App() as app:
            _qapp_instance = BettyApplication(qapp_args, app=app)
        yield _qapp_instance
    else:
        yield qapp_instance
    gc.collect()


Navigate: TypeAlias = Callable[['QMainWindow | QMenu', list[str]], None]


@pytest.fixture
def navigate(qtbot: QtBot) -> Navigate:
    def _navigate(item: QMainWindow | QMenu, attributes: list[str]) -> None:
        if attributes:
            attribute = attributes.pop(0)
            item = getattr(item, attribute)
            if isinstance(item, QMenu):
                qtbot.mouseClick(item, Qt.MouseButton.LeftButton)
            elif isinstance(item, QAction):
                item.trigger()
            else:
                raise RuntimeError('Can only navigate to menus and actions, but attribute "%s" contains %s.' % (attribute, type(item)))

            _navigate(item, attributes)
    return _navigate


QWidgetT = TypeVar('QWidgetT', bound=QWidget)


AssertTopLevelWidget: TypeAlias = Callable[['type[QWidgetT] | QWidgetT'], QWidgetT]


@pytest.fixture
def assert_top_level_widget(qapp: BettyApplication, qtbot: QtBot) -> AssertTopLevelWidget[QWidgetT]:
    def _wait_assert_top_level_widget(widget_type: type[QWidgetT] | QWidgetT) -> QWidgetT:
        if isinstance(widget_type, QWidget):
            assert widget_type.isVisible()

        widgets = []

        def __assert_top_level_widget() -> None:
            nonlocal widgets
            widgets = [
                widget
                for widget
                in qapp.topLevelWidgets()
                if widget.isVisible() and (isinstance(widget, widget_type) if isinstance(widget_type, type) else widget is widget_type)
            ]
            assert len(widgets) == 1
        qtbot.waitUntil(__assert_top_level_widget)
        widget = widgets[0]
        qtbot.addWidget(widget)
        return cast(QWidgetT, widget)
    return _wait_assert_top_level_widget


AssertNotTopLevelWidget: TypeAlias = Callable[['type[QWidget] | QWidgetT'], None]


@pytest.fixture
def assert_not_top_level_widget(qapp: BettyApplication, qtbot: QtBot) -> AssertNotTopLevelWidget[QWidgetT]:
    def _assert_not_top_level_widget(widget_type: type[QWidget] | QWidgetT) -> None:
        if isinstance(widget_type, QWidget):
            assert widget_type.isHidden()
        widgets = [
            widget
            for widget
            in qapp.topLevelWidgets()
            if widget.isVisible() and (isinstance(widget, widget_type) if isinstance(widget_type, type) else widget is widget_type)
        ]
        assert len(widgets) == 0
    return _assert_not_top_level_widget


QMainWindowT = TypeVar('QMainWindowT', bound=QMainWindow)


AssertWindow: TypeAlias = Callable[[Union[type[QMainWindowT], QMainWindowT]], QMainWindowT]


@pytest.fixture
def assert_window(assert_top_level_widget: AssertTopLevelWidget[QMainWindowT]) -> AssertWindow[QMainWindowT]:
    def _assert_window(window_type: type[QMainWindowT] | QMainWindowT) -> QMainWindowT:
        return assert_top_level_widget(window_type)
    return _assert_window


AssertNotWindow: TypeAlias = Callable[[Union[type[QMainWindowT], QMainWindowT]], None]


@pytest.fixture
def assert_not_window(assert_not_top_level_widget: AssertNotTopLevelWidget[QWidget]) -> AssertNotWindow[QMainWindow]:
    def _assert_not_window(window_type: type[QMainWindow] | QMainWindow) -> None:
        assert_not_top_level_widget(window_type)
    return _assert_not_window


AssertError: TypeAlias = Callable[[type[ErrorT]], ErrorT]


@pytest.fixture
def assert_error(qapp: BettyApplication, qtbot: QtBot) -> AssertError[ErrorT]:
    def _wait_assert_error(error_type: type[ErrorT]) -> ErrorT:
        widget = None

        def _assert_error_modal() -> None:
            nonlocal widget
            widget = qapp.activeModalWidget()
            assert isinstance(widget, error_type)
        qtbot.waitUntil(_assert_error_modal)
        qtbot.addWidget(widget)
        return cast(ErrorT, widget)
    return _wait_assert_error


AssertValid: TypeAlias = Callable[[QWidget], None]


@pytest.fixture
def assert_valid() -> AssertValid:
    def _assert_valid(widget: QWidget) -> None:
        assert widget.property('invalid') in {'false', None}
    return _assert_valid


AssertInvalid: TypeAlias = Callable[[QWidget], None]


@pytest.fixture
def assert_invalid() -> AssertInvalid:
    def _assert_invalid(widget: QWidget) -> None:
        assert 'true' == widget.property('invalid')
    return _assert_invalid
