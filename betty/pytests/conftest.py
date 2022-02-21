import gc
import json
from typing import Union, List, Type, Dict

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenu, QWidget

from betty.gui import Error, BettyApplication


@pytest.fixture(scope="function")
def qapp(qapp_args):
    """
    Fixture that instantiates the BettyApplication instance that will be used by
    the tests.

    You can use the ``qapp`` fixture in tests which require a ``BettyApplication``
    to run, but where you don't need full ``qtbot`` functionality.

    This overrides pytest-qt's built-in qapp fixture and adds forced garbage collection after each function.
    """
    app = BettyApplication.instance()
    if app is None:
        global _qapp_instance
        _qapp_instance = BettyApplication(qapp_args)
        yield _qapp_instance
    else:
        yield app  # pragma: no cover
    gc.collect()


@pytest.fixture
def minimal_dumped_app_configuration(tmpdir) -> Dict:
    output_directory_path = str(tmpdir.join('output'))
    base_url = 'https://example.com'
    return {
        'output': output_directory_path,
        'base_url': base_url,
    }


@pytest.fixture
def minimal_configuration_file_path(minimal_dumped_app_configuration, tmpdir) -> str:
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        json.dump(minimal_dumped_app_configuration, f)
    return configuration_file_path


@pytest.fixture
def navigate(qtbot):
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


@pytest.fixture
def assert_window(assert_top_level_widget):
    def _assert_window(window_type: Type[QMainWindow]) -> QMainWindow:
        return assert_top_level_widget(window_type)
    return _assert_window


@pytest.fixture
def assert_error(qapp, qtbot):
    def _assert_error(error_type: Type[Error]) -> Error:
        widget = None

        def _assert_error_modal():
            nonlocal widget
            widget = qapp.activeModalWidget()
            assert isinstance(widget, error_type)
        qtbot.waitUntil(_assert_error_modal)
        qtbot.addWidget(widget)
        return widget
    return _assert_error


@pytest.fixture
def assert_top_level_widget(qapp, qtbot):
    def _assert_top_level_widget(widget_type: Type[QWidget]) -> QWidget:
        widgets = [widget for widget in qapp.topLevelWidgets() if isinstance(widget, widget_type) and widget.isVisible()]
        assert len(widgets) == 1
        widget = widgets[0]
        qtbot.addWidget(widget)
        return widget
    return _assert_top_level_widget


@pytest.fixture
def assert_not_window(assert_not_top_level_widget):
    def _assert_window(window_type: Type[QMainWindow]) -> None:
        return assert_not_top_level_widget(window_type)
    return _assert_window


@pytest.fixture
def assert_not_top_level_widget(qapp, qtbot):
    def _assert_not_top_level_widget(widget_type: Type[QWidget]) -> None:
        widgets = [widget for widget in qapp.topLevelWidgets() if isinstance(widget, widget_type) and widget.isVisible()]
        assert len(widgets) == 0
    return _assert_not_top_level_widget


@pytest.fixture
def assert_valid():
    def _assert_valid(widget: QWidget) -> None:
        assert widget.property('invalid') in {'false', None}
    return _assert_valid


@pytest.fixture
def assert_invalid():
    def _assert_invalid(widget: QWidget) -> None:
        assert 'true' == widget.property('invalid')
    return _assert_invalid
