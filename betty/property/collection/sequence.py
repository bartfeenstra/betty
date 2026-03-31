"""
Sequence properties.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, override

from betty.functools import passthrough
from betty.property import Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.data.aggregate.collection.sequence import SequenceDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class SequenceProperty[MutableSequenceT: MutableSequence[Any], ValueSetT](
    Property[MutableSequenceT, ValueSetT]
):
    """
    A property that contains a :py:class:`collections.abc.MutableSequence`.
    """

    _data: SequenceDefinition[MutableSequenceT]

    def __init__(
        self,
        data: Intersection[DataDefinition[MutableSequenceT], SequenceDefinition]
        | Data[Intersection[DataDefinition[MutableSequenceT], SequenceDefinition]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableSequenceT], bool] | None = None,
        resolver: Callable[
            [ValueSetT | Iterable[ValueSetT]], Iterable[ValueSetT]
        ] = passthrough,
        default: Callable[[], ValueSetT | Iterable[ValueSetT]] = list,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._values_resolver = resolver
        self._default_values = default

    def _new_default(self) -> MutableSequenceT:
        new = self._data.new()
        new.extend(self._values_resolver(self._default_values()))
        return new

    @override
    def set(
        self, instance: Any, value: ValueSetT | MutableSequenceT
    ) -> MutableSequenceT:
        data = self.get(instance)
        data.clear()
        data.extend(self._values_resolver(value))
        return data
