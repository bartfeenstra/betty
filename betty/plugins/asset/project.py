"""
Project assets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.asset import AssetDefinition
from betty.plugins.asset.app import APP
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.discovery import ResolvableDiscovery


@Project.require
def _discover(project: Project, /) -> Iterable[ResolvableDiscovery[AssetDefinition]]:
    yield AssetDefinition(
        "project",
        assets=project.assets_directory,
        after=lambda other: other != APP.id,
        before={APP},
        auto=True,
    )
