"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.config.factory import ConfigurationDependentSelfFactory
from betty.jinja2 import Filters, Jinja2Provider
from betty.model import EntityDefinition
from betty.project.extension import ExtensionDefinition
from betty.project.extension._theme import jinja2_filters
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.project.generate import Generator
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext
    from betty.service.level.factory import AnyFactoryTarget


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
    assets_directory_path=Path(__file__).parent / "assets",
)
class RaspberryMint(
    ConfigurationDependentSelfFactory[RaspberryMintConfiguration],
    ProjectDependentSelfFactory,
    Jinja2Provider,
    Generator,
    EntryPointProvider,
):
    """
    .. plugin:: extension:raspberry-mint.

    .. important::
        This extension requires :ref:`Node.js <installation-requirements-nodejs>`.

    Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

    .. tab-set::

       .. tab-item:: YAML

          .. code-block:: yaml

              extensions:
                raspberry-mint: {}

       .. tab-item:: JSON

          .. code-block:: json

              {
                "extensions": {
                  "raspberry-mint": {}
                }
              }

    Configuration
    -------------
    This extension is configurable:

    .. tab-set::

       .. tab-item:: YAML

          .. code-block:: yaml

              extensions:
                raspberry-mint:
                  configuration:
                    primary_color: '#b3446c'
                    secondary_color: '#3eb489'
                    tertiary_color: '#ffbd22'
                    regional_content:
                      front-page-content:
                        - id: raspberry-mint-featured-entities
                          configuration:
                            - entity_type: person
                              entity: P123
                            - entity_type: place
                              entity: Amsterdam

       .. tab-item:: JSON

          .. code-block:: json

              {
                "extensions": {
                  "raspberry-mint": {
                    "configuration" : {
                      "primary_color": "#b3446c",
                      "secondary_color": "#3eb489",
                      "tertiary_color": "#ffbd22",
                      "regional_content": {
                        "front-page-content":[
                          {
                            "id": "raspberry-mint-featured-entities":
                            "configuration": [
                              {
                                "entity_type": "person",
                                "entity": "P123"
                              },
                              {
                                "entity_type": "place",
                                "entity": "Amsterdam"
                              }
                            ]
                          }
                        ]
                      ]
                    }
                  }
                }
              }

    ``primary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the primary color. Defaults to ``#b3446c``.

    ``secondary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the secondary color. Defaults to ``#3eb489``.

    ``tertiary_color``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The case-insensitive hexadecimal code for the tertiary color. Defaults to ``#ffbd22``.

    ``regional_content``
    ^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    Assign content to regions within this theme. Keys are theme regions, and values are sequences of
    :py:class:`content provider <betty.content_provider.ContentProviderDefinition>` instance configurations.

    ``regional_content[][].id``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`required`

    The plugin ID of the content provider to assign to this region.

    ``regional_content[][].configuration``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`optional`

    The configuration for the content provider, if needed.

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

    - :py:func:`associated_file_references <betty.project.extension._theme.associated_file_references>`
    - :py:func:`person_descendant_families <betty.project.extension._theme.person_descendant_families>`
    - :py:func:`person_timeline_events <betty.project.extension._theme.person_timeline_events>`

    """

    @private
    def __init__(
        self,
        *,
        project: Project,
        configuration: RaspberryMintConfiguration | None = None,
    ):
        super().__init__(
            configuration=RaspberryMintConfiguration()
            if configuration is None
            else configuration,
            project=project,
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[RaspberryMintConfiguration]:
        return RaspberryMintConfiguration

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: RaspberryMintConfiguration
    ) -> AnyFactoryTarget[Self]:
        return CallbackProjectDependentFactory(
            lambda project: cls(configuration=configuration, project=project)
        )

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        from betty.project.extension.raspberry_mint.jobs import (
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
            self._project.configuration.root_path,
            self._configuration.primary_color.hex,
            self._configuration.secondary_color.hex,
            self._configuration.tertiary_color.hex,
        )

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self._project)

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
                for entity_type in await self._project.plugins(EntityDefinition)
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
