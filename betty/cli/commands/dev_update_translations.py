from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import asyncclick as click

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
        async def dev_update_translations() -> None:
            await translation.update_dev_translations()

        return dev_update_translations
