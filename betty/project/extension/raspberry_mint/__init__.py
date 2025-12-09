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
    The Raspberry Mint theme.
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
    def regions(self) -> set[str]:
        """
        The available regions.
        """
        return {
            "front-page-content",
            "front-page-summary",
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

    DARK = "dark"
    """
    A dark style with a black background.
    """

    DARK_SECONDARY = "dark-secondary"
    """
    A dark style with a dark shade of the secondary color for the background.
    """
