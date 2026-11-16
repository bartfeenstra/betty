"""
Catalogs backed by dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import disjoint_base

from betty.collections import ValueResolvable
from betty.collections.catalog.mapping import MappingCatalog, MutableMappingCatalog
from betty.collections.mapping.dict import empty_frozen_dict
from betty.freezers.frozen import Frozen
from betty.pipeline import pipe

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from betty.collections import KeyResolver, ValueResolver


@disjoint_base
class FrozenDictCatalog[KeyT, ResolvableKeyT, ValueT](
    MappingCatalog[KeyT, ResolvableKeyT, ValueT, dict[KeyT, ValueT]], Frozen
):
    """
    An immutable catalog backed by a dictionary.
    """

    __slots__ = ()

    def __init__(
        self,
        values: Mapping[KeyT, ValueT] = empty_frozen_dict,
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
    ):
        super().__init__(dict(values), key=key)

    def __hash__(self) -> int:
        return hash(tuple(self.__wrapped__.items()))


@disjoint_base
class DictCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableMappingCatalog[
        KeyT, ResolvableKeyT, ValueT, ResolvableValueT, dict[KeyT, ValueT]
    ],
    ValueResolvable[ValueT, ResolvableValueT],
):
    """
    A mutable catalog backed by a dictionary.
    """

    def __init__(
        self,
        keyer: Callable[[ValueT], KeyT | ResolvableKeyT],
        values: Iterable[ValueT | ResolvableValueT] = (),
        /,
        *,
        key: KeyResolver[KeyT, ResolvableKeyT] = pipe,
        value: ValueResolver[ValueT, ResolvableValueT] = pipe,
    ):
        super().__init__(
            {
                key(keyer(resolved_value)): resolved_value
                for value_ in values
                if (resolved_value := value(value_))
            },
            keyer,
            key=key,
            value=value,
        )
