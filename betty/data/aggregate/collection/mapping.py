"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Key
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from betty.data import DataDefinition
    from betty.locale.localizable import LocalizableLike

_DataItemT = TypeVar("_DataItemT")
_MutableMappingT = TypeVar("_MutableMappingT", bound=MutableMapping[str, Any])


@final
class MappingDefinition(CollectionDefinition[_MutableMappingT, Key]):
    """
    A key-value mapping data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_MutableMappingT],
        item: DataDefinition[_DataItemT],
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        factory: Callable[[Mapping[str, _DataItemT]], _MutableMappingT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=item,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
        )
        self._factory = factory

    @override
    def elements(self, data: _MutableMappingT) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(key), self.item) for key, item_data in data.items()]

    def _load(self, portable: PortableData, /) -> _MutableMappingT:
        from betty.assertion import assert_mapping, assert_str

        factory = self.cls if not self._factory else self._factory
        return factory(assert_mapping(self._item.load, assert_str())(portable))

    def _dump(self, data: _MutableMappingT) -> PortableData:
        return {key: self._item.dump(item) for key, item in data.items()}
