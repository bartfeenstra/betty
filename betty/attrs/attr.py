"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attr import Attr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class AttrAttr[OwnerT: HasProperties, GetT, SetT](Attr[OwnerT, GetT, SetT]):
    """
    An object attribute stored on an instance.
    """

    def __init__(
        self,
        data: DataDefinition[GetT] | type[Data[DataDefinition[GetT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[GetT], bool] | None = None,
        default: Callable[[], GetT] | None = None,
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
        self._label = label
        self._description = description
        self._default = default

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return getattr(owner, f"_{self.property.name}")

    @final
    @override
    def init_property_owner(self, owner: OwnerT, /) -> None:
        if self._default is None:
            return
        setattr(owner, f"_{self.property.name}", self._default())
