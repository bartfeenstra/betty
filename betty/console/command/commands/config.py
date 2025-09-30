from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app import config as app_config
from betty.app.config import AppConfiguration
from betty.app.factory import AppDependentFactory
from betty.config.file import write_configuration_file
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale import DEFAULT_LOCALE, get_display_name
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    id="config",
    label=_("Configure Betty"),
)
class Config(AppDependentFactory, Command):
    """
    A command to manage Betty application configuration.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        parser.add_argument(
            "--locale",
            default=DEFAULT_LOCALE,
            help=localizer._(
                "Set the locale for Betty's user interface. This must be an IETF BCP 47 language tag."
            ),
        )
        return self._command_function

    async def _command_function(self, *, locale: str) -> None:
        localizers = await self._app.localizers
        updated_configuration = AppConfiguration()
        updated_configuration.update(self._app.configuration)
        updated_configuration.locale = locale
        self._app.user.localizer = localizers.get(locale)
        await self._app.user.message_information(
            _("Betty will talk to you in {locale}").format(
                locale=str(get_display_name(locale))
            )
        )

        await write_configuration_file(
            updated_configuration, app_config.CONFIGURATION_FILE_PATH
        )
