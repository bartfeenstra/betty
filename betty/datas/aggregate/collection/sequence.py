"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, final, override

from betty.assertions.sequence import assert_sequence
from betty.datas.aggregate.collection import CollectionDefinition
from betty.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from betty.data import Data, DataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class SequenceDefinition[MutableSequenceT: MutableSequence[Any], ValueT](
    CollectionDefinition[MutableSequenceT, Iterable[ValueT], Index]
):
    """
    A sequence data definition.
    """

    def __init__(
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
            factory=factory,
            porter=CallbackPorter(self._load, self._dump),
        )

    def _load(self, portable: PortableData, /) -> MutableSequenceT:
        loaded = self.new()
        loaded.extend(assert_sequence(self.item.porter.load)(portable))
        return loaded

    def _dump(self, data: MutableSequenceT) -> PortableData:
        return [self.item.porter.dump(item) for item in data]

    @final
    @override
    def clear(self, data: MutableSequenceT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: MutableSequenceT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.extend(values)
