"""
Mapping properties.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, override

from betty.property import Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.data.aggregate.collection.mapping import MappingDefinition
    from betty.locale.localizable import ResolvableLocalizable


class MappingProperty[MutableMappingT: MutableMapping[Any, Any], ValueSetT](
    Property[MutableMappingT, ValueSetT]
):
    """
    A property that contains a :py:class:`collections.abc.MutableMapping`.
    """

    _data: MappingDefinition[MutableMappingT]

    def __init__(
        self,
        data: Intersection[DataDefinition[MutableMappingT], MappingDefinition]
        | Data[Intersection[DataDefinition[MutableMappingT], MappingDefinition]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableMappingT], bool] | None = None,
        default: Callable[[], Mapping] = dict,
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

    def _new_default(self) -> MutableMappingT:
        new = self._data.new()
        new.update(self._default_values())
        return new

    @override
    def set(self, instance: Any, value: ValueSetT | MutableMappingT) -> MutableMappingT:
        data = self.get(instance)
        data.clear()
        data.update(self._resolver(value))
        return data
