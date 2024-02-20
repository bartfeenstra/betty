"""
Manage windows.
"""
from __future__ import annotations

from os import path

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from betty.app import App
from betty.gui.locale import LocalizedObject
from betty.locale import Localizable


class BettyMainWindow(LocalizedObject, QMainWindow):
    window_width = 800
    window_height = 600

    def __init__(
        self,
        app: App,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(app, parent)
        self.resize(self.window_width, self.window_height)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        geometry = self.frameGeometry()
        screen = QApplication.primaryScreen()
        assert screen is not None
        geometry.moveCenter(screen.availableGeometry().center())
        self.move(geometry.topLeft())

    def _set_translatables(self) -> None:
        self.setWindowTitle(f'{self.window_title.localize(self._app.localizer)} - Betty')

    @property
    def window_title(self) -> Localizable:
        raise NotImplementedError(repr(self))
