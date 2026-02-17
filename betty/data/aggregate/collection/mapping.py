"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, final, override

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Key
from betty.portable import CallbackPorter, PortableData, Porter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable

_DataKeyT = TypeVar("_DataKeyT")
_DataItemT = TypeVar("_DataItemT")
_MutableMappingT = TypeVar("_MutableMappingT", bound=MutableMapping[Any, Any])


@final
class MappingDefinition(CollectionDefinition[_MutableMappingT, Key]):
    """
    A key-value mapping data definition.
    """

    def __init__(
        self,
        *,
        cls: type[
            Intersection[_MutableMappingT, MutableMapping[_DataKeyT, _DataItemT]]
        ],
        key: DataDefinition[_DataKeyT],
        value: DataDefinition[_DataItemT] | type[Intersection[_DataItemT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[Mapping[str, _DataItemT]], _MutableMappingT] | None = None,
        porter: Porter[_MutableMappingT] | None = None,
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

    @override
    def elements(self, data: _MutableMappingT) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(key), self.item) for key, item_data in data.items()]

    def _load(self, portable: PortableData, /) -> _MutableMappingT:
        from betty.assertion import assert_mapping

        factory = self.cls if not self._factory else self._factory
        return factory(
            assert_mapping(self._item.porter.load, self._key.porter.load)(portable)  # ty:ignore[too-many-positional-arguments]
        )

    def _dump(self, data: _MutableMappingT) -> PortableData:
        return {
            self._key.porter.dump(key): self._item.porter.dump(item)
            for key, item in data.items()
        }  # ty:ignore[invalid-return-type]
