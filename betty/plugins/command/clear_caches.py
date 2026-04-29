from __future__ import annotations  # noqa: D100

import shutil
from asyncio import gather, to_thread
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.argparse import add_yes_argument
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    import argparse

    from betty.project import Project


_LEGACY_CACHE_DIRECTORY = Path.home() / ".betty" / "cache"


async def _clear_legacy_cache() -> None:
    # Before Betty 0.5, Betty stored its caches in the home directory. Clear those until Betty 0.6.
    with suppress(FileNotFoundError):
        await to_thread(shutil.rmtree, _LEGACY_CACHE_DIRECTORY)


@final
@CommandDefinition("clear-caches", label=_("Clear all caches"), aliases=["cc"])
class ClearCaches(Manufacturable, Command):
    """
    .. plugin:: command:clear-caches.
    """

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        add_yes_argument(parser, localizer=self._app.user.localizer)
        return await add_project_argument(
            parser, self._command_function, self._app, required=False
        )

    async def _command_function(self, project: Project | None, yes: bool) -> None:
        if not yes:
            yes = await self._app.user.ask_confirmation(
                _("Are you sure you want to clear all caches?")
            )
        if yes:
            tasks = [
                self._app.cache.clear(),
                self._app.binary_file_cache.clear(),
                _clear_legacy_cache(),
            ]
            if project is not None:
                tasks.append(project.cache.clear())
                tasks.append(project.binary_file_cache.clear())
            await gather(*tasks)
            await self._app.user.message_information(_("All caches cleared."))
