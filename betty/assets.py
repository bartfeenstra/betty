"""
The Assets API.
"""

from __future__ import annotations

from os import walk
from typing import Sequence, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from collections.abc import Iterator


class AssetRepository:
    """
    Manages a set of assets.

    This repository unifies several directory paths on disk, overlaying them on
    each other. Paths added later act as fallbacks, e.g. earlier paths have priority.
    """

    def __init__(self, *assets_directory_paths: Path):
        self._assets_directory_paths = assets_directory_paths
        self._assets = {}
        for assets_directory_path in reversed(assets_directory_paths):
            for directory_path, _, file_names in walk(assets_directory_path):
                for file_name in file_names:
                    file_path = Path(directory_path) / file_name
                    self._assets[file_path.relative_to(assets_directory_path)] = (
                        file_path
                    )

    @property
    def assets_directory_paths(self) -> Sequence[Path]:
        """
        The paths to the individual virtual layers.
        """
        return self._assets_directory_paths

    def walk(self, asset_directory_path: Path | None = None) -> Iterator[Path]:
        """
        Get virtual paths to available assets.

        :param asset_directory_path: If given, only asses under the directory are returned.
        """
        for asset_path in self._assets:
            if (
                asset_directory_path is None
                or asset_directory_path in asset_path.parents
            ):
                yield asset_path

    def __getitem__(self, path: Path) -> Path:
        """
        Get the path to a single asset file.

        :param path: The virtual asset path.
        :return: The path to the actual file on disk.
        """
        return self._assets[path]
