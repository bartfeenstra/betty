from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.assertion import assert_str, assert_path, assert_locale
from betty.config.file import write_configuration_file
from betty.locale import get_display_name, DEFAULT_LOCALE
from betty.locale.localizable import _, StaticTranslationsMapping, Localizable
from betty.machine_name import machinify, assert_machine_name
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.config import (
    LocaleConfiguration,
    ProjectConfiguration,
    EntityTypeConfiguration,
)
from betty.project.extension.deriver import Deriver
from betty.project.extension.gramps import Gramps
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
)
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.privatizer import Privatizer
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.wiki import Wiki
from betty.requirement import AllRequirements

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.app import App
    from betty.user import User


async def new(app: App) -> None:
    """
    Create a new project.
    """
    localizers = await app.localizers

    extensions = (
        Deriver,
        HttpApiDoc,
        Maps,
        Privatizer,
        RaspberryMint,
        Trees,
        # Enable the Webpack extension explicitly for the test's mock to work.
        Webpack,
        Wiki,
    )
    AllRequirements(
        *[await extension.plugin.cls.requirement(app=app) for extension in extensions]
    ).assert_met()

    configuration_file_path = await app.user.ask_input(
        _("Where do you want to save your project's configuration file?"),
        assertion=_assert_project_configuration_file_path,
    )
    configuration = ProjectConfiguration(
        configuration_file_path,
        entity_types=[
            EntityTypeConfiguration(Person, generate_html_list=True),
            EntityTypeConfiguration(Event, generate_html_list=True),
            EntityTypeConfiguration(Place, generate_html_list=True),
            EntityTypeConfiguration(Source, generate_html_list=True),
        ],
    )

    configuration.extensions.enable(*extensions)

    configuration.locales.replace(
        LocaleConfiguration(
            await app.user.ask_input(
                _(
                    "Which language should your project site be generated in? Enter an IETF BCP 47 language code."
                ),
                default=DEFAULT_LOCALE,
                assertion=assert_locale(),
            )
        )
    )
    while await app.user.ask_confirmation(_("Do you want to add another locale?")):
        configuration.locales.append(
            LocaleConfiguration(
                await app.user.ask_input(
                    _(
                        "Which language should your project site be generated in? Enter an IETF BCP 47 language code."
                    ),
                    assertion=assert_locale(),
                )
            )
        )
    locales = list(configuration.locales)

    configuration.title = await _user_input_static_translations(
        app.user, locales, _("What is your project called in {locale}?")
    )

    configuration.name = await app.user.ask_input(
        _("What is your project's machine name?"),
        default=str(
            machinify(
                configuration.title.localize(
                    localizers.get(configuration.locales.default.locale)
                )
            )
        ),
        assertion=assert_machine_name(),
    )

    configuration.author = await _user_input_static_translations(
        app.user, locales, _("What is the project author called in {locale}?")
    )

    configuration.url = await app.user.ask_input(
        _("At which URL will your site be published?"),
        default="https://example.com",
        assertion=_assert_url,
    )

    if await app.user.ask_confirmation(_("Do you want to load a Gramps family tree?")):
        gramps_requirement = await Gramps.requirement(app=app)
        if gramps_requirement is not None:
            gramps_requirement.assert_met()
        configuration.extensions.append(
            PluginInstanceConfiguration(
                Gramps.plugin,
                configuration=GrampsConfiguration(
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

    await write_configuration_file(configuration, configuration.configuration_file_path)
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
    user: User, locales: Sequence[str], question: Localizable
) -> StaticTranslationsMapping:
    return {
        locale: await user.ask_input(
            question.format(locale=get_display_name(locale) or locale)
        )
        for locale in locales
    }
