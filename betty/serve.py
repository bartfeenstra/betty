"""
Provide the Serve API to serve resources within the application.
"""
from __future__ import annotations

import contextlib
import logging
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from io import StringIO
from pathlib import Path
from types import TracebackType
from typing import Sequence, Any

from aiofiles.os import makedirs, symlink
from aiofiles.tempfile import TemporaryDirectory, AiofilesContextManagerTempDir

from betty.app import App
from betty.asyncio import sync
from betty.error import UserFacingError
from betty.locale import Str, Localizer

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

    def __init__(self, localizer: Localizer):
        self._localizer = localizer

    @classmethod
    def name(cls) -> str:
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def label(cls) -> Str:
        raise NotImplementedError(repr(cls))

    async def start(self) -> None:
        """
        Start the server.
        """
        pass

    async def show(self) -> None:
        """
        Show the served site to the user.
        """
        logging.getLogger(__name__).info(self._localizer._('Serving your site at {url}...').format(
            url=self.public_url,
        ))
        webbrowser.open_new_tab(self.public_url)

    async def stop(self) -> None:
        """
        Stop the server.
        """
        pass

    @property
    def public_url(self) -> str:
        raise NotImplementedError(repr(self))

    async def __aenter__(self) -> Server:
        await self.start()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.stop()


class AppServer(Server):
    def __init__(self, app: App) -> None:
        super().__init__(localizer=app.localizer)
        self._app = app

    @staticmethod
    def get(app: App) -> AppServer:
        for server in app.servers.values():
            if isinstance(server, AppServer):
                return server
        raise RuntimeError(f'Cannot find a project server. This must never happen, because {BuiltinAppServer} should be the fallback.')

    async def start(self) -> None:
        await makedirs(self._app.project.configuration.www_directory_path, exist_ok=True)
        await super().start()


class ServerProvider:
    @property
    def servers(self) -> Sequence[Server]:
        raise NotImplementedError(repr(self))


class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


class BuiltinServer(Server):
    def __init__(
        self,
        www_directory_path: Path,
        *,
        root_path: str | None = None,
        localizer: Localizer,
    ) -> None:
        super().__init__(localizer)
        self._www_directory_path = www_directory_path
        self._root_path = root_path
        self._http_server: HTTPServer | None = None
        self._port: int | None = None
        self._thread: threading.Thread | None = None
        self._temporary_root_directory: AiofilesContextManagerTempDir[None, Any, Any] | None = None

    @classmethod
    def label(cls) -> Str:
        return Str._('Python built-in')

    async def start(self) -> None:
        await super().start()
        if self._root_path:
            # To mimic the root path, symlink the project's WWW directory into a temporary
            # directory, so we do not have to make changes to any existing files.
            self._temporary_root_directory = TemporaryDirectory()
            temporary_root_directory_path = Path(await self._temporary_root_directory.__aenter__())
            temporary_www_directory = temporary_root_directory_path
            for root_path_component in self._root_path.split('/'):
                temporary_www_directory /= root_path_component
            if temporary_www_directory != temporary_root_directory_path:
                await symlink(self._www_directory_path, temporary_www_directory)
            www_directory_path = temporary_root_directory_path
        else:
            www_directory_path = self._www_directory_path
        logging.getLogger(__name__).info(self._localizer._("Starting Python's built-in web server..."))
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(
                    ('', self._port),
                    lambda request, client_address, server: _BuiltinServerRequestHandler(
                        request,
                        client_address,
                        server,
                        directory=str(www_directory_path),
                    ),
                )
                break
        if self._http_server is None:
            raise OsError(Str._('Cannot find an available port to bind the web server to.'))
        self._thread = threading.Thread(target=self._serve)
        self._thread.start()

    @property
    def public_url(self) -> str:
        if self._port is not None:
            url = f'http://localhost:{self._port}'
            if self._root_path:
                url = f'{url}/{self._root_path}'
            return url
        raise NoPublicUrlBecauseServerNotStartedError()

    @sync
    async def _serve(self) -> None:
        with contextlib.redirect_stderr(StringIO()):
            assert self._http_server
            self._http_server.serve_forever()

    async def stop(self) -> None:
        await super().stop()
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._thread is not None:
            self._thread.join()
        if self._temporary_root_directory is not None:
            await self._temporary_root_directory.__aexit__(None, None, None)


class BuiltinAppServer(AppServer):
    def __init__(self, app: App) -> None:
        super().__init__(app)
        self._server = BuiltinServer(
            self._app.project.configuration.www_directory_path,
            root_path=self._app.project.configuration.root_path,
            localizer=self._app.localizer
        )

    @classmethod
    def label(cls) -> Str:
        return BuiltinServer.label()

    @property
    def public_url(self) -> str:
        return self._server.public_url

    async def start(self) -> None:
        await super().start()
        await self._server.start()

    async def stop(self) -> None:
        await super().stop()
        await self._server.stop()
