"""
Integrate Betty's Graphical User Interface with the Serve API.
"""

from __future__ import annotations

import asyncio
from typing import final, TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton
from typing_extensions import override

from betty import documentation, serve
from betty.asyncio import wait_to_thread
from betty.extension import demo
from betty.gui.error import ExceptionCatcher
from betty.gui.text import Text
from betty.gui.window import BettyMainWindow
from betty.locale import Str, Localizable

if TYPE_CHECKING:
    from betty.serve import Server
    from betty.app import App


class _ServeThread(QThread):
    server_started = pyqtSignal()

    def __init__(
        self,
        server: Server,
        serve_window: _ServeWindow,
    ):
        super().__init__(serve_window)
        self._server = server
        self._serve_window = serve_window

    @override
    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        with ExceptionCatcher(self._serve_window, close_parent=True):
            await self._server.start()
            self.server_started.emit()
            await self._server.show()

    def stop(self) -> None:
        wait_to_thread(self._server.stop())


class _ServeWindow(BettyMainWindow):
    server_started = pyqtSignal()
    window_width = 500
    window_height = 100

    def __init__(
        self,
        app: App,
        *,
        parent: QWidget | None = None,
    ):
        super().__init__(app, parent=parent)
        self.server_started.connect(self._server_started)
        self._server = self._new_server()
        self._serve_thread = _ServeThread(self._server, self)

        self._central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._loading_instruction = Text(self._app.localizer._("Loading..."))
        self._loading_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(self._loading_instruction)

    def _new_server(self) -> Server:
        raise NotImplementedError(repr(self))

    def _build_instruction(self) -> str:
        raise NotImplementedError(repr(self))

    @override
    def show(self) -> None:
        super().show()
        # Explicitly activate this window in case it existed and was shown before, but requested again.
        self.activateWindow()
        self._start()

    def _start(self) -> None:
        self._serve_thread.server_started.connect(self.server_started)
        self._serve_thread.start()

    def _server_started(self) -> None:
        self._loading_instruction.close()

        instance_instruction = Text(self._build_instruction())
        instance_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(instance_instruction)

        general_instruction = Text(
            self._app.localizer._("Keep this window open to keep the site running.")
        )
        general_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(general_instruction)

        stop_server_button = QPushButton(self._app.localizer._("Stop the site"), self)
        stop_server_button.released.connect(
            self.close,
        )
        self._central_layout.addWidget(stop_server_button)

    @override
    def close(self) -> bool:
        self._stop()
        return super().close()

    def _stop(self) -> None:
        self._serve_thread.stop()


@final
class ServeProjectWindow(_ServeWindow):
    """
    A window to control the server for the current project.
    """

    @override
    def _new_server(self) -> Server:
        return serve.BuiltinAppServer(self._app)

    @override
    @property
    def window_title(self) -> Localizable:
        return Str._("Serving your site...")

    @override
    def _build_instruction(self) -> str:
        return self._app.localizer._(
            'You can now view your site at <a href="{url}">{url}</a>.'
        ).format(
            url=self._server.public_url,
        )


@final
class ServeDemoWindow(_ServeWindow):
    """
    A window to control the demonstration site server.
    """

    @override
    def _new_server(self) -> Server:
        return demo.DemoServer(app=self._app)

    @override
    def _build_instruction(self) -> str:
        return self._app.localizer._(
            'You can now view a Betty demonstration site at <a href="{url}">{url}</a>.'
        ).format(
            url=self._server.public_url,
        )

    @override
    @property
    def window_title(self) -> Localizable:
        return Str._("Serving the Betty demo...")


@final
class ServeDocsWindow(_ServeWindow):
    """
    A window to control the documentation server.
    """

    @override
    def _new_server(self) -> Server:
        return documentation.DocumentationServer(
            self._app.binary_file_cache.path,
            localizer=self._app.localizer,
        )

    @override
    def _build_instruction(self) -> str:
        return self._app.localizer._(
            'You can now view the documentation at <a href="{url}">{url}</a>.'
        ).format(
            url=self._server.public_url,
        )

    @override
    @property
    def window_title(self) -> Localizable:
        return Str._("Serving the Betty documentation...")
