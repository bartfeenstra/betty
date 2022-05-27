import copy
from contextlib import suppress
from os import path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton

from betty import serve
from betty.app import App
from betty.asyncio import sync
from betty.config import ConfigurationError
from betty.gui import BettyWindow
from betty.gui.text import Text

if TYPE_CHECKING:
    from betty.builtins import _


class _ServeThread(QThread):
    server_started = pyqtSignal()

    def __init__(self, app: App, server: serve.Server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._server = server

    @sync
    async def run(self) -> None:
        self._app.acquire()
        await self._server.start()
        self.server_started.emit()

    @sync
    async def stop(self) -> None:
        await self._server.stop()
        self._app.release()


class _ServeWindow(BettyWindow):
    """
    Show a window that controls the site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    width = 500
    height = 100
    _instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self._server = NotImplemented

        self._central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._loading_instruction = Text(_('Loading...'))
        self._loading_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(self._loading_instruction)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def _build_instruction(self) -> str:
        raise NotImplementedError

    def _server_started(self) -> None:
        # The server may have been stopped before this method was called.
        if self._server is None:
            return

        self._loading_instruction.close()

        instance_instruction = Text(self._build_instruction())
        instance_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(instance_instruction)

        general_instruction = Text(_('Keep this window open to keep the site running.'))
        general_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(general_instruction)

        stop_server_button = QPushButton(_('Stop the site'), self)
        stop_server_button.released.connect(self.close)
        self._central_layout.addWidget(stop_server_button)

    def show(self) -> None:
        super().show()
        # Explicitly activate this window in case it existed and was shown before, but requested again.
        self.activateWindow()
        self._start()

    def _start(self) -> None:
        if self._thread is None:
            self._thread = _ServeThread(copy.copy(self._app), self._server)
            self._thread.server_started.connect(self._server_started)
            self._thread.start()

    def close(self) -> bool:
        self._stop()
        return super().close()

    def _stop(self) -> None:
        with suppress(AttributeError):
            self._thread.stop()
        self._thread = None
        self._server = None
        self.__class__._instance = None


class ServeAppWindow(_ServeWindow):
    """
    Show a window that controls an application's site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._server = serve.AppServer(self._app)

        if not path.isdir(self._app.project.configuration.www_directory_path):
            self.close()
            raise ConfigurationError(_('Web root directory "{path}" does not exist.').format(path=self._app.project.configuration.www_directory_path))

    @property
    def title(self) -> str:
        return _('Serving your site...')

    def _build_instruction(self) -> str:
        return _('You can now view your site at <a href="{url}">{url}</a>.').format(url=self._server.public_url)


class ServeDemoWindow(_ServeWindow):
    """
    Show a window that controls the demo site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    def __init__(self, *args, **kwargs):
        from betty import demo

        super().__init__(*args, **kwargs)

        self._server = demo.DemoServer()

    def _build_instruction(self) -> str:
        return _('You can now view a Betty demonstration site at <a href="{url}">{url}</a>.').format(url=self._server.public_url)

    @property
    def title(self) -> str:
        return _('Serving the Betty demo...')
