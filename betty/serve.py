import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO

DEFAULT_PORT = 8000


def serve(www_directory_path: str, port: int = DEFAULT_PORT) -> None:
    threading.Thread(target=_start_http_server, args=(www_directory_path, port)).start()
    public_url = 'http://localhost:%d' % port
    logging.getLogger().info('Serving your site at %s...' % public_url)
    webbrowser.open_new_tab(public_url)


def _start_http_server(www_directory_path: str, port: int) -> None:
    class RequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            SimpleHTTPRequestHandler.__init__(self, *args, directory=www_directory_path, **kwargs)
    server = HTTPServer(('', port), RequestHandler)
    with contextlib.redirect_stderr(StringIO()):
        server.serve_forever()
