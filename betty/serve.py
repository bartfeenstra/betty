import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from typing import Iterable
from betty.os import ChDir
from betty.site import Site

DEFAULT_PORT = 8000


class Server:
    @property
    def public_url(self) -> str:
        """
        The public URL under which the site is served.

        :raises RuntimeError if the server context has not been entered yet and no URL is available yet.
        """
        raise NotImplementedError

    def __enter__(self) -> 'Server':
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ServerProvider:
    @property
    def servers(self) -> Iterable[Server]:
        raise NotImplementedError


class SiteServer(Server):
    def __init__(self, site: Site):
        self._site = site
        self._server = None

    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise RuntimeError('Cannot determine the public URL until this server\'s context has been entered.')

    def _get_server(self) -> Server:
        servers = (server for plugin in self._site.plugins.values() if isinstance(plugin, ServerProvider) for server in plugin.servers)
        with contextlib.suppress(StopIteration):
            return next(servers)
        return BuiltinServer(self._site.configuration.www_directory_path)

    def __enter__(self) -> Server:
        self._server = self._get_server()
        self._server.__enter__()
        logging.getLogger().info('Serving your site at %s...' % self.public_url)
        webbrowser.open_new_tab(self.public_url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.__exit__(exc_type, exc_val, exc_tb)


class BuiltinServer(Server):
    def __init__(self, www_directory_path: str):
        self._www_directory_path = www_directory_path
        self._port = None
        self._http_server = None
        self._cwd = None

    @property
    def public_url(self) -> str:
        if self._port is not None:
            return 'http://localhost:%d' % self._port
        raise RuntimeError('Cannot determine the public URL until this server\'s context has been entered.')

    def __enter__(self) -> Server:
        logging.getLogger().info('Starting Python\'s built-in web server...')
        for port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(('', port), SimpleHTTPRequestHandler)
                self._port = port
                break
        self._cwd = ChDir(self._www_directory_path).change()
        threading.Thread(target=self._serve).start()
        return self

    def _serve(self):
        with contextlib.redirect_stderr(StringIO()):
            self._http_server.serve_forever()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._http_server.shutdown()
        self._cwd.revert()
