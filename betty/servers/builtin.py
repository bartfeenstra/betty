"""
A web server using Python's HTTP server.
"""

from __future__ import annotations

import contextlib
import threading
from asyncio import to_thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from io import StringIO
from os import symlink
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Final, final, override

from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.server import Server, ServerNotStarted

if TYPE_CHECKING:
    from betty.pathlib import StrPath
    from betty.user import User


class _OsError(HumanFacingException, OSError):
    pass


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

    _default_port: Final[int] = 8000

    def __init__(
        self,
        www_directory: StrPath,
        /,
        *,
        root_path: str | None = None,
        user: User,
    ) -> None:
        super().__init__(user=user)
        self._www_directory = www_directory
        self._root_path = root_path
        self._http_server: HTTPServer | None = None
        self._port: int | None = None
        self._thread: threading.Thread | None = None
        self._temporary_root_directory: Path | None = None

    @override
    async def start(self) -> None:
        if self._root_path:
            # To mimic the root path, symlink the WWW directory into a temporary
            # directory, so we do not have to make changes to any existing files.
            self._temporary_root_directory = Path(
                await to_thread(mkdtemp),  # ty:ignore[invalid-argument-type]
            )
            temprary_www_directory = self._temporary_root_directory
            for root_path_component in self._root_path.split("/"):
                temprary_www_directory /= root_path_component
            if temprary_www_directory != self._temporary_root_directory:
                temprary_www_directory.parent.mkdir(parents=True, exist_ok=True)
                await to_thread(symlink, self._www_directory, temprary_www_directory)
            www_directory = self._temporary_root_directory
        else:
            www_directory = self._www_directory
        await self._user.message_debug(_("Starting Python's built-in web server..."))
        for self._port in range(  # noqa: B020
            self._default_port,
            65535,
        ):
            with contextlib.suppress(OSError):
                self._http_server = HTTPServer(
                    ("", self._port),
                    lambda request, client_address, server: (
                        _BuiltinServerRequestHandler(
                            request,
                            client_address,
                            server,
                            directory=str(www_directory),
                        )
                    ),
                )
                break
        if self._http_server is None:
            raise _OsError(
                _("Cannot find an available port to bind the web server to.")
            )
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
        raise ServerNotStarted

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
