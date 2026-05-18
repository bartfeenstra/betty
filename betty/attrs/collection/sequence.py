"""
Sequence properties.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.attr import AttrAttr
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import ResolvableDataDefinition
    from betty.datas.aggregate.collection.sequence import SequenceDefinition
    from betty.locale.localizable import ResolvableLocalizable


class SequenceAttr[
    OwnerT: HasProperties,
    MutableSequenceT: MutableSequence[Any],
    ItemSetT,
](AttrAttr[OwnerT, MutableSequenceT, Iterable[ItemSetT]]):
    """
    An attribute that contains a :py:class:`collections.abc.MutableSequence`.
    """

    _data: SequenceDefinition[MutableSequenceT, ItemSetT]

    def __init__(
        self,
        data: ResolvableDataDefinition[SequenceDefinition[MutableSequenceT, ItemSetT]],
        *,
        default: Callable[[], Iterable[ItemSetT]] = tuple,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableSequenceT], bool] | None = None,
        omit_load: bool | None = None,
    ):
        super().__init__(
            data,
            default=self._new_default,
            description=description,
            label=label,
            omit_dump=omit_dump,
            omit_load=omit_load,
        )
        self.__default_items = default

    @final
    def _new_default(self) -> MutableSequenceT:
        return self._data.new(self.__default_items())

    @final
    @override
    def set(self, owner: OwnerT, value: Iterable[ItemSetT], /) -> None:
        self._data.replace(self.get(owner), value)
