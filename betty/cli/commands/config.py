from __future__ import annotations  # noqa D100

from logging import getLogger
from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app import config as app_config
from betty.app.config import AppConfiguration
from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.config import write_configuration_file
from betty.locale import DEFAULT_LOCALE, get_display_name
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.app import App


@final
class Config(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to manage Betty application configuration.
    """

    _plugin_id = "config"
    _plugin_label = _("Configure Betty")

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
        @click.option(
            "--locale",
            "locale",
            default=DEFAULT_LOCALE,
            help="Set the locale for Betty's user interface. This must be an IETF BCP 47 language tag.",
        )
        async def config(*, locale: str) -> None:
            logger = getLogger(__name__)
            updated_configuration = AppConfiguration()
            updated_configuration.update(self._app.configuration)
            updated_configuration.locale = locale
            new_localizer = await self._app.localizers.get(locale)
            logger.info(
                new_localizer._("Betty will talk to you in {locale}").format(
                    locale=get_display_name(locale)
                )
            )

            await write_configuration_file(
                updated_configuration, app_config.CONFIGURATION_FILE_PATH
            )

        return config
