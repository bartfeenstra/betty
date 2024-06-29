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
from typing import Any, TYPE_CHECKING

from aiofiles.os import makedirs, symlink
from aiofiles.tempfile import TemporaryDirectory, AiofilesContextManagerTempDir
from aiohttp import ClientSession
from typing_extensions import override

from betty.error import UserFacingError
from betty.functools import Do
from betty.locale import Str, Localizer, Localizable

if TYPE_CHECKING:
    from betty.project.__init__ import Project
    from types import TracebackType

DEFAULT_PORT = 8000


class ServerNotStartedError(RuntimeError):
    """
    Raised when a web server has not (fully) started yet.
    """

    pass  # pragma: no cover


class NoPublicUrlBecauseServerNotStartedError(ServerNotStartedError):
    """
    A public URL is not yet available because the server has not (fully) started yet.
    """

    def __init__(self):
        super().__init__(
            "Cannot get the public URL for a server that has not started yet."
        )


class OsError(UserFacingError, OSError):
    """
    Raised for I/O errors.
    """

    pass  # pragma: no cover


class Server:
    """
    Provide a development web server.
    """

    def __init__(self, localizer: Localizer):
        self._localizer = localizer

    @classmethod
    def name(cls) -> str:
        """
        Get the server's machine name.
        """
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def label(cls) -> Localizable:
        """
        Get the server's human-readable label.
        """
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
        logging.getLogger(__name__).info(
            self._localizer._("Serving your site at {url}...").format(
                url=self.public_url,
            )
        )
        webbrowser.open_new_tab(self.public_url)

    async def stop(self) -> None:
        """
        Stop the server.
        """
        pass

    @property
    def public_url(self) -> str:
        """
        The server's public URL.
        """
        raise NotImplementedError(repr(self))

    async def __aenter__(self) -> Server:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def assert_available(self) -> None:
        """
        Assert that this server is available.
        """
        # @todo In Betty 0.4.0, require the app's existing client session.
        async with ClientSession() as session:
            try:
                await Do[Any, None](self._assert_available, session).until()
            except Exception as error:
                raise UserFacingError(
                    Str._("The server was unreachable after starting.")
                ) from error

    async def _assert_available(self, session: ClientSession) -> None:
        """
        Assert that this server is available.

        If this method returns, the server is considered available.
        If this method raises an exception, the server is considered unavailable.
        """
        async with session.get(self.public_url) as response:
            assert response.status == 200


class ProjectServer(Server):
    """
    A web server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(localizer=project.app.localizer)
        self._project = project

    @override
    async def start(self) -> None:
        await makedirs(self._project.configuration.www_directory_path, exist_ok=True)
        await super().start()


class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    @override
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


class BuiltinServer(Server):
    """
    A built-in server for a WWW directory.
    """

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
        self._temporary_root_directory: (
            AiofilesContextManagerTempDir[None, Any, Any] | None
        ) = None

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Python built-in")

    @override
    async def start(self) -> None:
        await super().start()
        if self._root_path:
            # To mimic the root path, symlink the project's WWW directory into a temporary
            # directory, so we do not have to make changes to any existing files.
            self._temporary_root_directory = TemporaryDirectory()
            temporary_root_directory_path = Path(
                await self._temporary_root_directory.__aenter__()
            )
            temporary_www_directory = temporary_root_directory_path
            for root_path_component in self._root_path.split("/"):
                temporary_www_directory /= root_path_component
            if temporary_www_directory != temporary_root_directory_path:
                await symlink(self._www_directory_path, temporary_www_directory)
            www_directory_path = temporary_root_directory_path
        else:
            www_directory_path = self._www_directory_path
        logging.getLogger(__name__).info(
            self._localizer._("Starting Python's built-in web server...")
        )
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(
                    ("", self._port),
                    lambda request,
                    client_address,
                    server: _BuiltinServerRequestHandler(
                        request,
                        client_address,
                        server,
                        directory=str(www_directory_path),
                    ),
                )
                break
        if self._http_server is None:
            raise OsError(
                Str._("Cannot find an available port to bind the web server to.")
            )
        self._thread = threading.Thread(target=self._serve)
        self._thread.start()
        await self.assert_available()

    @override
    @property
    def public_url(self) -> str:
        if self._port is not None:
            url = f"http://localhost:{self._port}"
            if self._root_path:
                url = f"{url}/{self._root_path}"
            return url
        raise NoPublicUrlBecauseServerNotStartedError()

    def _serve(self) -> None:
        with contextlib.redirect_stderr(StringIO()):
            assert self._http_server
            self._http_server.serve_forever()

    @override
    async def stop(self) -> None:
        await super().stop()
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._thread is not None:
            self._thread.join()
        if self._temporary_root_directory is not None:
            await self._temporary_root_directory.__aexit__(None, None, None)


class BuiltinProjectServer(ProjectServer):
    """
    A built-in server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(project)
        self._server = BuiltinServer(
            project.configuration.www_directory_path,
            root_path=project.configuration.root_path,
            localizer=project.app.localizer,
        )

    @override
    @classmethod
    def label(cls) -> Localizable:
        return BuiltinServer.label()

    @override
    @property
    def public_url(self) -> str:
        return self._server.public_url

    @override
    async def start(self) -> None:
        await super().start()
        await self._server.start()

    @override
    async def stop(self) -> None:
        await super().stop()
        await self._server.stop()
