"""
Sequence properties.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.attr import AttrAttr
from betty.functools import passthrough
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data
    from betty.datas.aggregate.collection.sequence import SequenceDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class SequenceAttr[
    OwnerT: HasProperties,
    MutableSequenceT: MutableSequence[Any],
    ItemGetT,
    SetT,
](AttrAttr[OwnerT, MutableSequenceT, SetT]):
    """
    An attribute that contains a :py:class:`collections.abc.MutableSequence`.
    """

    _data: SequenceDefinition[MutableSequenceT]

    def __init__(
        self,
        data: SequenceDefinition[
            Intersection[MutableSequenceT, MutableSequence[ItemGetT]]
        ]
        | type[
            Data[
                SequenceDefinition[
                    Intersection[MutableSequenceT, MutableSequence[ItemGetT]]
                ]
            ]
        ],
        *,
        default: Callable[[], SetT] | None = None,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableSequenceT], bool] | None = None,
        omit_load: bool | None = None,
        resolver: Callable[[SetT], Iterable[ItemGetT]] = passthrough,
    ):
        super().__init__(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            default=self._new_default,
        )
        self._default_values = default
        self._sequence_resolver = resolver

    @final
    def _new_default(self) -> MutableSequenceT:
        new = self._data.new()
        if self._default_values is not None:
            new.extend(self._sequence_resolver(self._default_values()))
        return new

    @final
    @override
    def set(self, owner: OwnerT, value: SetT, /) -> MutableSequenceT:
        data = self.get(owner)
        data.clear()
        data.extend(self._sequence_resolver(value))
        return data
