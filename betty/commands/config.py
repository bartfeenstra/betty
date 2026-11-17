from __future__ import annotations  # noqa: D100

from asyncio import to_thread
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App, AppConfig
from betty.argparse import validator_to_argument_type
from betty.console import Command, CommandDefinition, CommandResult
from betty.factory import Manufacturable
from betty.file import read, write
from betty.locale import default_locale, to_language_tag
from betty.localizables.gettext import _
from betty.serializers.json import Json
from betty.user import Severity
from betty.validators.locale import is_locale

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from babel import Locale

    from betty.console import CommandFunction


@final
@CommandDefinition("config", label=_("Configure Betty"))
class Config(Manufacturable, Command):
    """
    .. plugin:: command:config.
    """

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
        parser.add_argument(
            "--locale",
            default=default_locale,
            help=self._app.ui.localizer.translate._(
                "Set the locale for Betty's user interface. This must be an IETF BCP 47 language tag."
            ),
            type=validator_to_argument_type(is_locale),
        )
        return self._command_function

    async def _command_function(self, *, locale: Locale) -> CommandResult:
        serializer = Json()
        porter = AppConfig.definition.porter

        if AppConfig.file.exists():
            updated_configuration = porter.load(
                serializer.load(await read(AppConfig.file))
            )
        else:
            updated_configuration = AppConfig()
        updated_configuration.locale = locale
        await self._app.ui.message(
            _("Next time, Betty will talk to you in {locale}").format(
                locale=locale.get_display_name() or to_language_tag(locale)
            ),
            Severity.CONFIRM,
        )

        await to_thread(AppConfig.file.parent.mkdir, exist_ok=True, parents=True)
        await write(AppConfig.file, serializer.dump(porter.dump(updated_configuration)))
