from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Any

from betty.assertion import assert_locale, assert_path, assert_url
from betty.extension import ExtensionDefinition, ExtensionManufacturer
from betty.load import (
    EnricherDefinition,
    LoaderDefinition,
    LoaderManufacturer,
)
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.machine_name import MachineName
from betty.plugins.enricher.deriver import Deriver
from betty.plugins.enricher.privatizer import Privatizer
from betty.plugins.enricher.wiki import Wiki
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.plugins.extension.maps import Maps
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.raspberry_mint.data import RaspberryMintConfiguration
from betty.plugins.extension.raspberry_mint.default import regional_content
from betty.plugins.extension.trees import Trees
from betty.plugins.extension.webpack import Webpack
from betty.plugins.loader.gramps import FamilyTree, Gramps, GrampsConfiguration
from betty.portable.file import dump_file
from betty.project.data import ProjectConfiguration
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence
    from pathlib import Path

    from babel import Locale

    from betty.app import App
    from betty.locale.localizable import Localizable
    from betty.plugin.factory import ResolvablePluginManufacturer
    from betty.user import User


async def new(app: App) -> None:
    """
    Create a new project.
    """
    localizers = await app.localizers

    configuration_file_path = await app.user.ask_input(
        _("Where do you want to save your project's configuration file?"),
        assertion=_assert_project_configuration_file_path,
    )

    locales = [
        await app.user.ask_input(
            _(
                "Which language should your project site be generated in? Enter a language code."
            ),
            default=DEFAULT_LOCALE_TAG,
            assertion=assert_locale(),
        )
    ]
    while await app.user.ask_confirmation(_("Do you want to add another locale?")):
        locales.append(
            await app.user.ask_input(
                _(
                    "Which language should your project site be generated in? Enter a language code."
                ),
                assertion=assert_locale(),
            )
        )

    extensions: MutableSequence[ResolvablePluginManufacturer[ExtensionDefinition]] = [
        HttpApiDoc,
        Maps,
        ExtensionManufacturer(
            RaspberryMint,
            RaspberryMintConfiguration(
                regional_content=regional_content(
                    localizers=[localizers.get(locale) for locale in locales]
                )
            ),
        ),
        Trees,
        # Enable the Webpack extension explicitly for the test's mock to work.
        Webpack,
    ]
    loaders: MutableSequence[ResolvablePluginManufacturer[LoaderDefinition]] = []
    enrichers: MutableSequence[ResolvablePluginManufacturer[EnricherDefinition]] = [
        Deriver,
        Privatizer,
        Wiki,
    ]

    title = await _user_input_static_translations(
        app.user, locales, _("What is your project called in {locale}?")
    )

    name = await app.user.ask_input(
        _("What is your project's machine name?"),
        default=MachineName.machinify(title.localize(localizers.get(locales[0])))
        or Void,
        assertion=MachineName,
    )

    author = await _user_input_static_translations(
        app.user, locales, _("What is the project author called in {locale}?")
    )

    url = await app.user.ask_input(
        _("At which URL will your site be published?"),
        default="https://example.com",
        assertion=assert_url(),
    )

    if await app.user.ask_confirmation(_("Do you want to load a Gramps family tree?")):
        loaders.append(
            LoaderManufacturer(
                Gramps,
                GrampsConfiguration(
                    family_trees=[
                        FamilyTree(
                            await app.user.ask_input(
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

    configuration = ProjectConfiguration(
        author=author,
        locales=locales,
        enrichers=enrichers,
        entity_types=[
            Person,
            Event,
            Place,
            Source,
        ],
        extensions=extensions,
        loaders=loaders,
        name=name,
        title=title,
        url=url,
    )
    await dump_file(
        configuration.data().porter.dump(configuration), configuration_file_path
    )
    await app.user.message_information(
        _("Saved your project to {configuration_file}.").format(
            configuration_file=str(configuration_file_path)
        )
    )


def _assert_project_configuration_file_path(value: Any) -> Path:
    configuration_file_path = assert_path()(value)
    if not configuration_file_path.suffix:
        configuration_file_path /= "betty.yaml"
    return configuration_file_path


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
