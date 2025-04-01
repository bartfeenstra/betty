from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cache.memory import MemoryCache
from betty.console.project import add_project_argument
from betty.console.command import Command, CommandFunction
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project import ProjectContext

if TYPE_CHECKING:
    import argparse

    from betty.app import App
    from betty.project import Project


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

        async with (
            project,
            project.app.user.message_progress(_("Generating site...")) as progress,
        ):
            job_context = ProjectContext(
                project, cache=MemoryCache(), progress=progress
            )
            await load.load(project, job_context=job_context)
            await generate.generate(project, job_context=job_context)
