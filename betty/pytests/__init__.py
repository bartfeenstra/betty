import time
from typing import Type, List, Union

import pytest
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QWidget

from betty.gui import Error


class QTest:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self._qtbot = qtbot

    def navigate(self, item: Union[QMainWindow, QMenu], attributes: List[str]) -> None:
        if attributes:
            attribute = attributes.pop(0)
            item = getattr(item, attribute)
            if isinstance(item, QMenu):
                self._qtbot.mouseClick(item, QtCore.Qt.LeftButton)
            elif isinstance(item, QAction):
                item.trigger()
            else:
                raise RuntimeError('Can only navigate to menus and actions, but attribute "%s" contains %s.' % (attribute, type(item)))

            self.navigate(item, attributes)

    def assert_window(self, window_type: Type[QMainWindow]) -> QMainWindow:
        return self._assert_top_level_widget(window_type)

    def assert_error(self, error_type: Type[Error]) -> Error:
        return self._assert_top_level_widget(error_type)

    def _assert_top_level_widget(self, widget_type: Type[QWidget]) -> QWidget:
        widgets = [widget for widget in QApplication.topLevelWidgets() if isinstance(widget, widget_type)]
        # @todo Find a way to await a widget by its type that doesn't involve waiting for a whole second.
        if 0 == len(widgets):
            time.sleep(1)
        assert 1 == len(widgets)
        return widgets[0]
