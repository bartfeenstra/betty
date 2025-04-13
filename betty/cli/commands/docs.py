from __future__ import annotations  # noqa D100

import asyncio
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty import documentation
from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import asyncclick as click

    from betty.app import App


@final
class Docs(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to view Betty's documentation.
    """

    _plugin_id = "docs"
    _plugin_label = _("View the documentation")

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
        async def docs() -> None:
            server = documentation.DocumentationServer(
                self._app.binary_file_cache.path,
                localizer=await self._app.localizer,
            )
            async with server:
                await server.show()
                while True:
                    await asyncio.sleep(999)

        return docs
