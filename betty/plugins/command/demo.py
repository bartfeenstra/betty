from __future__ import annotations  # noqa: D100

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

import betty.plugins.extension.demo as stddemo
from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.job import Context
from betty.locale.localizable.gettext import _
from betty.plugins.extension.demo.project import create_project
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse


@final
@CommandDefinition("demo", label=_("Explore a demonstration site"))
class Demo(Manufacturable, Command):
    """
    .. plugin:: command:demo.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require(App)
    async def new(cls, app: App, /) -> Self:
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
        from betty.plugins.extension.demo.serve import DemoServer

        if path is None:
            async with DemoServer(app=self._app) as server:
                await server.show()
                while True:
                    await asyncio.sleep(999)
        else:
            project = await create_project(self._app, Path(path), url=url)
            async with (
                project,
                project.upstream.user.message_progress(
                    _("Generating site...")
                ) as progress,
            ):
                context = Context(progress=progress)
                await stddemo.generate_with_cleanup(project, context=context)
