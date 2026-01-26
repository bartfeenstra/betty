"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from betty.data import DataDefinition
    from betty.locale.localizable import LocalizableLike

_DataItemT = TypeVar("_DataItemT")
_MutableSequenceT = TypeVar("_MutableSequenceT", bound=MutableSequence[Any])


@final
class SequenceDefinition(CollectionDefinition[_MutableSequenceT, Index]):
    """
    A sequence data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_MutableSequenceT],
        item: DataDefinition[_DataItemT],
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        factory: Callable[[Iterable[_DataItemT]], _MutableSequenceT] | None = None,
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
    def elements(
        self, data: _MutableSequenceT
    ) -> Sequence[tuple[Index, DataDefinition]]:
        return [(Index(index), self.item) for index, item_data in enumerate(data)]

    def _load(self, portable: PortableData, /) -> _MutableSequenceT:
        from betty.assertion import assert_sequence

        factory = self.cls if not self._factory else self._factory
        return factory(assert_sequence(self._item.porter.load)(portable))

    def _dump(self, data: _MutableSequenceT) -> PortableData:
        return [self._item.porter.dump(item) for item in data]
