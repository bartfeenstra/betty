from __future__ import annotations  # noqa: D100

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.assertion import assert_locale, assert_path
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.factory import Manufacturable
from betty.load import (
    LoaderManufacturer,
)
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.machine_name import MachineName
from betty.plugins.enricher.deriver import Deriver
from betty.plugins.enricher.privatizer import Privatizer
from betty.plugins.enricher.wiki import Wiki as WikiEnricher
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.plugins.extension.maps import Maps
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.trees import Trees
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.wiki import Wiki as WikiExtension
from betty.plugins.loader.gramps import FamilyTree, Gramps, GrampsData
from betty.project import ProjectData
from betty.project.new import new
from betty.typing import Void

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence

    from babel import Locale

    from betty.locale.localizable import Localizable
    from betty.user import User


@final
@CommandDefinition("new", label=_("Create a new project"))
class New(Manufacturable, Command):
    """
    .. plugin:: command:new.
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
        localizers, translations, serializers = await gather(
            self._app.localizers, self._app.translations, gather(*self._app.serializers)
        )
        configuration = _new_default_configuration()

        configuration_file = await self._app.user.ask_input(
            _("Where do you want to save your project's configuration file?"),
            assertion=assert_path(),
        )
        if not configuration_file.suffix:
            configuration_file /= f"betty{serializers[0].media_type().extensions[0]}"

        configuration.locales = [
            await self._app.user.ask_input(
                _(
                    "Which language should your project site be generated in? Enter a language code."
                ),
                default=DEFAULT_LOCALE_TAG,
                assertion=assert_locale(),
            )
        ]
        while await self._app.user.ask_confirmation(
            _("Do you want to add another locale?")
        ):
            configuration.locales.add(
                await self._app.user.ask_input(
                    _(
                        "Which language should your project site be generated in? Enter a language code."
                    ),
                    assertion=assert_locale(),
                )
            )
        locales = tuple(configuration.locales.keys())
        default_locale = locales[0]

        configuration.title = await _user_input_static_translations(
            self._app.user, locales, _("What is your project called in {locale}?")
        )

        configuration.name = await self._app.user.ask_input(
            _("What is your project's machine name?"),
            default=MachineName.machinify(
                configuration.title.localize(localizers.get(default_locale))
            )
            or Void,
        )

        configuration.author = await _user_input_static_translations(
            self._app.user, locales, _("What is the project author called in {locale}?")
        )

        configuration.url = await self._app.user.ask_input(
            _("At which URL will your site be published?"), default=configuration.url
        )

        if await self._app.user.ask_confirmation(
            _("Do you want to load a Gramps family tree?")
        ):
            configuration.loaders.add(
                LoaderManufacturer(
                    Gramps,
                    GrampsData(
                        family_trees=[
                            FamilyTree(
                                await self._app.user.ask_input(
                                    _(
                                        "What is the path to your exported Gramps family tree file?"
                                    ),
                                    assertion=assert_path(),
                                )
                            )
                        ]
                    ),
                )
            )

        await new(self._app, configuration, configuration_file)


async def _user_input_static_translations(
    user: User, locales: Sequence[Locale], question: Localizable
) -> StaticTranslations:
    return StaticTranslations(
        {
            locale: await user.ask_input(
                question.format(
                    locale=locale.get_display_name() or to_language_tag(locale)
                )
            )
            for locale in locales
        }  # ty:ignore[invalid-argument-type]
    )


def _new_default_configuration() -> ProjectData:
    return ProjectData(
        enrichers=[
            Deriver,
            Privatizer,
            WikiEnricher,
        ],
        extensions=[
            HttpApiDoc,
            Maps,
            RaspberryMint,
            Trees,
            # Enable the Webpack extension explicitly for the test's mock to work.
            Webpack,
            WikiExtension,
        ],
        title="Betty",
        url="https://example.com",
    )
