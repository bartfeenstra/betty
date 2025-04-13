from __future__ import annotations  # noqa D100

from asyncio import gather, to_thread
from contextlib import suppress
from shutil import rmtree
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command, project_option
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from pathlib import Path

    import asyncclick as click

    from betty.app import App
    from betty.project import Project


def _rmtree_if_exists(path: Path) -> None:
    with suppress(FileNotFoundError):
        rmtree(path)


@final
class Generate(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to generate a new site.
    """

    _plugin_id = "generate"
    _plugin_label = _("Generate a static site")

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
        @project_option
        async def generate(project: Project) -> None:
            from betty.project import generate, load

            await gather(
                load.load(project),
                to_thread(
                    _rmtree_if_exists, project.configuration.output_directory_path
                ),
            )
            await generate.generate(project)

        return generate
