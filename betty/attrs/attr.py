"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, final, override

from betty.attr import Attr, AttrNotInitialized
from betty.datas.aggregate.record.object import AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.property import HasProperties
from betty.typing import Void

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
        resolver: Callable[[SetT], GetT] = passthrough,
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
            resolver=resolver,
        )
        self._data = data
        self._label = label
        self._description = description
        self._default = default

    @final
    @override
    def get(self, owner: OwnerT, /) -> GetT:
        value = cast(
            GetT | Void,
            getattr(owner, f"_{self.property.name}", Void),
        )
        if value is Void:
            if self._default is None:
                instance_name = fully_qualified_name(type(owner))
                raise AttrNotInitialized(
                    f"{instance_name}.{f'_{self.property.name}'[1:]} was never initialized. Either provide a default when initializing the attribute, or make {instance_name}.__init__() set a value."
                )
            value = self._default()
            setattr(owner, f"_{self.property.name}", value)
        return value  # ty:ignore[invalid-return-type]

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        setattr(owner, f"_{self.property.name}", self._resolver(value))
