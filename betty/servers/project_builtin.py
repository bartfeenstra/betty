"""
The built-in server.
"""

from __future__ import annotations

from asyncio import to_thread
from typing import Self, final, override

from betty.factory import Arg1Manufacturable
from betty.localizables.gettext import _
from betty.plugin.cls import Plugin
from betty.project import Project
from betty.server import Server, ServerDefinition
from betty.servers.builtin import BuiltinServer


@final
@ServerDefinition(
    "builtin",
    label=_("Built-in"),
    description=_(
        "Serve your site using Python's built-in web server. This is for local use only, and unsafe for publishing your site."
    ),
    auto=True,
    after=lambda _: True,
    requires=[Project.require],
)
class ProjectBuiltinServer(
    Server, Arg1Manufacturable[Project], Plugin[ServerDefinition]
):
    """
    .. plugin:: server:builtin.
    """

    def __init__(self, project: Project, /) -> None:
        super().__init__(user=project.upstream.user)
        self._server = BuiltinServer(
            project.www_directory,
            root_path=project.root_path,
            user=project.upstream.user,
        )
        self._www_directory = project.www_directory

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project)

    @override
    @property
    def public_url(self) -> str:
        return self._server.public_url

    @override
    async def start(self) -> None:
        await to_thread(self._www_directory.mkdir, exist_ok=True, parents=True)
        await self._server.start()

    @override
    async def stop(self) -> None:
        await self._server.stop()
