import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from typing import Iterable

from betty.error import UserFacingError
from betty.os import ChDir, PathLike
from betty.app import App

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
        :return: The public URL.
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

    async def __aenter__(self) -> 'Server':
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
        self._server = None

    def _get_server(self) -> Server:
        servers = (server for extension in self._app.extensions if isinstance(extension, ServerProvider) for server in extension.servers)
        with contextlib.suppress(StopIteration):
            return next(servers)
        return BuiltinServer(self._app.configuration.www_directory_path)

    async def start(self) -> None:
        self._server = self._get_server()
        await self._server.start()
        logging.getLogger().info('Serving your site at %s...' % self.public_url)
        webbrowser.open_new_tab(self.public_url)

    @property
    def public_url(self) -> str:
        if self._server is None:
            raise NoPublicUrlBecauseServerNotStartedError()
        return self._server.public_url

    async def stop(self) -> None:
        await self._server.stop()


class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


class BuiltinServer(Server):
    def __init__(self, www_directory_path: PathLike):
        self._www_directory_path = www_directory_path
        self._http_server = None
        self._port = None

    async def start(self) -> None:
        logging.getLogger().info('Starting Python\'s built-in web server...')
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(('', self._port), _BuiltinServerRequestHandler)
                break
        if self._http_server is None:
            raise OsError('Cannot find an available port to bind the web server to.')
        threading.Thread(target=self._serve).start()

    @property
    def public_url(self) -> str:
        if self._port is not None:
            return 'http://localhost:%d' % self._port
        raise NoPublicUrlBecauseServerNotStartedError()

    def _serve(self):
        with contextlib.redirect_stderr(StringIO()):
            with ChDir(self._www_directory_path):
                self._http_server.serve_forever()

    async def stop(self) -> None:
        if self._http_server is not None:
            self._http_server.shutdown()
