"""
Keyed collection properties.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, final, override

from betty.collection.keyed import MutableKeyedCollection
from betty.functools import passthrough
from betty.property import Property

if TYPE_CHECKING:
    from betty.data import Data
    from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
    from betty.datas.aggregate.record.object import AttrDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class KeyedCollectionProperty[
    KeyedCollectionDefinitionT: KeyedCollectionDefinition,
    MutableKeyedCollectionT: MutableKeyedCollection,
    ValueSetT,
](Property[KeyedCollectionDefinitionT, MutableKeyedCollectionT, Iterable[ValueSetT]]):
    """
    A property that contains an :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    _attr: AttrDefinition[
        Intersection[
            KeyedCollectionDefinition[MutableKeyedCollectionT],
            KeyedCollectionDefinitionT,
        ],
        MutableKeyedCollectionT,
    ]

    def __init__(
        self,
        data: Intersection[
            KeyedCollectionDefinition[MutableKeyedCollectionT],
            KeyedCollectionDefinitionT,
        ]
        | type[
            Data[
                Intersection[
                    KeyedCollectionDefinition[MutableKeyedCollectionT],
                    KeyedCollectionDefinitionT,
                ]
            ]
        ],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MutableKeyedCollectionT], bool] | None = None,
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

    @final
    def _new_default(self) -> MutableKeyedCollectionT:
        new = self._attr.data.new()
        new.add(*self._values_resolver(self._default_values()))
        return new

    @final
    @override
    def set(
        self, instance: Any, value: Iterable[ValueSetT], /
    ) -> MutableKeyedCollectionT:
        data = self.get(instance)
        data.clear()
        data.add(*self._values_resolver(value))
        return data
