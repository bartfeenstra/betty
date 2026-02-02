"""
Key-value mapping data types.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.assertion import assert_mapping, assert_sequence
from betty.collections import AutoMapping, PrimaryKeyMapping
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Element, Key
from betty.portable import (
    CallbackPorter,
    PortableData,
    PortableMapping,
    PortableSequence,
    Porter,
)

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.data.aggregate.record import RecordDefinition
    from betty.locale.localizable import ResolvableLocalizable

_DataKeyT = TypeVar("_DataKeyT")
_DataValueT = TypeVar("_DataItemT")
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
            Intersection[_MutableMappingT, MutableMapping[_DataKeyT, _DataValueT]]
        ],
        key: DataDefinition[_DataKeyT],
        value: DataDefinition[_DataValueT] | type[Intersection[_DataValueT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[Mapping[str, _DataValueT]], _MutableMappingT] | None = None,
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
            assert_mapping(self._item.porter.load, self._key.porter.load)(portable)
        )

    def _dump(self, data: _MutableMappingT) -> PortableData:
        return {
            self._key.porter.dump(key): self._item.porter.dump(item)
            for key, item in data.items()
        }  # ty:ignore[invalid-return-type]


@final
class AutoMappingDefinition(
    CollectionDefinition[AutoMapping[Any, Any, _DataValueT, Any], Key]
):
    """
    A definition for :py:class:`betty.collections.AutoMapping`.
    """

    _item: RecordDefinition[_DataValueT, Key]

    def __init__(
        self,
        *,
        value: RecordDefinition[_DataValueT] | type[Data[RecordDefinition]],
        key: Element[str],
        ordered: bool,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=AutoMapping,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=value,
        )
        self._key = key
        self._ordered = ordered

    @override
    def elements(
        self, data: AutoMapping[Any, Any, _DataValueT, Any]
    ) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(self._key.get(item_data)), self.item) for item_data in data]

    def _load(
        self, portable: PortableData, /
    ) -> AutoMapping[str, str, _DataValueT, Any]:
        if self._ordered:
            items = assert_sequence(self._item.porter.load)(portable)
        else:
            items = [
                self._item.porter.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        return PrimaryKeyMapping(items, key=self._key.get)

    def _dump(
        self, data: AutoMapping[str, str, _DataValueT, Any]
    ) -> PortableMapping | PortableSequence:
        if self._ordered:
            return [self._item.porter.dump(value) for value in data]
        return dict(
            self._item.porter.dump_key(item_data, self._key) for item_data in data
        )
