"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import override

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable

_DataItemT = TypeVar("_DataItemT")
_MutableSequenceT = TypeVar("_MutableSequenceT", bound=MutableSequence[Any])


class SequenceDefinition(CollectionDefinition[_MutableSequenceT, Index]):
    """
    A sequence data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_MutableSequenceT],
        value: DataDefinition[_DataItemT] | type[Intersection[_DataItemT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[Sequence[_DataItemT]], _MutableSequenceT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=value,
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
        return factory(assert_sequence(self._item.porter.load)(portable))  # ty:ignore[too-many-positional-arguments]

    def _dump(self, data: _MutableSequenceT) -> PortableData:
        return [self._item.porter.dump(item) for item in data]
