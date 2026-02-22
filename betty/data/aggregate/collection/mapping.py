"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from typing import TYPE_CHECKING, Any, final

from betty.data import DataDefinition
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Key
from betty.portable import CallbackPorter, PortableData, Porter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data
    from betty.locale.localizable import ResolvableLocalizable


@final
class MappingDefinition[MutableMappingT: MutableMapping[Any, Any]](
    CollectionDefinition[MutableMappingT, Key]
):
    """
    A key-value mapping data definition.
    """

    def __init__[KeyT, ValueT](
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
            porter=CallbackPorter(self._load, self._dump) if porter is None else porter,
        )
        self._value = value if isinstance(value, DataDefinition) else value.data()
        self._factory = factory

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
        }  # ty:ignore[invalid-return-type]
