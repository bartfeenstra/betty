import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO

from betty.os import ChDir
from betty.site import Site

DEFAULT_PORT = 8000


class Server:
    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SiteServer(Server):
    def __init__(self, site: Site, port: int):
        self._site = site
        self._port = port
        self._server = BuiltinServer(site.configuration.www_directory_path, port)

    def __enter__(self) -> None:
        public_url = 'http://localhost:%d' % self._port
        self._server.__enter__()
        logging.getLogger().info('Serving your site at %s...' % public_url)
        webbrowser.open_new_tab(public_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.__exit__(exc_type, exc_val, exc_tb)


class BuiltinServer(Server):
    def __init__(self, www_directory_path: str, port: int):
        self._port = port
        self._www_directory_path = www_directory_path
        self._http_server = None
        self._cwd = None

    def __enter__(self) -> None:
        self._http_server = HTTPServer(('', self._port), SimpleHTTPRequestHandler)
        self._cwd = ChDir(self._www_directory_path).change()
        threading.Thread(target=self._serve).start()

    def _serve(self):
        with contextlib.redirect_stderr(StringIO()):
            self._http_server.serve_forever()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._http_server.shutdown()
        self._cwd.revert()
