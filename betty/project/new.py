"""
Create new projects.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING

from betty.extension import ExtensionManufacturer
from betty.locale.localizable.gettext import _
from betty.plugins.enricher.deriver import Deriver
from betty.plugins.enricher.privatizer import Privatizer
from betty.plugins.enricher.wiki import Wiki
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.plugins.extension.maps import Maps
from betty.plugins.extension.raspberry_mint import (
    RaspberryMint,
    RaspberryMintConfiguration,
)
from betty.plugins.extension.raspberry_mint.default import regional_content
from betty.plugins.extension.trees import Trees
from betty.plugins.extension.webpack import Webpack
from betty.portable.file import dump_file
from betty.project.data import ProjectConfiguration

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from betty.app import App
    from betty.locale.localize import Localizer


async def new(
    app: App, configuration: ProjectConfiguration, configuration_file: Path, /
) -> None:
    """
    Create a new project.
    """
    await dump_file(
        configuration.data().porter.dump(configuration),
        configuration_file,
        serializers=await gather(*app.serializers),
    )
    await app.user.message_information(
        _("Saved your project to {configuration_file}.").format(
            configuration_file=str(configuration_file)
        )
    )


def new_default_configuration(
    *, localizers: Collection[Localizer]
) -> ProjectConfiguration:
    """
    Create new default project configuration.
    """
    return ProjectConfiguration(
        enrichers=[
            Deriver,
            Privatizer,
            Wiki,
        ],
        extensions=[
            HttpApiDoc,
            Maps,
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content=regional_content(localizers=localizers)
                ),
            ),
            Trees,
            # Enable the Webpack extension explicitly for the test's mock to work.
            Webpack,
        ],
        title="Betty",
        url="https://example.com",
    )
