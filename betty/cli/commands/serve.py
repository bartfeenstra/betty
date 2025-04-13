from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command, project_option
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import asyncclick as click

    from betty.app import App
    from betty.project import Project


@final
class Serve(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to serve a generated site.
    """

    _plugin_id = "serve"
    _plugin_label = _("Serve a generated site")

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
        async def serve(project: Project) -> None:
            from betty import serve

            async with await serve.BuiltinProjectServer.new_for_project(
                project
            ) as server:
                await server.show()
                while True:
                    await asyncio.sleep(999)

        return serve
