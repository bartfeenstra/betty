import contextlib
import logging
import multiprocessing
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO

from betty.os import chdir
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
        self._process = None
        self._server = None
        self._parent_connection, self._child_connection = multiprocessing.Pipe(True)

    def __enter__(self) -> None:
        self._server = HTTPServer(('', self._port), SimpleHTTPRequestHandler)
        self._process = multiprocessing.Process(target=self._serve, args=(self._child_connection,))
        self._process.start()

    def _serve(self, connection: multiprocessing.connection.Connection) -> None:
        try:
            with chdir(self._www_directory_path):
                with contextlib.redirect_stderr(StringIO()):
                    threading.Thread(target=self._server.serve_forever).start()
                    if connection.recv():
                        self._server.shutdown()
        except BaseException as e:
            connection.send(e)
            connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._parent_connection.send(True)
        self._process.join()
        if self._parent_connection.poll():
            raise self._parent_connection.recv()
