from __future__ import annotations  # noqa: D100

import shutil
from asyncio import gather, to_thread
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.locale.localizable.gettext import _
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse


_LEGACY_CACHE_DIRECTORY_PATH = Path.home() / ".betty" / "cache"


@final
@CommandDefinition("clear-caches", label=_("Clear all caches"), aliases=["cc"])
class ClearCaches(Manufacturable, Command):
    """
    .. plugin:: command:clear-caches.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
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
