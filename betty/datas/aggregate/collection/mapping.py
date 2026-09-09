"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.mapping import assert_mapping
from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.collection import (
    CollectionDefinition,
    DataFactory,
    MutableCollectionDefinition,
)
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData, Porter
    from betty.typing import Intersection


type NewMapping[KeyT, ValueT] = Mapping[KeyT, ValueT] | Iterable[tuple[KeyT, ValueT]]


class MappingDefinition[MappingT: Mapping[Any, Any], KeyT, ValueT](
    CollectionDefinition[MappingT, KeyT, NewMapping[KeyT, ValueT]]
):
    """
    A key-value mapping data definition.
    """

    def __init__(
        self,
        *,
        cls: type[Intersection[MappingT, Mapping[KeyT, ValueT]]] | None = None,
        key: ResolvableDataDefinition[DataDefinition[KeyT]],
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: DataFactory[MappingT, NewMapping[KeyT, ValueT]] | None = None,
        porter: Porter[MappingT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=key,
            label=label,
            description=description,
            factory=factory,
            porter=CallbackPorter(self._load, self._dump) if porter is None else porter,
        )
        self._value = resolve_data_definition(value)

    def _load(self, portable: PortableData, /) -> MappingT:
        return self.new(
            assert_mapping(self._value.porter.load, self.item.porter.load)(portable)
        )

    def _dump(self, data: MappingT) -> PortableData:
        return {
            self._dump_key(key): self._value.porter.dump(item)
            for key, item in data.items()
        }

    def _dump_key(self, key: KeyT, /) -> str:
        dumped = self.item.porter.dump(key)
        assert isinstance(dumped, str)
        return dumped


class MutableMappingDefinition[MappingT: MutableMapping[Any, Any], KeyT, ValueT](
    MappingDefinition[MappingT, KeyT, ValueT],
    MutableCollectionDefinition[MappingT, KeyT, NewMapping[KeyT, ValueT]],
):
    """
    A mutable key-value mapping data definition.
    """

    @final
    @override
    def clear(self, data: MappingT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: MappingT, values: NewMapping[KeyT, ValueT], /) -> None:
        data.clear()
        data.update(values)
