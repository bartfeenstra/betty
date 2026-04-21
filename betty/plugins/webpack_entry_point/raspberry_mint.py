"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import Content, ContentManufacturer
from betty.dirs import ROOT_DIRECTORY
from betty.factory import Manufacturable
from betty.plugins.extension.raspberry_mint.region import ResolvableRegion
from betty.project import Project
from betty.webpack import WebpackEntryPoint, WebpackEntryPointDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

type RegionalContent = Mapping[str, Sequence[Content]]
type RegionalContentManufacturers = Mapping[
    ResolvableRegion, Iterable[ContentManufacturer]
]


@final
@WebpackEntryPointDefinition(
    "raspberry-mint",
    entry_point=ROOT_DIRECTORY / "webpack-entry-points" / "raspberry-mint",
)
class RaspberryMint(Manufacturable, WebpackEntryPoint):
    """
    .. plugin:: webpack-entry-point:raspberry-mint.
    """

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    @override
    @classmethod
    @Project.require
    async def new(cls, project: Project, /) -> Self:
        return cls(project)

    @override
    async def cache_keys(self) -> Sequence[str]:
        from betty.plugins.extension.raspberry_mint import (
            RaspberryMint as RaspberryMintExtension,
        )

        raspberry_mint = await self._project.extensions[RaspberryMintExtension]
        return (
            self._project.root_path,
            raspberry_mint.primary_color,
            raspberry_mint.secondary_color,
            raspberry_mint.tertiary_color,
        )
