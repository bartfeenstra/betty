"""
Service plugin management.

Service levels can expose services of plugin instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, overload, override

from betty.collection.keyed import KeyedCollection
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from ty_extensions import Intersection


@final
class PluginCollection[PluginDefinitionT: PluginDefinition, PluginT: Plugin](
    KeyedCollection[MachineName, ResolvableId[PluginDefinitionT], PluginT]
):
    """
    A collection of plugin instances.
    """

    def __init__(self, plugins: Iterable[Iterable[PluginT]], /):
        self._batches = tuple(map(tuple, plugins))
        self._all = {
            plugin.plugin().id: plugin for batch in self._batches for plugin in batch
        }

    @override
    def __len__(self) -> int:
        return len(self._all)

    @override
    def __iter__(self) -> Iterator[PluginT]:
        yield from self._all.values()

    @override
    def __contains__(self, key: Any) -> bool:
        if isinstance(key, type) and issubclass(key, Plugin):
            key = key.plugin().id
        elif isinstance(key, PluginDefinition):
            key = key.id
        return key in self._all

    @overload
    def __getitem__[T](
        self, key: type[Intersection[PluginT, T]]
    ) -> Intersection[PluginT, T]:
        pass

    @overload
    def __getitem__(self, key: ResolvableId[PluginDefinitionT]) -> PluginT:
        pass

    @override
    def __getitem__(self, key):
        return self._all[resolve_id(key)]

    @override
    def keys(self) -> Iterable[MachineName]:
        return self._all.keys()
