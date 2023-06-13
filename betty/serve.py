from __future__ import annotations

import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from types import TracebackType
from typing import Sequence

from betty.app import App
from betty.error import UserFacingError
from betty.locale import Localizer, Localizable
from betty.os import ChDir
from betty.project import Project

DEFAULT_PORT = 8000


class ServerNotStartedError(RuntimeError):
    pass


class NoPublicUrlBecauseServerNotStartedError(ServerNotStartedError):
    def __init__(self):
        super().__init__('Cannot get the public URL for a server that has not started yet.')


class OsError(UserFacingError, OSError):
    pass


class Server(Localizable):
    """
    Provide a development web server.
    """

    @classmethod
    def name(cls) -> str:
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        raise NotImplementedError(repr(cls))

    async def start(self) -> None:
        """
        Starts the server.
        """
        raise NotImplementedError(repr(self))

    async def show(self) -> None:
        """
        Shows the served site to the user.
        """
        logging.getLogger().info(self.localizer._('Serving your site at {url}...').format(url=self.public_url))
        webbrowser.open_new_tab(self.public_url)

    async def stop(self) -> None:
        """
        Stops the server.
        """
        await self._stop()

    async def _stop(self) -> None:
        raise NotImplementedError(repr(self))

    @property
    def public_url(self) -> str:
        raise NotImplementedError(repr(self))

    async def __aenter__(self) -> Server:
        await self.start()
        return self

    async def __aexit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        await self.stop()


class ProjectServer(Server):
    def __init__(self, project: Project, *, localizer: Localizer | None = None) -> None:
        super().__init__(localizer=localizer)
        self._project = project

    @staticmethod
    def get(app: App) -> ProjectServer:
        for server in app.servers.values():
            if isinstance(server, ProjectServer):
                return server
        raise RuntimeError(f'Cannot find a project server. This must never happen, because {BuiltinServer} should be the fallback.')

    async def start(self) -> None:
        self._project.configuration.www_directory_path.mkdir(parents=True, exist_ok=True)
        await super().start()


class ServerProvider:
    @property
    def servers(self) -> Sequence[Server]:
        raise NotImplementedError(repr(self))


class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


class BuiltinServer(ProjectServer):
    def __init__(self, project: Project, *, localizer: Localizer | None = None) -> None:
        super().__init__(project, localizer=localizer)
        self._http_server: HTTPServer | None = None
        self._port: int | None = None
        self._thread: threading.Thread | None = None

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Python built-in')

    async def start(self) -> None:
        logging.getLogger().info(self.localizer._("Starting Python's built-in web server..."))
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(('', self._port), _BuiltinServerRequestHandler)
                break
        if self._http_server is None:
            raise OsError('Cannot find an available port to bind the web server to.')
        self._thread = threading.Thread(target=self._serve, args=(self._project,))
        self._thread.start()

    @property
    def public_url(self) -> str:
        if self._port is not None:
            return f'http://localhost:{self._port}'
        raise NoPublicUrlBecauseServerNotStartedError()

    def _serve(self, project: Project) -> None:
        with contextlib.redirect_stderr(StringIO()):
            with ChDir(project.configuration.www_directory_path):
                assert self._http_server
                self._http_server.serve_forever()

    async def stop(self) -> None:
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._thread is not None:
            self._thread.join()
