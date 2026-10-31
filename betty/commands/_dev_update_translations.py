from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty import gettext
from betty.commands._dev import DevCommand
from betty.console import CommandDefinition, CommandResult
from betty.job import Context

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from betty.console import CommandFunction


@final
@CommandDefinition(
    "dev-update-translations", label="Update all existing translations for Betty itself"
)
class DevUpdateTranslations(DevCommand):
    """
    .. plugin:: command:dev-update-translations.
    """

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> CommandResult:
        async with self._app.ui.progress("Updating translations...") as progress:
            context = Context(progress=progress)
            await gettext.update_builtin_translations(context=context)
