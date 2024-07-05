"""
Manage windows.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow
from typing_extensions import override

from betty.gui.locale import LocalizedObject

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable
    from betty.app import App
    from PyQt6.QtCore import QObject


class BettyMainWindow(LocalizedObject, QMainWindow):
    """
    A generic window.
    """

    #: The window's default width in pixels.
    window_width = 800

    #: The window's default height in pixels.
    window_height = 600

    def __init__(
        self,
        app: App,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(app, parent)
        self.resize(self.window_width, self.window_height)
        self.setWindowIcon(
            QIcon(
                str(
                    Path(__file__).parent
                    / "assets"
                    / "public"
                    / "static"
                    / "betty-512x512.png"
                )
            )
        )
        geometry = self.frameGeometry()
        screen = QApplication.primaryScreen()
        assert screen is not None
        geometry.moveCenter(screen.availableGeometry().center())
        self.move(geometry.topLeft())

    @override
    def _set_translatables(self) -> None:
        self.setWindowTitle(
            f"{self.window_title.localize(self._app.localizer)} - Betty"
        )

    @property
    def window_title(self) -> Localizable:
        """
        The human-readable short title of this window.
        """
        raise NotImplementedError(repr(self))

    @override
    def close(self) -> bool:
        for child in self.children():
            if isinstance(child, QMainWindow):
                child.close()
                child.deleteLater()
        return super().close()
