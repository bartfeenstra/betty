"""
Provide the Serve API to serve resources within the application.
"""

from __future__ import annotations

import contextlib
import threading
import webbrowser
from abc import ABC, abstractmethod
from asyncio import to_thread
from http.client import HTTPConnection
from http.server import HTTPServer, SimpleHTTPRequestHandler
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, final
from urllib.parse import urlparse

from aiofiles.os import makedirs, symlink
from aiofiles.tempfile import AiofilesContextManagerTempDir, TemporaryDirectory
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.functools import Do
from betty.locale.localizable import _
from betty.project.factory import ProjectDependentFactory

if TYPE_CHECKING:
    from types import TracebackType

    from betty.project import Project
    from betty.user import User

DEFAULT_PORT = 8000


class ServerNotStartedError(RuntimeError):
    """
    Raised when a web server has not (fully) started yet.
    """


class NoPublicUrlBecauseServerNotStartedError(ServerNotStartedError):
    """
    A public URL is not yet available because the server has not (fully) started yet.
    """

    def __init__(self):
        super().__init__(
            "Cannot get the public URL for a server that has not started yet."
        )


class OsError(HumanFacingException, OSError):
    """
    Raised for I/O errors.
    """


class Server(ABC):
    """
    Provide a (development) web server.
    """

    def __init__(self, *, user: User):
        self._user = user

    @abstractmethod
    async def start(self) -> None:  # noqa B027
        """
        Start the server.
        """

    async def show(self) -> None:
        """
        Show the served site to the user.
        """
        await self._user.message_information(
            _("Serving your site at {url}...").format(
                url=self.public_url,
            )
        )
        webbrowser.open_new_tab(self.public_url)

    @abstractmethod
    async def stop(self) -> None:  # noqa B027
        """
        Stop the server.
        """

    @property
    @abstractmethod
    def public_url(self) -> str:
        """
        The server's public URL.
        """

    async def __aenter__(self) -> Server:
        await self.start()
        try:
            await self.assert_available()
        except BaseException:
            await self.stop()
            raise
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
        try:
            await Do[Any, None](self._assert_available).until()
        except Exception as error:
            raise HumanFacingException(
                _("The server at {url} was unreachable after starting.").format(
                    url=self.public_url
                )
            ) from error

    async def _assert_available(self) -> None:
        await to_thread(self.__assert_available)

    def __assert_available(self) -> None:
        url = urlparse(self.public_url)
        connection = HTTPConnection(url.netloc)
        connection.request("GET", url.path)
        response = connection.getresponse()
        assert 400 > response.status >= 200


class ProjectServer(ProjectDependentFactory, Server):
    """
    A web server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(user=project.app.user)
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)


@final
class _BuiltinServerRequestHandler(SimpleHTTPRequestHandler):
    @override
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


@final
class BuiltinServer(Server):
    """
    A built-in server for a WWW directory.
    """

    def __init__(
        self, www_directory_path: Path, *, root_path: str | None = None, user: User
    ) -> None:
        super().__init__(user=user)
        self._www_directory_path = www_directory_path
        self._root_path = root_path
        self._http_server: HTTPServer | None = None
        self._port: int | None = None
        self._thread: threading.Thread | None = None
        self._temporary_root_directory: AiofilesContextManagerTempDir | None = None

    @override
    async def start(self) -> None:
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
                temporary_www_directory.parent.mkdir(parents=True, exist_ok=True)
                await symlink(self._www_directory_path, temporary_www_directory)
            www_directory_path = temporary_root_directory_path
        else:
            www_directory_path = self._www_directory_path
        await self._user.message_debug(_("Starting Python's built-in web server..."))
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
            raise OsError(_("Cannot find an available port to bind the web server to."))
        self._thread = threading.Thread(target=self._serve)
        self._thread.start()

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
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
        if self._thread is not None:
            self._thread.join()
        if self._temporary_root_directory is not None:
            await self._temporary_root_directory.__aexit__(None, None, None)


@final
class BuiltinProjectServer(ProjectServer):
    """
    A built-in server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(project)
        self._server = BuiltinServer(
            project.configuration.www_directory_path,
            root_path=project.configuration.root_path,
            user=project.app.user,
        )

    @override
    @property
    def public_url(self) -> str:
        return self._server.public_url

    @override
    async def start(self) -> None:
        await makedirs(self._project.configuration.www_directory_path, exist_ok=True)
        await self._server.start()

    @override
    async def stop(self) -> None:
        await self._server.stop()
