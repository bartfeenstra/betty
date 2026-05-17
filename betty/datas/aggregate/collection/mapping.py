"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final, override

from betty.data import DataDefinition, ResolvableDataDefinition, resolve_data_definition
from betty.datas.aggregate.collection import CollectionDefinition
from betty.indicator.selector import Key
from betty.portable import CallbackPorter, PortableData, Porter

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class MappingDefinition[MutableMappingT: MutableMapping[Any, Any], KeyT, ValueT](
    CollectionDefinition[MutableMappingT, Mapping[KeyT, ValueT], Key]
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
        key: ResolvableDataDefinition[DataDefinition[KeyT, str]],
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
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
        self._value = resolve_data_definition(value)

    def _load(self, portable: PortableData, /) -> MutableMappingT:
        from betty.assertion import assert_mapping

        loaded = self.new()
        loaded.update(
            assert_mapping(self._value.porter.load, self._item.porter.load)(portable)
        )
        return loaded

    def _dump(self, data: MutableMappingT) -> PortableData:
        return {
            self._item.porter.dump(key): self._value.porter.dump(item)
            for key, item in data.items()
        }

    @final
    @override
    def replace(self, data: MutableMappingT, values: Mapping[KeyT, ValueT], /) -> None:
        data.clear()
        data.update(values)
