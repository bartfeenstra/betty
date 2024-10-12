from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import asyncclick as click
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
        async def demo() -> None:
            from betty.project.extension.demo.serve import DemoServer

            async with DemoServer(app=self._app) as server:
                await server.show()
                while True:
                    await asyncio.sleep(999)

        return demo
