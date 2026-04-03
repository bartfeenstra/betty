"""
Project assets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.asset import Asset, AssetDefinition
from betty.plugins.asset.universe import Universe
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.discovery import ResolvableDiscovery


@Project.require
def _discover(project: Project, /) -> Iterable[ResolvableDiscovery[AssetDefinition]]:
    @AssetDefinition(
        "project",
        assets=project.assets_directory,
        after=lambda other: other != Universe.plugin().id,
        before={Universe},
        auto=True,
    )
    class _Project(Asset):
        """
        .. plugin:: asset:project.
        """

    yield _Project
