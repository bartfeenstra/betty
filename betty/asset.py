"""
The Assets API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import to_thread
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.concurrent import ThreadSafeLock
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable, Mapping, Sequence

    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


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

    def __init__(self, *directories: Path):
        """
        :param directories: Earlier paths have priority over later paths.
        """
        self._directories = directories
        self.__assets: Mapping[Path, Path] | None = None
        self._lock = ThreadSafeLock()

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
            for assets_directory_path in reversed(self._directories)
            for directory_path, _, file_names in walk(assets_directory_path)
            for file_name in file_names
        }

    @override
    @property
    def directories(self) -> Sequence[Path]:
        return self._directories

    @override
    async def walk(self, directory: Path | None = None, /) -> AsyncIterable[Path]:
        asset_directory_path_str = str(directory)
        for asset_path in await self._assets():
            if directory is None or str(asset_path).startswith(
                asset_directory_path_str
            ):
                yield asset_path

    @override
    async def get(self, path: Path, /) -> Path:
        try:
            return (await self._assets())[path]
        except KeyError:
            raise UnknownAsset(path, self.directories) from None


@final
@PluginTypeDefinition(
    "asset",
    label=_("Asset"),
    label_plural=_("Assets"),
    label_countable=ngettext("{count} asset", "{count} assets"),
)
class AssetDefinition(OrderedPluginDefinition):
    """
    .. plugin_type:: asset.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[AssetDefinition] = (),
        assets: Path,
        auto: bool = False,
        before: Order[AssetDefinition] = (),
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            after=after,
            auto=auto,
            before=before,
            requires=requires,
        )
        self._assets = assets

    @property
    def assets(self) -> Path:
        """
        The path on disk where the asset's assets are located.
        """
        return self._assets


@final
class AssetRepositoryService[ServiceProviderT: PluginServiceProvider](
    CollectionPluginDefinitionServiceManager[
        ServiceProviderT, AssetDefinition, AssetRepository
    ]
):
    """
    A service of plugin definitions keyed by their IDs.
    """

    def __init__(self):
        super().__init__(AssetDefinition)

    @override
    def new_service(self, instance: ServiceProviderT, /) -> AssetRepository:
        return StaticAssetRepository(
            *(
                self.new_service_item(instance, asset).assets
                for asset in self.get_plugins(instance)
            )
        )
