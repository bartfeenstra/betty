from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_locale_identifier
from betty.cli.commands import command, Command, parameter_callback
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.app import App


@final
class DevNewTranslation(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to create a new translation for Betty itself.
    """

    _plugin_id = "dev-new-translation"
    _plugin_label = _("Create a new translation for Betty itself")

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
        @click.argument(
            "locale",
            required=True,
            callback=parameter_callback(assert_locale_identifier()),
        )
        async def dev_new_translation(locale: str) -> None:
            await translation.new_dev_translation(locale)

        return dev_new_translation
