from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.app import config as app_config
from betty.app.config import AppConfiguration
from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_locale
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.locale import DEFAULT_LOCALE, to_language_tag
from betty.locale.localizable.gettext import _
from betty.portable.file import dump_file
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement import require_app

if TYPE_CHECKING:
    import argparse

    from babel import Locale

    from betty.app import App


@final
@CommandDefinition("config", label=_("Configure Betty"))
class Config(ServiceLevelDependentSelfFactory, Command):
    """
    .. plugin:: command:config.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
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
            type=assertion_to_argument_type(assert_locale(), localizer=localizer),
        )
        return self._command_function

    async def _command_function(self, *, locale: Locale) -> None:
        localizers = await self._app.localizers
        updated_configuration = AppConfiguration.data().porter.load(
            AppConfiguration.data().porter.dump(self._app.configuration)
        )
        updated_configuration.locale = locale
        self._app.user.localizer = localizers.get(locale)
        await self._app.user.message_information(
            _("Betty will talk to you in {locale}").format(
                locale=locale.get_display_name() or to_language_tag(locale)
            )
        )

        await dump_file(
            AppConfiguration.data().porter.dump(updated_configuration),
            app_config.CONFIGURATION_FILE_PATH,
        )
