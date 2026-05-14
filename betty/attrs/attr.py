"""
Attributes that store data in instance attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, final, override

from betty.attr import Attr, AttrNotInitialized
from betty.datas.aggregate.record.object import AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable


class AttrAttr[ValueGetT, ValueSetT](Attr[ValueGetT, ValueSetT]):
    """
    An object attribute stored on an instance.
    """

    def __init__(
        self,
        data: DataDefinition[ValueGetT] | type[Data[DataDefinition[ValueGetT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[ValueGetT], bool] | None = None,
        resolver: Callable[[ValueSetT], ValueGetT] = passthrough,
        default: Callable[[], ValueGetT] | None = None,
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
    def get(self, instance: Any, /) -> ValueGetT:
        value = cast(
            ValueGetT | Void,
            getattr(instance, self._attr_name, Void),
        )
        if value is Void:
            if self._default is None:
                instance_name = fully_qualified_name(type(instance))
                raise AttrNotInitialized(
                    f"{instance_name}.{self._attr_name[1:]} was never initialized. Either provide a default when initializing the attribute, or make {instance_name}.__init__() set a value."
                )
            value = self._default()
            setattr(instance, self._attr_name, value)
        return value  # ty:ignore[invalid-return-type]
