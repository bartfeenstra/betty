"""
Page regions.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, final

from betty.entity import EntityDefinition

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.project import Project


@final
class Region(Enum):
    """
    The available regions.
    """

    ENTITY_PAGE_CONTENT = "entity-page-content"
    FRONT_PAGE_CONTENT = "front-page-content"
    FRONT_PAGE_SUMMARY = "front-page-summary"

    @classmethod
    async def all(cls, project: Project, /) -> Collection[str]:
        """
        The available regions.
        """
        return {
            *(region.value for region in cls),
            *[
                f"entity-page-content--{entity_type.id}"
                async for entity_type in project.plugins[EntityDefinition]
                if entity_type.public_facing
            ],
        }

    @classmethod
    def resolve(cls, region: ResolvableRegion) -> str:
        """
        Resolve a region to its string name.
        """
        if isinstance(region, str):
            return region
        return region.value


type ResolvableRegion = Region | str
