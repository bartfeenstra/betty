"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, final, override

from betty.datas.aggregate.collection import CollectionDefinition
from betty.indicator.selector import Index
from betty.portable import CallbackPorter, PortableData

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.locale.localizable import ResolvableLocalizable
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
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
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
        from betty.assertion import assert_sequence

        loaded = self.new()
        loaded.extend(assert_sequence(self._item.porter.load)(portable))
        return loaded

    def _dump(self, data: MutableSequenceT) -> PortableData:
        return [self._item.porter.dump(item) for item in data]

    @final
    @override
    def replace(self, data: MutableSequenceT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.extend(values)
