from __future__ import annotations  # noqa: D100

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App, AppData
from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_locale
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.factory import Manufacturable
from betty.locale import DEFAULT_LOCALE, to_language_tag
from betty.locale.localizable.gettext import _
from betty.portable.file import assert_load_file, dump_file

if TYPE_CHECKING:
    import argparse

    from babel import Locale


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
        localizers, serializers = await gather(
            self._app.localizers, gather(*self._app.serializers)
        )

        if AppData.FILE.exists():
            updated_configuration = AppData.data().porter.load(
                assert_load_file(serializers=serializers)(AppData.FILE)
            )
        else:
            updated_configuration = AppData()
        updated_configuration.locale = locale
        self._app.user.localizer = localizers.get(locale)
        await self._app.user.message_information(
            _("Betty will talk to you in {locale}").format(
                locale=locale.get_display_name() or to_language_tag(locale)
            )
        )

        await dump_file(
            AppData.data().porter.dump(updated_configuration),
            AppData.FILE,
            serializers=serializers,
        )
