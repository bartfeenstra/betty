"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.sequence import assert_sequence
from betty.datas.aggregate.collection import (
    CollectionDefinition,
    DataFactory,
    MutableCollectionDefinition,
)
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.typing import Intersection


class SequenceDefinition[SequenceT: Sequence[Any], ValueT](
    CollectionDefinition[SequenceT, ValueT, Iterable[ValueT]]
):
    """
    A sequence data definition.
    """

    def __init__(
        self,
        *,
        cls: type[Intersection[SequenceT, Sequence[ValueT]]] | None = None,
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: DataFactory[SequenceT, Iterable[ValueT]] | None = None,
    ):
        super().__init__(
            cls=cls,
            item=value,
            label=label,
            description=description,
            factory=factory,
            porter=CallbackPorter(self._load, self._dump),
        )

    def _load(self, portable: PortableData, /) -> SequenceT:
        return self.new(assert_sequence(self.item.porter.load)(portable))

    def _dump(self, data: SequenceT) -> PortableData:
        return [self.item.porter.dump(item) for item in data]


class MutableSequenceDefinition[SequenceT: MutableSequence[Any], ValueT](
    SequenceDefinition[SequenceT, ValueT],
    MutableCollectionDefinition[SequenceT, ValueT, Iterable[ValueT]],
):
    """
    A mutable sequence data definition.
    """

    @final
    @override
    def clear(self, data: SequenceT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: SequenceT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.extend(values)
