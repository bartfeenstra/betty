from __future__ import annotations  # noqa D100

import shutil
from asyncio import to_thread, gather
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse

    from betty.app import App


_LEGACY_CACHE_DIRECTORY_PATH = Path.home() / ".betty" / "cache"


@final
@CommandDefinition(
    id="clear-caches",
    label=_("Clear all caches"),
)
class ClearCaches(AppDependentFactory, Command):
    """
    A command to clear all Betty caches.
    """

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
        await gather(self._app.cache.clear(), self._clear_legacy_cache())
        await self._app.user.message_information(_("All caches cleared."))

    async def _clear_legacy_cache(self) -> None:
        # Before Betty 0.5, Betty stored its caches in the home directory. Clear those until Betty 0.6.
        with suppress(FileNotFoundError):
            await to_thread(shutil.rmtree, _LEGACY_CACHE_DIRECTORY_PATH)
