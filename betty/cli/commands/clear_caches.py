from __future__ import annotations  # noqa D100

import logging
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
class ClearCaches(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to clear all Betty caches.
    """

    _plugin_id = "clear-caches"
    _plugin_label = _("Clear all caches")

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
        async def clear_caches() -> None:
            await self._app.cache.clear()
            logging.getLogger(__name__).info(localizer._("All caches cleared."))

        return clear_caches
