import json
from typing import Union, List, Type

import pytest
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QMenu, QAction, QApplication, QWidget

from betty.gui import Error


@pytest.fixture
def minimal_configuration_file_path(tmpdir) -> str:
    configuration_file_path = tmpdir.join('betty.json')
    output_directory_path = str(tmpdir.join('output'))
    base_url = 'https://example.com'
    with open(configuration_file_path, 'w') as f:
        json.dump({
            'output': output_directory_path,
            'base_url': base_url,
        }, f)
    return configuration_file_path


@pytest.fixture
def navigate(qtbot):
    def _navigate(item: Union[QMainWindow, QMenu], attributes: List[str]) -> None:
        if attributes:
            attribute = attributes.pop(0)
            item = getattr(item, attribute)
            if isinstance(item, QMenu):
                qtbot.mouseClick(item, QtCore.Qt.LeftButton)
            elif isinstance(item, QAction):
                item.trigger()
            else:
                raise RuntimeError('Can only navigate to menus and actions, but attribute "%s" contains %s.' % (attribute, type(item)))

            navigate(qtbot)(item, attributes)
    return _navigate


@pytest.fixture
def assert_window(assert_top_level_widget):
    def _assert_window(window_type: Type[QMainWindow]) -> QMainWindow:
        return assert_top_level_widget(window_type)
    return _assert_window


@pytest.fixture
def assert_error(assert_top_level_widget):
    def _assert_error(error_type: Type[Error]) -> Error:
        return assert_top_level_widget(error_type)
    return _assert_error


@pytest.fixture
def assert_top_level_widget(qtbot):
    def _assert_top_level_widget(widget_type: Type[QWidget]) -> QWidget:
        widgets = [widget for widget in QApplication.topLevelWidgets() if isinstance(widget, widget_type)]
        assert len(widgets) == 1
        widget = widgets[0]
        qtbot.addWidget(widget)
        return widget
    return _assert_top_level_widget
