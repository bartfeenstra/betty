"""
Keyed collection properties.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, override

from betty.collection.keyed import MutableKeyedCollection
from betty.functools import passthrough
from betty.property import Property

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import Data, DataDefinition
    from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
    from betty.locale.localizable import ResolvableLocalizable


class KeyedCollectionProperty[
    MutableKeyedCollectionT: MutableKeyedCollection,
    ValueSetT,
](Property[MutableKeyedCollectionT, Iterable[ValueSetT]]):
    """
    A property that contains an :py:class:`betty.collection.keyed.KeyedCollection`.
    """

    _data: KeyedCollectionDefinition[MutableKeyedCollectionT]

    def __init__(
        self,
        data: Intersection[
            DataDefinition[MutableKeyedCollectionT], KeyedCollectionDefinition
        ]
        | Data[
            Intersection[
                DataDefinition[MutableKeyedCollectionT], KeyedCollectionDefinition
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

    def _new_default(self) -> MutableKeyedCollectionT:
        new = self._data.new()
        new.add(*self._values_resolver(self._default_values()))
        return new

    @override
    def set(
        self, instance: Any, value: Iterable[ValueSetT] | MutableKeyedCollectionT
    ) -> MutableKeyedCollectionT:
        data = self.get(instance)
        data.clear()
        data.add(*self._values_resolver(value))
        return data
