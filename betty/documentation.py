"""
Provide the Documentation API.
"""

from __future__ import annotations

import multiprocessing
from asyncio import to_thread
from contextlib import AsyncExitStack
from shutil import copytree
from typing import TYPE_CHECKING, final, override

from sphinx.application import Sphinx
from sphinx.ext.autodoc import MethodDocumenter

from betty.dirs import root_directory
from betty.exception import HumanFacingException
from betty.pathlib import StrPath, resolve_path
from betty.server import Server, ServerNotStarted
from betty.servers import builtin
from betty.user import User, Verbosity

if TYPE_CHECKING:
    from pathlib import Path


async def _ensure_www_directory(
    output_directory: Path, cache_directory: Path, *, user: User
) -> None:
    if not output_directory.exists():
        await _build(output_directory, cache_directory, user=user)


async def _build(output_directory: Path, cache_directory: Path, *, user: User) -> None:
    output_directory.mkdir(exist_ok=True, parents=True)
    # sphinx-apidoc must output to the documentation directory, but because we do not want
    # to 'pollute' that with generated files that must not be committed, do our work in a
    # dedicated cache directory.
    source_directory = cache_directory / "source"
    await to_thread(copytree, root_directory / "documentation", source_directory)
    sphinx_app = Sphinx(
        buildername="dirhtml",
        confdir=str(source_directory),
        doctreedir=str(cache_directory / ".doctrees"),
        outdir=str(output_directory),
        parallel=multiprocessing.cpu_count(),
        srcdir=str(source_directory),
        verbosity=9 if user.verbosity is Verbosity.MOST_VERBOSE else 0,
        warningiserror=True,
    )
    # Work around a bug in Sphinx where MethodDocumenter.can_document_member would erroneously consider our descriptors
    # as methods resulting in errors being raised because said descriptors are not callable and do not have a signature.
    original_can_document_member = MethodDocumenter.can_document_member
    MethodDocumenter.can_document_member = (  # ty:ignore[invalid-assignment]
        lambda member, membername, isattr, parent: (
            original_can_document_member(member, membername, isattr, parent)
            and callable(member)
        )
    )
    try:
        sphinx_app.build()
    finally:
        MethodDocumenter.can_document_member = original_can_document_member  # ty:ignore[invalid-assignment]
    if sphinx_app.statuscode != 0:
        raise HumanFacingException("Sphinx failed.")


@final
class DocumentationServer(Server):
    """
    Serve the documentation site.
    """

    def __init__(self, cache_directory: StrPath, *, user: User):
        super().__init__(user=user)
        self._cache_directory = resolve_path(cache_directory)
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise ServerNotStarted

    @override
    async def start(self) -> None:
        www_directory = self._cache_directory / "www"
        await _ensure_www_directory(
            www_directory, self._cache_directory / "cache", user=self._user
        )
        self._server = builtin.BuiltinServer(www_directory, user=self._user)
        await self._exit_stack.enter_async_context(self._server)

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
