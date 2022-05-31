import gc
import logging
from typing import Union, List, Type, Callable, Iterator, Optional, TypeVar

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu, QWidget
from pytestqt.qtbot import QtBot

from betty.app import AppConfiguration
from betty.gui import BettyApplication
from betty.gui.error import Error

_qapp_instance: Optional[BettyApplication] = None


@pytest.fixture(scope='session', autouse=True)
def mock_app_configuration() -> Iterator[None]:
    """
    Prevent App from loading its application configuration from the current user session, as it would pollute the tests.
    """

    AppConfiguration._read = AppConfiguration.read  # type: ignore
    AppConfiguration.read = lambda _: None  # type: ignore
    yield
    AppConfiguration.read = AppConfiguration._read  # type: ignore
    del AppConfiguration._read  # type: ignore


@pytest.fixture(scope='function', autouse=True)
def set_logging(caplog) -> Iterator[None]:
    with caplog.at_level(logging.CRITICAL):
        yield


@pytest.fixture(scope='function')
def qapp(qapp_args) -> Iterator[BettyApplication]:
    """
    Fixture that instantiates the BettyApplication instance that will be used by
    the tests.

    You can use the ``qapp`` fixture in tests which require a ``BettyApplication``
    to run, but where you don't need full ``qtbot`` functionality.

    This overrides pytest-qt's built-in qapp fixture and adds forced garbage collection after each function.
    """
    qapp_instance = BettyApplication.instance()
    if qapp_instance is None:
        global _qapp_instance
        _qapp_instance = BettyApplication(qapp_args)
        yield _qapp_instance
    else:
        yield qapp_instance  # type: ignore
    gc.collect()


Navigate = Callable[[Union[QMainWindow, QMenu], List[str]], None]


@pytest.fixture
def navigate(qtbot: QtBot) -> Navigate:
    def _navigate(item: Union[QMainWindow, QMenu], attributes: List[str]) -> None:
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


AssertTopLevelWidget = Callable[[Type[QWidgetT]], QWidgetT]


@pytest.fixture
def assert_top_level_widget(qapp: BettyApplication, qtbot: QtBot) -> AssertTopLevelWidget:
    def _wait_assert_top_level_widget(widget_type: Type[QWidget]) -> QWidget:
        widgets = []

        def __assert_top_level_widget():
            nonlocal widgets
            widgets = [widget for widget in qapp.topLevelWidgets() if isinstance(widget, widget_type) and widget.isVisible()]
            assert len(widgets) == 1
        qtbot.waitUntil(__assert_top_level_widget)
        widget = widgets[0]
        qtbot.addWidget(widget)
        return widget
    return _wait_assert_top_level_widget


AssertNotTopLevelWidget = Callable[[Type[QWidget]], None]


@pytest.fixture
def assert_not_top_level_widget(qapp: BettyApplication, qtbot: QtBot) -> AssertNotTopLevelWidget:
    def _assert_not_top_level_widget(widget_type: Type[QWidget]) -> None:
        widgets = [widget for widget in qapp.topLevelWidgets() if isinstance(widget, widget_type) and widget.isVisible()]
        assert len(widgets) == 0
    return _assert_not_top_level_widget


QMainWindowT = TypeVar('QMainWindowT', bound=QMainWindow)


AssertWindow = Callable[[Type[QMainWindowT]], QMainWindowT]


@pytest.fixture
def assert_window(assert_top_level_widget: AssertTopLevelWidget) -> AssertWindow:
    def _assert_window(window_type: Type[QMainWindowT]) -> QMainWindowT:
        return assert_top_level_widget(window_type)
    return _assert_window


@pytest.fixture
def assert_not_window(assert_not_top_level_widget: AssertNotTopLevelWidget):
    def _assert_window(window_type: Type[QMainWindow]) -> None:
        return assert_not_top_level_widget(window_type)
    return _assert_window


@pytest.fixture
def assert_error(qapp: BettyApplication, qtbot: QtBot):
    def _wait_assert_error(error_type: Type[Error]) -> Error:
        widget = None

        def _assert_error_modal():
            nonlocal widget
            widget = qapp.activeModalWidget()
            assert isinstance(widget, error_type)
        qtbot.waitUntil(_assert_error_modal)
        qtbot.addWidget(widget)
        return widget  # type: ignore
    return _wait_assert_error


AssertValid = Callable[[QWidget], None]


@pytest.fixture
def assert_valid() -> AssertValid:
    def _assert_valid(widget: QWidget) -> None:
        assert widget.property('invalid') in {'false', None}
    return _assert_valid


AssertInvalid = Callable[[QWidget], None]


@pytest.fixture
def assert_invalid() -> AssertInvalid:
    def _assert_invalid(widget: QWidget) -> None:
        assert 'true' == widget.property('invalid')
    return _assert_invalid
