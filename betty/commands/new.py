from __future__ import annotations  # noqa: D100

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.assertions.locale import assert_locale
from betty.assertions.path import assert_path
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.enrichers.deriver import Deriver
from betty.enrichers.privatizer import Privatizer
from betty.enrichers.wiki import Wiki as WikiEnricher
from betty.factory import Arg1Manufacturable
from betty.load import LoaderManufacturer
from betty.loaders.gramps import FamilyTree, Gramps, GrampsData
from betty.locale import default_locale_tag, to_language_tag
from betty.localizables.gettext import _
from betty.localizables.static import StaticTranslations
from betty.machine_name import MachineName
from betty.nothing import Nothing
from betty.project import ProjectData
from betty.project.new import new
from betty.service_providers.http_api_doc import HttpApiDoc
from betty.service_providers.maps import Maps
from betty.service_providers.raspberry_mint import RaspberryMint
from betty.service_providers.trees import Trees
from betty.service_providers.webpack import Webpack
from betty.service_providers.wiki import Wiki as WikiExtension

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence

    from babel import Locale

    from betty.localizable import Localizable
    from betty.user import User


@final
@CommandDefinition("new", label=_("Create a new project"))
class New(Arg1Manufacturable[App], Command):
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
        serializers = await gather(*self._app.serializers)
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
                default=default_locale_tag,
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
                configuration.title.localize(
                    await self._app.localizers.get(default_locale)
                )
            )
            or Nothing,
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
    return StaticTranslations({
        locale: await user.ask_input(
            question.format(locale=locale.get_display_name() or to_language_tag(locale))
        )
        for locale in locales
    })


def _new_default_configuration() -> ProjectData:
    return ProjectData(
        enrichers=[
            Deriver,
            Privatizer,
            WikiEnricher,
        ],
        service_providers=[
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
