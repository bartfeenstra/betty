"""
Provide the demonstration project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.content_provider.content_providers import Render, RenderConfiguration
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localize import LocalizerRepository
from betty.media_type.media_types import HTML
from betty.model.config import EntityReference
from betty.plugin.config import PluginConfiguration
from betty.project import Project
from betty.project.config import (
    ExtensionInstanceConfigurationMapping,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    ProjectConfiguration,
)
from betty.project.extension.demo.content_provider import _IncompleteTranslationWarning
from betty.project.extension.raspberry_mint import (
    Breakpoint,
    RaspberryMint,
)
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.project.extension.raspberry_mint.config.default import regional_content
from betty.project.extension.raspberry_mint.content_provider import (
    Columns,
    ColumnsConfiguration,
    EntityCard,
    Section,
    SectionConfiguration,
)

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


async def create_project(app: App, project_directory_path: Path) -> Project:
    """
    Create a new demonstration project.
    """
    from betty.project.extension.demo import Demo

    translations = await app.translations
    localizer_repository = LocalizerRepository(translations)
    localizers = [localizer_repository.get(locale) for locale in translations.locales]

    configuration = ProjectConfiguration(
        name=Demo.plugin().id,
        license=PluginConfiguration("spdx-gpl-3--0-or-later"),
        title=_("A Betty demonstration"),
        author=_("Bart Feenstra and contributors"),
        url="https://example.com",
        extensions=ExtensionInstanceConfigurationMapping(
            [
                PluginConfiguration(Demo),
                PluginConfiguration(
                    RaspberryMint,
                    RaspberryMintConfiguration(
                        regional_content={
                            **regional_content(localizers=localizers),
                            "front-page-content": [
                                PluginConfiguration(
                                    Columns,
                                    ColumnsConfiguration(
                                        [[_IncompleteTranslationWarning]]
                                    ),
                                ),
                                PluginConfiguration(
                                    Section,
                                    SectionConfiguration(
                                        PluginConfiguration(
                                            Columns,
                                            ColumnsConfiguration(
                                                [
                                                    [
                                                        PluginConfiguration(
                                                            Render,
                                                            RenderConfiguration(
                                                                Chain(
                                                                    "<h2>",
                                                                    _("Get started"),
                                                                    "</h2>"
                                                                    '<a href="https://betty.readthedocs.io/" class="view-more">',
                                                                    _(
                                                                        "Read the documentation"
                                                                    ),
                                                                    "</a>",
                                                                    '<a href="https://github.com/bartfeenstra/betty/" class="view-more">',
                                                                    _("View the code"),
                                                                    "</a>",
                                                                ),
                                                                HTML,
                                                            ),
                                                        ),
                                                        PluginConfiguration(
                                                            Render,
                                                            RenderConfiguration(
                                                                Chain(
                                                                    "<p>",
                                                                    _(
                                                                        "Betty was named after <a href=\"betty-entity://person/betty-demo-liberta-lankester\">Liberta 'Betty' Lankester</a>, and this website shows a small sample of her family history. You can browse the pages about her and some of her family to get an idea of what a Betty site looks like."
                                                                    ),
                                                                    "</p>",
                                                                ),
                                                                HTML,
                                                            ),
                                                        ),
                                                    ]
                                                ],
                                                width={
                                                    Breakpoint.XS: [12, 12],
                                                    Breakpoint.MD: [5, 6],
                                                    Breakpoint.LG: [4, 7],
                                                },
                                            ),
                                        ),  # ty:ignore[invalid-argument-type]
                                        heading=_("Welcome"),
                                        visually_hide_heading=True,
                                    ),
                                ),
                                PluginConfiguration(
                                    Section,
                                    SectionConfiguration(
                                        PluginConfiguration(
                                            Columns,
                                            ColumnsConfiguration(
                                                [
                                                    [
                                                        PluginConfiguration(
                                                            EntityCard,
                                                            EntityReference(
                                                                Place,
                                                                "betty-demo-amsterdam",
                                                            ),
                                                        )
                                                    ],
                                                    [
                                                        PluginConfiguration(
                                                            EntityCard,
                                                            EntityReference(
                                                                Person,
                                                                "betty-demo-liberta-lankester",
                                                            ),
                                                        )
                                                    ],
                                                    [
                                                        PluginConfiguration(
                                                            EntityCard,
                                                            EntityReference(
                                                                Place,
                                                                "betty-demo-netherlands",
                                                            ),
                                                        )
                                                    ],
                                                ],
                                                width={
                                                    Breakpoint.XS: [12, 12, 12],
                                                    Breakpoint.MD: [6, 6, 6],
                                                    Breakpoint.LG: [4, 4, 4],
                                                },
                                            ),
                                        ),  # ty:ignore[invalid-argument-type]
                                        heading=_("Explore a family history..."),
                                    ),
                                ),
                            ],
                            "front-page-summary": [
                                PluginConfiguration(
                                    Render,
                                    RenderConfiguration(
                                        _(
                                            "Betty is an application that takes a family tree and builds a website out of it, much like the one you are viewing right now. The more information your genealogical research contains, the more interactivity Betty can add to your site, such as media galleries, maps, and browsable family trees."
                                        )
                                    ),
                                ),
                            ],
                        }
                    ),
                ),
            ]
        ),
        entity_types=[
            Person,
            Event,
            Place,
            Source,
        ],
        locales=LocaleConfigurationMapping(
            [
                # The first configured locale is the project default.
                LocaleConfiguration(DEFAULT_LOCALE),
                *[
                    LocaleConfiguration(locale)
                    for locale in translations.locales
                    if locale != DEFAULT_LOCALE
                ],
            ]
        ),
    )
    return Project(
        app, project_directory_path / "betty.json", configuration=configuration
    )
