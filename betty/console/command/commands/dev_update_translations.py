from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
class DevUpdateTranslations(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to update all of Betty's translations.
    """

    _plugin_id = "dev-update-translations"
    _plugin_label = _("Update all existing translations for Betty itself")

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
        await translation.update_dev_translations()
