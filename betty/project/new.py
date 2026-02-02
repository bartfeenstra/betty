from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.assertion import assert_locale, assert_path, assert_str
from betty.extension import Extension, ExtensionDefinition
from betty.extension.deriver import Deriver
from betty.extension.gramps import Gramps
from betty.extension.gramps.config import FamilyTreeConfiguration, GrampsConfiguration
from betty.extension.http_api_doc import HttpApiDoc
from betty.extension.maps import Maps
from betty.extension.privatizer import Privatizer
from betty.extension.raspberry_mint import RaspberryMint
from betty.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.extension.raspberry_mint.config.default import regional_content
from betty.extension.trees import Trees
from betty.extension.webpack import Webpack
from betty.extension.wiki import Wiki
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.machine_name import assert_machine_name, machinify
from betty.plugin.config import PluginConfiguration, ResolvablePluginConfiguration
from betty.portable.file import dump_file
from betty.project.config import ProjectConfiguration

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence
    from pathlib import Path

    from babel import Locale

    from betty.app import App
    from betty.locale.localizable import Localizable
    from betty.user import User


async def new(app: App) -> None:
    """
    Create a new project.
    """
    await app.plugins.plugins(ExtensionDefinition)
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

    extensions: MutableSequence[
        ResolvablePluginConfiguration[ExtensionDefinition, Extension]
    ] = [
        Deriver,
        HttpApiDoc,
        Maps,
        Privatizer,
        PluginConfiguration(
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
        Wiki,
    ]

    title = await _user_input_static_translations(
        app.user, locales, _("What is your project called in {locale}?")
    )

    name = await app.user.ask_input(
        _("What is your project's machine name?"),
        default=str(machinify(title.localize(localizers.get(locales[0])))),
        assertion=assert_machine_name(),
    )

    author = await _user_input_static_translations(
        app.user, locales, _("What is the project author called in {locale}?")
    )

    url = await app.user.ask_input(
        _("At which URL will your site be published?"),
        default="https://example.com",
        assertion=_assert_url,
    )

    if await app.user.ask_confirmation(_("Do you want to load a Gramps family tree?")):
        extensions.append(
            PluginConfiguration(
                Gramps,
                GrampsConfiguration(
                    family_trees=[
                        FamilyTreeConfiguration(
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
        entity_types=[
            Person,
            Event,
            Place,
            Source,
        ],
        extensions=extensions,
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


def _assert_url(value: Any) -> str:
    url = assert_str()(value)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "http"
    return f"{scheme}://{parsed_url.netloc}{parsed_url.path}"


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
        }
    )
