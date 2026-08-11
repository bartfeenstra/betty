"""
The Assets API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import to_thread
from typing import TYPE_CHECKING, Final, final, override

from betty.concurrent import ThreadSafeLock
from betty.localizables.gettext import _, ngettext
from betty.pathlib import resolve_path
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable, Mapping, Sequence
    from pathlib import Path

    from betty.machine_name import ResolvableMachineName
    from betty.pathlib import StrPath
    from betty.requirement import Requires


class AssetError(Exception):
    """
    Raised for asset API errors.
    """


class UnknownAsset(AssetError):
    """
    Raised when a requested asset cannot be found.
    """

    def __init__(self, path: Path, assets_directories: Iterable[Path], /):
        super().__init__(
            f"Asset {path} cannot be found in any of: {', '.join(map(str, assets_directories))}"
        )


class AssetRepository(metaclass=ABCMeta):
    """
    Manages a set of assets.

    This repository unifies several directory paths on disk, overlaying them on
    each other. Paths added later act as fallbacks, e.g. earlier paths have priority.
    """

    @property
    @abstractmethod
    def directories(self) -> Sequence[Path]:
        """
        The paths to the individual virtual layers.
        """

    @abstractmethod
    def walk(self, directory: Path | None = None, /) -> AsyncIterable[Path]:
        """
        Get virtual paths to available assets.

        :param directory: If given, only asses under the directory are returned.
        """

    @abstractmethod
    async def get(self, path: Path, /) -> Path:
        """
        Get the path to a single asset file.

        :param path: The virtual asset path.
        :return: The path to the actual file on disk.
        """


class StaticAssetRepository(AssetRepository):
    """
    Manages static assets.
    """

    def __init__(self, *directories: StrPath):
        """
        :param directories: Earlier paths have priority over later paths.
        """
        self._directories = tuple(map(resolve_path, directories))
        self.__assets: Mapping[Path, Path] | None = None
        self._lock = ThreadSafeLock()

    async def _assets(self) -> Mapping[Path, Path]:
        if self.__assets is None:
            async with self._lock:
                self.__assets = await to_thread(self._init_assets)
        return self.__assets

    def _init_assets(self) -> Mapping[Path, Path]:
        return {
            (directory / file_name).relative_to(asset_directory): directory / file_name
            for asset_directory in reversed(self._directories)
            for directory, _, file_names in asset_directory.walk()
            for file_name in file_names
        }

    @override
    @property
    def directories(self) -> Sequence[Path]:
        return self._directories

    @override
    async def walk(self, directory: Path | None = None, /) -> AsyncIterable[Path]:
        asset_directory_str = str(directory)
        for asset in await self._assets():
            if directory is None or str(asset).startswith(asset_directory_str):
                yield asset

    @override
    async def get(self, path: Path, /) -> Path:
        try:
            return (await self._assets())[path]
        except KeyError:
            raise UnknownAsset(path, self.directories) from None


@final
@PluginTypeDefinition(
    "asset-directory",
    label=_("Asset directory"),
    label_plural=_("Asset directories"),
    label_countable=ngettext("{count} asset directory", "{count} asset directories"),
)
class AssetDirectoryDefinition(OrderedPluginDefinition):
    """
    .. plugin_type:: asset-directory.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[AssetDirectoryDefinition] = (),
        assets: Path,
        auto: bool = False,
        before: Order[AssetDirectoryDefinition] = (),
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            after=after,
            auto=auto,
            before=before,
            requires=requires,
        )
        self.assets: Final[Path] = assets
        """
        The path on disk where the asset's assets are located.
        """
