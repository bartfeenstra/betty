"""
Manage windows.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from typing_extensions import override

if TYPE_CHECKING:
    from betty.locale import Localizable
    from betty.app import App


class BettyMainWindow(QMainWindow):
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
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._app = app
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
