"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Key
from betty.portable import CallbackPorter, PortableData, Porter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
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
        cls: type[Intersection[MutableMappingT, MutableMapping[KeyT, ValueT]]],
        *,
        key: DataDefinition[KeyT, str],
        value: DataDefinition[ValueT] | type[Intersection[ValueT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[Mapping[KeyT, ValueT]], MutableMappingT] | None = None,
        porter: Porter[MutableMappingT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=value,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump) if porter is None else porter,
        )
        self._key = key
        self._factory = factory

    def _load(self, portable: PortableData, /) -> MutableMappingT:
        from betty.assertion import assert_mapping

        factory = self.cls if not self._factory else self._factory
        return factory(
            assert_mapping(self._item.porter.load, self._key.porter.load)(portable)  # ty:ignore[too-many-positional-arguments]
        )

    def _dump(self, data: MutableMappingT) -> PortableData:
        return {
            self._key.porter.dump(key): self._item.porter.dump(item)
            for key, item in data.items()
        }
