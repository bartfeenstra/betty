"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.mapping import assert_mapping
from betty.data import DataDefinition
from betty.datas.aggregate.collection import CollectionDefinition
from betty.indicator.selector import Key
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.data import Data
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData, Porter
    from betty.typing import Intersection


class MappingDefinition[MutableMappingT: MutableMapping[Any, Any], KeyT, ValueT](
    CollectionDefinition[
        MutableMappingT, Mapping[KeyT, ValueT] | Iterable[tuple[KeyT, ValueT]], Key
    ]
):
    """
    A key-value mapping data definition.
    """

    def __init__(
        self,
        /,
        cls: type[Intersection[MutableMappingT, MutableMapping[KeyT, ValueT]]]
        | None = None,
        *,
        key: DataDefinition[KeyT, str] | type[Intersection[KeyT, Data]],
        value: DataDefinition[ValueT] | type[Intersection[ValueT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[], MutableMappingT] | None = None,
        porter: Porter[MutableMappingT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=key,
            label=label,
            description=description,
            factory=factory,
            porter=CallbackPorter(self._load, self._dump) if porter is None else porter,
        )
        self._value = value if isinstance(value, DataDefinition) else value.data()

    def _load(self, portable: PortableData, /) -> MutableMappingT:
        loaded = self.new()
        loaded.update(
            assert_mapping(self._value.porter.load, self.item.porter.load)(portable)
        )
        return loaded

    def _dump(self, data: MutableMappingT) -> PortableData:
        return {
            self._item.porter.dump(key): self._value.porter.dump(item)
            for key, item in data.items()
        }

    @final
    @override
    def clear(self, data: MutableMappingT, /) -> None:
        data.clear()

    @final
    @override
    def replace(
        self,
        data: MutableMappingT,
        values: Mapping[KeyT, ValueT] | Iterable[tuple[KeyT, ValueT]],
        /,
    ) -> None:
        data.clear()
        data.update(values)
