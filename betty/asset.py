"""
The Assets API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import to_thread
from contextlib import suppress
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.concurrent import AsynchronizedLock
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable, Mapping, Sequence


class AssetError(Exception):
    """
    Raised for asset API errors.
    """


class UnknownAsset(AssetError):
    """
    Raised when a requested asset cannot be found.
    """

    def __init__(self, path: Path, assets_directory_paths: Iterable[Path], /):
        super().__init__(
            f"Asset {path} cannot be found in any of: {', '.join(map(str, assets_directory_paths))}"
        )


@threadsafe
class AssetRepository(ABC):
    """
    Manages a set of assets.

    This repository unifies several directory paths on disk, overlaying them on
    each other. Paths added later act as fallbacks, e.g. earlier paths have priority.
    """

    @property
    @abstractmethod
    def assets_directory_paths(self) -> Sequence[Path]:
        """
        The paths to the individual virtual layers.
        """

    @abstractmethod
    def walk(self, asset_directory_path: Path | None = None) -> AsyncIterable[Path]:
        """
        Get virtual paths to available assets.

        :param asset_directory_path: If given, only asses under the directory are returned.
        """

    @abstractmethod
    async def get(self, path: Path) -> Path:
        """
        Get the path to a single asset file.

        :param path: The virtual asset path.
        :return: The path to the actual file on disk.
        """


class ProxyAssetRepository(AssetRepository):
    """
    Provides assets from upstream repositories.
    """

    def __init__(self, *upstreams: AssetRepository):
        self._upstreams = upstreams

    @override
    @property
    def assets_directory_paths(self) -> Sequence[Path]:
        return [
            path
            for upstream in self._upstreams
            for path in upstream.assets_directory_paths
        ]

    @override
    async def walk(
        self, asset_directory_path: Path | None = None
    ) -> AsyncIterable[Path]:
        seen = set()
        for upstream in self._upstreams:
            async for path in upstream.walk(asset_directory_path):
                if path not in seen:
                    seen.add(path)
                    yield path

    @override
    async def get(self, path: Path) -> Path:
        for upstream in self._upstreams:
            with suppress(Exception):
                return await upstream.get(path)
        raise UnknownAsset(path, self.assets_directory_paths)


class StaticAssetRepository(AssetRepository):
    """
    Manages static assets.
    """

    def __init__(self, *assets_directory_paths: Path):
        """
        :param assets_directory_paths: Earlier paths have priority over later paths.
        """
        self._assets_directory_paths = assets_directory_paths
        self.__assets: Mapping[Path, Path] | None = None
        self._lock = AsynchronizedLock.new_threadsafe()

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

    @override
    @property
    def assets_directory_paths(self) -> Sequence[Path]:
        return self._assets_directory_paths

    @override
    async def walk(
        self, asset_directory_path: Path | None = None
    ) -> AsyncIterable[Path]:
        asset_directory_path_str = str(asset_directory_path)
        for asset_path in await self._assets():
            if asset_directory_path is None or str(asset_path).startswith(
                asset_directory_path_str
            ):
                yield asset_path

    @override
    async def get(self, path: Path) -> Path:
        try:
            return (await self._assets())[path]
        except KeyError:
            raise UnknownAsset(path, self.assets_directory_paths) from None
