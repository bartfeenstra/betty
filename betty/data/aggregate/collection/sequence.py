"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence
from typing import TYPE_CHECKING, Any

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class SequenceDefinition[MutableSequenceT: MutableSequence[Any]](
    CollectionDefinition[MutableSequenceT, Index]
):
    """
    A sequence data definition.
    """

    def __init__[ValueT](
        self,
        /,
        cls: type[Intersection[MutableSequenceT, MutableSequence[ValueT]]]
        | None = None,
        *,
        value: DataDefinition[ValueT] | type[Intersection[ValueT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[], MutableSequenceT] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=value,
            label=label,
            description=description,
            porter=CallbackPorter(self._load, self._dump),
        )
        self._factory = factory

    def _load(self, portable: PortableData, /) -> MutableSequenceT:
        from betty.assertion import assert_sequence

        loaded = self.new()
        loaded.extend(assert_sequence(self._item.porter.load)(portable))
        return loaded

    def _dump(self, data: MutableSequenceT) -> PortableData:
        return [self._item.porter.dump(item) for item in data]
