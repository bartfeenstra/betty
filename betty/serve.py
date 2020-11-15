import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from os import path

import docker
from docker.errors import DockerException
from docker.models.containers import Container

from betty.error import UserFacingError
from betty.os import ChDir
from betty.plugin.nginx import Nginx
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
        logger = logging.getLogger()
        self._server = None
        if Nginx in site.plugins:
            try:
                self._server = DockerServer(site.configuration.www_directory_path, port, site.configuration.output_directory_path)
                logger.info('Starting a Dockerized web server...')
            except DockerException as e:
                raise DockerServerError(e)
        if self._server is None:
            logger.info('Starting Python\'s built-in web server...')
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


class DockerServerError(UserFacingError, RuntimeError):
    pass


class DockerServer(Server):
    _TAG = 'betty-serve'

    def __init__(self, www_directory_path: str, port: int, output_directory_path: str):
        self._www_directory_path = www_directory_path
        self._port = port
        self._output_directory_path = output_directory_path
        self._client = docker.from_env()

    def __enter__(self) -> None:
        self._stop()
        nginx_directory_path = path.join(self._output_directory_path, 'nginx')
        nginx_conf_file_path = path.join(nginx_directory_path, 'nginx.conf')
        self._client.images.build(path=nginx_directory_path, tag=self._TAG)
        self._client.containers.run(self._TAG, name=self._TAG, auto_remove=True, detach=True, volumes={
            nginx_conf_file_path: {
                'bind': '/etc/nginx/conf.d/betty.conf',
                'mode': 'ro',
            },
            self._www_directory_path: {
                'bind': '/var/www/betty',
                'mode': 'ro',
            },
        }, ports={
            '80/tcp': self._port,
        })
        self._container.exec_run(['nginx', '-s', 'reload'])

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop()

    def _stop(self) -> None:
        if self._container is not None:
            self._container.stop()

    @property
    def _container(self) -> Container:
        return self._client.containers.get(self._TAG)
