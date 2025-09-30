from __future__ import annotations  # noqa D100

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

import betty.project.extension.demo as stddemo
from betty.app.factory import AppDependentFactory
from betty.cache.memory import MemoryCache
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale.localizable import _
from betty.project import ProjectContext
from betty.project.extension.demo.project import create_project

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    id="demo",
    label=_("Explore a demonstration site"),
)
class Demo(AppDependentFactory, Command):
    """
    A command to run the demonstration site.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        parser.add_argument(
            "--path",
            help="The path to the project directory to generate the demonstration site into instead of serving the site in a browser window.",
        )
        parser.add_argument(
            "--url",
            help="The site's public project URL. Used only when `--path` is given.",
        )
        return self._command_function

    async def _command_function(self, *, path: str | None, url: str | None) -> None:
        from betty.project.extension.demo.serve import DemoServer

        if path is None:
            async with DemoServer(app=self._app) as server:
                await server.show()
                while True:
                    await asyncio.sleep(999)
        else:
            project = await create_project(self._app, Path(path))
            if url is not None:
                project.configuration.url = url
            async with (
                project,
                project.app.user.message_progress(_("Generating site...")) as progress,
            ):
                job_context = ProjectContext(
                    project, cache=MemoryCache(), progress=progress
                )
                await stddemo.generate_with_cleanup(project, job_context=job_context)
