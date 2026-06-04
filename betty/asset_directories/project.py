"""
Project assets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.asset import AssetDirectoryDefinition
from betty.asset_directories.builtin import builtin
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.discovery import ResolvableDiscovery


@Project.require
def _discover(
    project: Project, /
) -> Iterable[ResolvableDiscovery[AssetDirectoryDefinition]]:
    yield AssetDirectoryDefinition(
        "project",
        assets=project.asset_directory,
        after=lambda other: other != builtin.id,
        before={builtin},
        auto=True,
    )
