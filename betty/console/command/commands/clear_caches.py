from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import argparse

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
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        await self._app.cache.clear()
        await self._app.user.message_information(_("All caches cleared."))
