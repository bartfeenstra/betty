import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from typing import Iterable

from betty.error import UserFacingError
from betty.os import ChDir
from betty.site import Site

DEFAULT_PORT = 8000


class ServerNotStartedError(RuntimeError):
    pass


class OsError(UserFacingError, OSError):
    pass


class Server:
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


class SiteServer(Server):
    def __init__(self, site: Site):
        self._site = site
        self._server = None

    def _get_server(self) -> Server:
        servers = (server for plugin in self._site.plugins.values() if isinstance(plugin, ServerProvider) for server in plugin.servers)
        with contextlib.suppress(StopIteration):
            return next(servers)
        return BuiltinServer(self._site.configuration.www_directory_path)

    async def start(self) -> None:
        self._server = self._get_server()
        await self._server.start()
        logging.getLogger().info('Serving your site at %s...' % self.public_url)
        webbrowser.open_new_tab(self.public_url)

    @property
    def public_url(self) -> str:
        return self._server.public_url

    async def stop(self) -> None:
        await self._server.stop()


class BuiltinServer(Server):
    def __init__(self, www_directory_path: str):
        self._www_directory_path = www_directory_path
        self._http_server = None
        self._cwd = None
        self._port = None

    async def start(self) -> None:
        logging.getLogger().info('Starting Python\'s built-in web server...')
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(('', self._port), SimpleHTTPRequestHandler)
                break
        if self._http_server is None:
            raise OsError('Cannot find an available port to bind the web server to.')
        self._cwd = ChDir(self._www_directory_path).change()
        threading.Thread(target=self._serve).start()

    @property
    def public_url(self) -> str:
        if self._port is not None:
            return 'http://localhost:%d' % self._port
        raise ServerNotStartedError('Cannot determine the public URL if the server has not started yet.')

    def _serve(self):
        with contextlib.redirect_stderr(StringIO()):
            self._http_server.serve_forever()

    async def stop(self) -> None:
        self._http_server.shutdown()
        self._cwd.revert()
