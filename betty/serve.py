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
from os import symlink
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Self, final, override
from urllib.parse import urlsplit

from betty.exception import HumanFacingException
from betty.functools import Do
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    from types import TracebackType

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
    async def start(self) -> None:
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
    async def stop(self) -> None:
        """
        Stop the server.
        """

    @property
    @abstractmethod
    def public_url(self) -> str:
        """
        The server's public URL.
        """

    async def __aenter__(self) -> Self:
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
        url_parts = urlsplit(self.public_url)
        connection = HTTPConnection(url_parts.netloc)
        connection.request("GET", url_parts.path)
        response = connection.getresponse()
        assert 400 > response.status >= 200


class ProjectServer(Manufacturable, Server):
    """
    A web server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(user=project.upstream.user)
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
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
        self._temporary_root_directory: Path | None = None

    @override
    async def start(self) -> None:
        if self._root_path:
            # To mimic the root path, symlink the project's WWW directory into a temporary
            # directory, so we do not have to make changes to any existing files.
            self._temporary_root_directory = Path(
                await to_thread(mkdtemp),  # ty:ignore[invalid-argument-type]
            )
            temprary_www_directory = self._temporary_root_directory
            for root_path_component in self._root_path.split("/"):
                temprary_www_directory /= root_path_component
            if temprary_www_directory != self._temporary_root_directory:
                temprary_www_directory.parent.mkdir(parents=True, exist_ok=True)
                await to_thread(
                    symlink, self._www_directory_path, temprary_www_directory
                )
            www_directory_path = self._temporary_root_directory
        else:
            www_directory_path = self._www_directory_path
        await self._user.message_debug(_("Starting Python's built-in web server..."))
        for self._port in range(DEFAULT_PORT, 65535):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(
                    ("", self._port),
                    lambda request, client_address, server: (
                        _BuiltinServerRequestHandler(
                            request,
                            client_address,
                            server,
                            directory=str(www_directory_path),
                        )
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
            await to_thread(rmtree, self._temporary_root_directory)


@final
class BuiltinProjectServer(ProjectServer):
    """
    A built-in server for a Betty project.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(project)
        self._server = BuiltinServer(
            project.www_directory,
            root_path=project.root_path,
            user=project.upstream.user,
        )

    @override
    @property
    def public_url(self) -> str:
        return self._server.public_url

    @override
    async def start(self) -> None:
        await to_thread(self._project.www_directory.mkdir, exist_ok=True, parents=True)
        await self._server.start()

    @override
    async def stop(self) -> None:
        await self._server.stop()
