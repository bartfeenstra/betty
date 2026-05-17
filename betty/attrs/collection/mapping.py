"""
Mapping properties.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.attr import AttrAttr
from betty.property import HasProperties

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data
    from betty.datas.aggregate.collection.mapping import MappingDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class MappingAttr[
    OwnerT: HasProperties,
    MutableMappingT: MutableMapping[Any, Any],
    KeyT,
    ValueT,
](AttrAttr[OwnerT, MutableMappingT, Mapping[KeyT, ValueT]]):
    """
    An attribute that contains a :py:class:`collections.abc.MutableMapping`.
    """

    _data: MappingDefinition[MutableMappingT, KeyT, ValueT]

    def __init__(
        self,
        data: MappingDefinition[
            Intersection[MutableMappingT, MutableMapping[KeyT, ValueT]], KeyT, ValueT
        ]
        | type[
            Data[
                MappingDefinition[
                    Intersection[MutableMappingT, MutableMapping[KeyT, ValueT]],
                    KeyT,
                    ValueT,
                ]
            ]
        ],
        *,
        default: Callable[[], Mapping[KeyT, ValueT]] = dict,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable | None = None,
        omit_dump: Callable[[MutableMappingT], bool] | None = None,
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
    def _new_default(self) -> MutableMappingT:
        return self._data.new(self.__default_items())

    @final
    @override
    def set(self, owner: OwnerT, value: Mapping[KeyT, ValueT], /) -> None:
        self._data.replace(self.get(owner), value)
