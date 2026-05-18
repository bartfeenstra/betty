"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.locale.localizable import ResolvableLocalizable


@final
class AttrAttr[OwnerT: HasProperties, T](OwnerAttr[OwnerT, T, T]):
    """
    An object attribute that stores its data on owner instances.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[DataDefinition[T]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[T], bool] | None = None,
        default: Callable[[], T] | None = None,
    ):
        super().__init__(
            AttrDefinition(
                data,
                label=label,
                description=description,
                omit_load=omit_load,
                omit_dump=omit_dump,
            ),
        )
        self._data = data
        self._default = default

    @final
    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        if self._default is None:
            return
        self._set_owner_attr(owner, self._default())

    @final
    @override
    def get(self, owner: OwnerT, /) -> T:
        return self._get_owner_attr(owner)

    @override
    def set(self, owner: OwnerT, value: T, /) -> None:
        self._set_owner_attr(owner, value)
