from __future__ import annotations  # noqa D100

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
import betty.project.extension.demo as stddemo
from betty.project.extension.demo.project import create_project
from typing_extensions import override

if TYPE_CHECKING:
    from betty.app import App


@final
class Demo(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to run the demonstration site.
    """

    _plugin_id = "demo"
    _plugin_label = _("Explore a demonstration site")

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def click_command(self) -> click.Command:
        localizer = await self._app.localizer
        description = self.plugin_description()

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(localizer),
            help=description.localize(localizer)
            if description
            else self.plugin_label().localize(localizer),
        )
        @click.option(
            "--path",
            "path",
            help="The path to the project directory to generate the demonstration site into instead of serving the site in a browser window.",
        )
        @click.option(
            "--url",
            "url",
            help="The site's public project URL. Used only when `--path` is given.",
        )
        async def demo(*, path: str | None, url: str | None) -> None:
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
                async with project:
                    await stddemo.generate_with_cleanup(project)

        return demo
