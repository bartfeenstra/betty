from __future__ import annotations  # noqa D100

from asyncio import gather, to_thread
from contextlib import suppress
from shutil import rmtree
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.project import add_project_argument
from betty.console.command import Command, CommandFunction
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

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
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        from betty.project import generate, load

        async with project:
            await gather(
                load.load(project),
                to_thread(
                    _rmtree_if_exists, project.configuration.output_directory_path
                ),
            )
            await generate.generate(project)
