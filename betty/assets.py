"""
The Assets API.
"""

from __future__ import annotations

from asyncio import to_thread
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING

from betty.concurrent import AsynchronizedLock
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping, Sequence


@threadsafe
class AssetRepository:
    """
    Manages a set of assets.

    This repository unifies several directory paths on disk, overlaying them on
    each other. Paths added later act as fallbacks, e.g. earlier paths have priority.
    """

    def __init__(self, *assets_directory_paths: Path):
        """
        :param assets_directory_paths: Earlier paths have priority over later paths.
        """
        self._assets_directory_paths = assets_directory_paths
        self.__assets: Mapping[Path, Path] | None = None
        self._lock = AsynchronizedLock.threading()

    async def _assets(self) -> Mapping[Path, Path]:
        if self.__assets is None:
            async with self._lock:
                self.__assets = await to_thread(self._init_assets)
        return self.__assets

    def _init_assets(self) -> Mapping[Path, Path]:
        return {
            (Path(directory_path) / file_name).relative_to(assets_directory_path): Path(
                directory_path
            )
            / file_name
            for assets_directory_path in reversed(self._assets_directory_paths)
            for directory_path, _, file_names in walk(assets_directory_path)
            for file_name in file_names
        }

    @property
    def assets_directory_paths(self) -> Sequence[Path]:
        """
        The paths to the individual virtual layers.
        """
        return self._assets_directory_paths

    async def walk(
        self, asset_directory_path: Path | None = None
    ) -> AsyncIterator[Path]:
        """
        Get virtual paths to available assets.

        :param asset_directory_path: If given, only asses under the directory are returned.
        """
        asset_directory_path_str = str(asset_directory_path)
        for asset_path in await self._assets():
            if asset_directory_path is None or str(asset_path).startswith(
                asset_directory_path_str
            ):
                yield asset_path

    async def get(self, path: Path) -> Path:
        """
        Get the path to a single asset file.

        :param path: The virtual asset path.
        :return: The path to the actual file on disk.
        """
        return (await self._assets())[path]
