"""
Sequence data types.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, Self, final, override

from betty.assertions.sequence import assert_sequence
from betty.capability import ResolvableStagedCapability, Stage
from betty.datas.aggregate.collection import CollectionDefinition
from betty.definition.cls import ClsDefinitionCapabilityStage
from betty.portable import Porter
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.typing import Intersection


class SequenceDefinition[
    SequenceT: MutableSequence[Any],
    ValueT,
    StageT: Stage = ClsDefinitionCapabilityStage,
    PorterT: Porter = Porter,
](CollectionDefinition[SequenceT, Iterable[ValueT], StageT, PorterT]):
    """
    A sequence data definition.
    """

    def __init__(
        self,
        *,
        cls: type[Intersection[SequenceT, MutableSequence[ValueT]]] | None = None,
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        factory: Callable[[], SequenceT] | None = None,
        porter: ResolvableStagedCapability[
            Self,
            Intersection[PorterT, Porter[SequenceT]],
            StageT | ClsDefinitionCapabilityStage,
        ]
        | None = None,
    ):
        super().__init__(
            cls=cls,
            item=value,
            label=label,
            description=description,
            factory=factory,
            porter=CallbackPorter(self._load, self._dump) if porter is None else porter,
        )

    def _load(self, portable: PortableData, /) -> SequenceT:
        loaded = self.new()
        loaded.extend(assert_sequence(self.item.porter.load)(portable))
        return loaded

    def _dump(self, data: SequenceT) -> PortableData:
        return [self.item.porter.dump(item) for item in data]

    @final
    @override
    def clear(self, data: SequenceT, /) -> None:
        data.clear()

    @final
    @override
    def replace(self, data: SequenceT, values: Iterable[ValueT], /) -> None:
        data.clear()
        data.extend(values)
