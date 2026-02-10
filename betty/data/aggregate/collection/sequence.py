"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any

from betty.data.aggregate.collection import CollectionDefinition
from betty.data.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class SequenceDefinition[MutableSequenceT: MutableSequence[Any]](
    CollectionDefinition[MutableSequenceT, Index]
):
    """
    A sequence data definition.
    """

    def __init__[ValueT](
        self,
        /,
        cls: type[MutableSequenceT],
        *,
        value: DataDefinition[ValueT] | type[Intersection[ValueT, Data]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[Sequence[ValueT]], MutableSequenceT] | None = None,
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

        factory = self.cls if not self._factory else self._factory
        return factory(assert_sequence(self._item.porter.load)(portable))  # ty:ignore[too-many-positional-arguments]

    def _dump(self, data: MutableSequenceT) -> PortableData:
        return [
            self._item.porter.dump(
                item,
            )  # ty:ignore[invalid-argument-type]
            for item in data
        ]  # ty:ignore[invalid-return-type]
