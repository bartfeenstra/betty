from __future__ import annotations

import contextlib
import copy
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from typing import Iterable, Optional, TYPE_CHECKING

from betty.app import App
from betty.error import UserFacingError
from betty.os import ChDir


if TYPE_CHECKING:
    from betty.builtins import _

DEFAULT_PORT = 8000


class ServerNotStartedError(RuntimeError):
    pass


class NoPublicUrlBecauseServerNotStartedError(ServerNotStartedError):
    def __init__(self):
        super().__init__('Cannot get the public URL for a server that has not started yet.')


class OsError(UserFacingError, OSError):
    pass


class Server:
    """
    Provide a development web server.
    """

    async def start(self) -> None:
        """
        Starts the server.
        """
        pass

    async def stop(self) -> None:
        """
        Stops the server.
        """
        pass

    @property
    def public_url(self) -> str:
        raise NotImplementedError

    async def __aenter__(self) -> Server:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


class ServerProvider:
    @property
    def servers(self) -> Iterable[Server]:
        raise NotImplementedError


class AppServer(Server):
    def __init__(self, app: App):
        self._app = app
        self._server: Optional[Server] = None

    def _get_server(self) -> Server:
        for extension in self._app.extensions.flatten():
            if isinstance(extension, ServerProvider):
                for server in extension.servers:
                    return server
        return BuiltinServer(self._app)

    async def start(self) -> None:
        self._server = self._get_server()
        await self._server.start()
        # Some tests fail on Windows with `NameError: name '_' is not defined`, so we acquire the locale to be sure.
        with self._app.acquire_locale():
            logging.getLogger().info(_('Serving your site at {url}...').format(url=self.public_url))
        webbrowser.open_new_tab(self.public_url)

    @property
    def public_url(self) -> str:
        if self._server is None:
            raise NoPublicUrlBecauseServerNotStartedError()
        return self._server.public_url

    async def stop(self) -> None:
        if self._server:
            await self._server.stop()


class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


class BuiltinServer(Server):
    def __init__(self, app: App):
        self._app = app
        self._http_server: Optional[HTTPServer] = None
        self._port: Optional[int] = None
        self._thread: Optional[threading.Thread] = None

    async def start(self) -> None:
        logging.getLogger().info(_("Starting Python's built-in web server..."))
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(('', self._port), _BuiltinServerRequestHandler)
                break
        if self._http_server is None:
            raise OsError('Cannot find an available port to bind the web server to.')
        self._thread = threading.Thread(target=self._serve)
        self._thread.start()

    @property
    def public_url(self) -> str:
        if self._port is not None:
            return f'http://localhost:{self._port}'
        raise NoPublicUrlBecauseServerNotStartedError()

    def _serve(self):
        with contextlib.redirect_stderr(StringIO()):
            with ChDir(self._app.project.configuration.www_directory_path):
                with copy.copy(self._app):
                    assert self._http_server
                    self._http_server.serve_forever()

    async def stop(self) -> None:
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._thread is not None:
            self._thread.join()
