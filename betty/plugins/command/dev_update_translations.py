from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty.about import IS_DEVELOPMENT
from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.factory import Manufacturable
from betty.locale import translation
from betty.locale.localizable.gettext import _
from betty.requirement import UnmetRequirement

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable

    from betty.plugin.discovery import ResolvableDiscovery
    from betty.service_level import ServiceLevel


@final
@CommandDefinition(
    "dev-update-translations",
    label=_("Update all existing translations for Betty itself"),
)
class DevUpdateTranslations(Manufacturable, Command):
    """
    .. plugin:: command:dev-update-translations.
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
        return self._command_function

    async def _command_function(self) -> None:
        await translation.update_universe_translations()


def _discover(_: ServiceLevel) -> Iterable[ResolvableDiscovery[CommandDefinition]]:
    if not IS_DEVELOPMENT:
        raise UnmetRequirement("This is only available when developing Betty")
    yield DevUpdateTranslations
