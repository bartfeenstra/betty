"""
Mapping properties.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final, override

from betty.functools import passthrough
from betty.property import Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.datas.aggregate.collection.mapping import MappingDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class MappingProperty[
    MutableMappingT: MutableMapping[Any, Any],
    KeyGetT,
    ItemGetT,
    ValueSetT,
](Property[MutableMappingT, ValueSetT]):
    """
    A property that contains a :py:class:`collections.abc.MutableMapping`.
    """

    _data: MappingDefinition[MutableMappingT]

    def __init__(
        self,
        data: Intersection[DataDefinition[MutableMappingT], MappingDefinition]
        | Data[Intersection[DataDefinition[MutableMappingT], MappingDefinition]],
        *,
        default: Callable[[], ValueSetT] | None = None,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableMappingT], bool] | None = None,
        omit_load: bool | None = None,
        resolver: Callable[[ValueSetT], Mapping[KeyGetT, ItemGetT]] = passthrough,
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
        self._mapping_resolver = resolver

    @final
    def _new_default(self) -> MutableMappingT:
        new = self._data.new()
        if self._default_values is not None:
            new.update(self._mapping_resolver(self._default_values()))
        return new

    @final
    @override
    def set(self, instance: Any, value: ValueSetT, /) -> MutableMappingT:
        data = self.get(instance)
        data.clear()
        data.update(self._mapping_resolver(value))
        return data
