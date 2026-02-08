"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.extension import ExtensionDefinition
from betty.extension._theme import jinja2_filters
from betty.extension.maps import Maps
from betty.extension.raspberry_mint.data import RaspberryMintConfiguration
from betty.extension.trees import Trees
from betty.extension.webpack import Webpack
from betty.extension.webpack.build import EntryPointProvider
from betty.jinja2 import Filters, Jinja2Provider
from betty.model import EntityDefinition
from betty.project import Project
from betty.project.generate import Generator
from betty.service.level import DataManufacturable, Manufacturable
from betty.service.requirement.project import require_project
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project.job import ProjectContext


@final
@ExtensionDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    depends_on={Webpack},
    comes_before={
        Maps,
        Trees,
    },
    theme=True,
    assets_directory=Path(__file__).parent / "assets",
)
class RaspberryMint(
    DataManufacturable[RaspberryMintConfiguration],
    Manufacturable,
    Jinja2Provider,
    Generator,
    EntryPointProvider[Project],
):
    """
    .. plugin:: extension:raspberry-mint.

    .. important::
        This extension requires :ref:`Node.js <installation-requirements-nodejs>`.

    Regions
    -------

    Raspberry Mint provides the following regions content providers may be configured for:

    - ``front-page-content``
      The main content for the front page.
    - ``front-page-summary``
      The page summary for the front page.
    - ``entity-page-content``
      The page content region for entity pages.
    - ``entity-page-content--{entity_type_id}``
      The page content region for entity pages of a specific public-facing entity type, where ``{entity_type_id}`` is the
      entity type ID. If no content is assigned to this region for an entity type, ``entity-page-content`` is used instead.

    Templating
    ----------

    Filters
    ^^^^^^^

    - :py:func:`associated_file_references <betty.extension._theme.associated_file_references>`
    - :py:func:`person_descendant_families <betty.extension._theme.person_descendant_families>`
    - :py:func:`person_timeline_events <betty.extension._theme.person_timeline_events>`

    """

    @private
    def __init__(
        self,
        *,
        project: Project,
        configuration: RaspberryMintConfiguration | None = None,
    ):
        super().__init__(services=project)
        self._configuration = (
            RaspberryMintConfiguration() if configuration is None else configuration
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[RaspberryMintConfiguration]:
        return RaspberryMintConfiguration

    @property
    def configuration(self) -> RaspberryMintConfiguration:
        """
        The configuration.
        """
        return self._configuration

    @override
    @classmethod
    @require_project
    async def new(
        cls,
        project: Project,
        data: RaspberryMintConfiguration | None = None,
        /,
    ) -> Self:
        return cls(configuration=data, project=project)

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        from betty.extension.raspberry_mint.jobs import (
            _GenerateLogo,
            _GenerateSearchIndex,
            _GenerateWebmanifest,
        )

        await scheduler.add(
            _GenerateLogo(),
            _GenerateSearchIndex(),
            _GenerateWebmanifest(),
        )

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self.services.configuration.root_path,
            self._configuration.primary_color,
            self._configuration.secondary_color,
            self._configuration.tertiary_color,
        )

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self.services)

    @property
    async def regions(self) -> set[str]:
        """
        The available regions.
        """
        return {
            "front-page-content",
            "front-page-summary",
            "entity-page-content",
            *{
                f"entity-page-content--{entity_type.id}"
                for entity_type in await self.services.plugins.plugins(EntityDefinition)
                if entity_type.public_facing
            },
        }


@final
class ColorStyle(Enum):
    """
    The available color styles.
    """

    LIGHT = "light"
    """
    A light style with a white background.
    """

    LIGHT_SECONDARY = "light-secondary"
    """
    A light style with a light shade of the secondary color for the background.
    """

    LIGHT_CONTRAST = "light-contrast"
    """
    A light style with a light shade of gray for the background.
    """

    DARK = "dark"
    """
    A dark style with a black background.
    """

    DARK_SECONDARY = "dark-secondary"
    """
    A dark style with a dark shade of the secondary color for the background.
    """


@final
class Breakpoint(Enum):
    """
    The theme's breakpoints.
    """

    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    XXL = "xxl"


@final
class JustifyContent(Enum):
    """
    How to justify content.
    """

    START = "start"
    END = "end"
    CENTER = "center"
    BETWEEN = "between"
    AROUND = "around"
    EVENLY = "evenly"


SINGLE_COLUMN_TEXT_WIDTH = {
    Breakpoint.XS: 12,
    Breakpoint.LG: 11,
    Breakpoint.XL: 10,
    Breakpoint.XXL: 9,
}
