from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton

from betty.app import App
from betty.asyncio import sync
from betty.gui import BettyWindow
from betty.gui.error import catch_exceptions
from betty.gui.text import Text
from betty.project import Project
from betty.serve import Server, AppServer


class _ServeThread(QThread):
    server_started = pyqtSignal()

    def __init__(self, project: Project, server_name: str, serve_window: _ServeWindow, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._project = project
        self._server_name = server_name
        self._serve_window = serve_window
        self._app: App | None = None
        self._server: Server | None = None

    @property
    def server(self) -> Server:
        if self._server is None:
            raise RuntimeError('This thread has not been started yet.')
        return self._server

    @sync
    async def run(self) -> None:
        with catch_exceptions(parent=self._serve_window, close_parent=True):
            async with App(project=self._project) as self._app:
                self._server = self._app.servers[self._server_name]
                await self._server.start()
                self.server_started.emit()
                await self._server.show()

    @sync
    async def stop(self) -> None:
        server = self._server
        if server is not None:
            await server.stop()


class _ServeWindow(BettyWindow):
    window_width = 500
    window_height = 100

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.__thread: _ServeThread | None = None

        self._central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._loading_instruction = Text(self._app.localizer._('Loading...'))
        self._loading_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(self._loading_instruction)

    def _server_name(self) -> str:
        raise NotImplementedError(repr(self))

    @property
    def _thread(self) -> _ServeThread:
        if self.__thread is None:
            raise RuntimeError('This window has not been shown yet.')
        return self.__thread

    def _build_instruction(self) -> str:
        raise NotImplementedError(repr(self))

    def _server_started(self) -> None:
        # The server may have been stopped before this method was called.
        if self.__thread is None:
            return

        self._loading_instruction.close()

        instance_instruction = Text(self._build_instruction())
        instance_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(instance_instruction)

        general_instruction = Text(self._app.localizer._('Keep this window open to keep the site running.'))
        general_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(general_instruction)

        stop_server_button = QPushButton(self._app.localizer._('Stop the site'), self)
        stop_server_button.released.connect(
            self.close,
        )
        self._central_layout.addWidget(stop_server_button)

    def show(self) -> None:
        super().show()
        # Explicitly activate this window in case it existed and was shown before, but requested again.
        self.activateWindow()
        self._start()

    def _start(self) -> None:
        if self.__thread is None:
            self.__thread = _ServeThread(self._app.project, self._server_name(), self)
            self.__thread.server_started.connect(self._server_started)
            self.__thread.start()

    def close(self) -> bool:
        self._stop()
        return super().close()

    def _stop(self) -> None:
        if self.__thread is not None:
            self.__thread.stop()
        self.__thread = None


class ServeProjectWindow(_ServeWindow):
    def _server_name(self) -> str:
        return AppServer.get(self._app).name()

    @property
    def title(self) -> str:
        return self._app.localizer._('Serving your site...')

    def _build_instruction(self) -> str:
        return self._app.localizer._('You can now view your site at <a href="{url}">{url}</a>.').format(
            url=self._thread.server.public_url,
        )


class ServeDemoWindow(_ServeWindow):
    def _server_name(self) -> str:
        from betty.extension import demo

        return demo.DemoServer.name()

    def _build_instruction(self) -> str:
        return self._app.localizer._('You can now view a Betty demonstration site at <a href="{url}">{url}</a>.').format(
            url=self._thread.server.public_url,
        )

    @property
    def title(self) -> str:
        return self._app.localizer._('Serving the Betty demo...')
