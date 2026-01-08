"""
Keyed collection data types.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.assertion import assert_mapping, assert_sequence
from betty.collections import KeyedCollection
from betty.data import DataDefinition
from betty.data.aggregate.collection import CollectionDefinition
from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Element, Key
from betty.locale.localizable import LocalizableLike
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection  # noqa: TC004


_ValueT = TypeVar("_ValueT")
_ElementT = TypeVar("_ElementT")
_ElementTT = TypeVar("_ElementTT", bound=Element[Any])


@final
class KeyedCollectionDefinition(
    CollectionDefinition[KeyedCollection[Any, _ValueT, Any, Any], Key]
):
    """
    A definition for :py:class:`betty.collections.KeyedCollection`.
    """

    _item: RecordDefinition[_ValueT, Element[Any]]

    def __init__(
        self,
        *,
        item: RecordDefinition[_ValueT, _ElementTT],
        key: "Intersection[_ElementTT, Element[_ElementT]]",
        ordered: bool,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            cls=KeyedCollection,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
            item=item,
        )
        self._key = key
        self._ordered = ordered

    @override
    def elements(
        self, data: KeyedCollection[Any, _ValueT, Any, Any]
    ) -> Sequence[tuple[Key, DataDefinition]]:
        return [(Key(self._key.get(item_data)), self.item) for item_data in data]

    def _load(
        self, portable: PortableData, /
    ) -> KeyedCollection[str, _ValueT, str, _ValueT]:
        if self._ordered:
            items = assert_sequence(self._item.load)(portable)
        else:
            items = [
                self._item.load_key(portable_item, self._key, portable_key)
                for portable_key, portable_item in assert_mapping()(portable).items()
            ]

        return KeyedCollection(items, key=self._key.get)

    def _dump(self, data: KeyedCollection[str, _ValueT, str, _ValueT]) -> PortableData:
        if self._ordered:
            return [self._item.dump(value) for value in data]
        return dict(self._item.dump_key(item_data, self._key) for item_data in data)
