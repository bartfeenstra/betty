"""
Provide the demonstration project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.content_provider.content_providers import PlainText, PlainTextConfiguration
from betty.locale.localizable.gettext import _
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)
from betty.project import Project
from betty.project.config import (
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    ExtensionInstanceConfigurationMapping,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    ProjectConfiguration,
)
from betty.project.extension.demo.content_provider import _FrontPageContent
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.project.extension.raspberry_mint.content_provider import (
    FeaturedEntities,
    Section,
    SectionConfiguration,
)
from betty.project.extension.theme.config import RegionalContentConfiguration

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


async def create_project(app: App, project_directory_path: Path) -> Project:
    """
    Create a new demonstration project.
    """
    from betty.project.extension.demo import Demo

    configuration = ProjectConfiguration(
        name=Demo.plugin().id,
        license=PluginInstanceConfiguration("spdx-gpl-3--0-or-later"),
        title=_("A Betty demonstration"),
        author=_("Bart Feenstra and contributors"),
        extensions=ExtensionInstanceConfigurationMapping(
            [
                PluginInstanceConfiguration(Demo),
                PluginInstanceConfiguration(
                    RaspberryMint,
                    RaspberryMintConfiguration(
                        regional_content=RegionalContentConfiguration(
                            {
                                "front-page-content": PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(_FrontPageContent),
                                        PluginInstanceConfiguration(
                                            Section,
                                            SectionConfiguration(
                                                heading=_("Start exploring..."),
                                                content=[
                                                    PluginInstanceConfiguration(
                                                        FeaturedEntities,
                                                        EntityReferenceSequence(
                                                            [
                                                                EntityReference(
                                                                    Place,
                                                                    "betty-demo-amsterdam",
                                                                ),
                                                                EntityReference(
                                                                    Person,
                                                                    "betty-demo-liberta-lankester",
                                                                ),
                                                                EntityReference(
                                                                    Place,
                                                                    "betty-demo-netherlands",
                                                                ),
                                                            ],
                                                        ),
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ]
                                ),
                                "front-page-summary": PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(
                                            PlainText,
                                            PlainTextConfiguration(
                                                _(
                                                    "Betty is an application that takes a family tree and builds a website out of it, much like the one you are viewing right now. The more information your genealogical research contains, the more interactivity Betty can add to your site, such as media galleries, maps, and browsable family trees."
                                                )
                                            ),
                                        ),
                                    ]
                                ),
                            }
                        ),
                    ),
                ),
            ]
        ),
        entity_types=EntityTypeConfigurationMapping(
            [
                EntityTypeConfiguration(Person, generate_html_list=True),
                EntityTypeConfiguration(Event, generate_html_list=True),
                EntityTypeConfiguration(Place, generate_html_list=True),
                EntityTypeConfiguration(Source, generate_html_list=True),
            ]
        ),
        locales=LocaleConfigurationMapping(
            [
                LocaleConfiguration("en-US", alias="en"),
                LocaleConfiguration("de-DE", alias="de"),
                LocaleConfiguration("fr-FR", alias="fr"),
                LocaleConfiguration("nl-NL", alias="nl"),
                LocaleConfiguration("ru-RU", alias="ru"),
                LocaleConfiguration("uk"),
            ]
        ),
    )
    return Project(
        app, project_directory_path / "betty.json", configuration=configuration
    )
