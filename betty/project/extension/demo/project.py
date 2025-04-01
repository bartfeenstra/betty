"""
Provide the demonstration project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.model.config import EntityReference
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.config import LocaleConfiguration, ProjectConfiguration
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


async def create_project(app: App, project_directory_path: Path) -> Project:
    """
    Create a new demonstration project.
    """
    from betty.project.extension.demo import Demo

    configuration = await ProjectConfiguration.new(
        project_directory_path / "betty.json",
        name=Demo.plugin_id(),
        license=PluginInstanceConfiguration("spdx-gpl-3--0-or-later"),
        title={
            "en-US": "A Betty demonstration",
            "de-DE": "Eine Betty-Demonstration",
            "fr-FR": "Une démonstration de Betty",
            "nl-NL": "Een demonstratie van Betty",
            "uk": "Демонстрація Betty",
        },
        author={
            "en-US": "Bart Feenstra and contributors",
            "fr-FR": "Bart Feenstra et contributeurs",
            "nl-NL": "Bart Feenstra en bijdragers",
            "uk": "Bart Feenstra і учасники",
        },
        extensions=[
            PluginInstanceConfiguration(Demo),
            PluginInstanceConfiguration(
                RaspberryMint,
                configuration=RaspberryMintConfiguration(
                    featured_entities=[
                        EntityReference(Place, "betty-demo-amsterdam"),
                        EntityReference(Person, "betty-demo-liberta-lankester"),
                        EntityReference(Place, "betty-demo-netherlands"),
                    ],
                ),
            ),
        ],
        locales=[
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
            LocaleConfiguration("ar"),
            LocaleConfiguration(
                "de-DE",
                alias="de",
            ),
            LocaleConfiguration(
                "fr-FR",
                alias="fr",
            ),
            LocaleConfiguration("he"),
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "uk",
                alias="uk",
            ),
        ],
    )
    return await Project.new(app, configuration=configuration)
