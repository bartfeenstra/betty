"""
Attributes with default values.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from inspect import signature
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.settable import SettableAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps, ProxyProp

if TYPE_CHECKING:
    from betty.attrs.owner import CollectionOwnerAttr


@final
class DefaultAttr[OwnerT: HasProps, GetT, SetT](
    ProxyProp[OwnerT, GetT, SetT], SettableAttr[OwnerT, GetT, SetT]
):
    """
    An attribute with a default value.
    """

    def __init__(
        self,
        proxied: SettableAttr[OwnerT, GetT, SetT],
        default: Callable[[], SetT] | Callable[[OwnerT], SetT],
        /,
    ):

        super().__init__(
            FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
            proxied=proxied,
        )
        self._proxied = proxied
        self._default: Callable[[OwnerT], SetT] = (
            default if len(signature(default).parameters) == 1 else lambda _: default()  # ty:ignore[invalid-assignment, missing-argument]
        )

    def _omit_dump(self, owner: OwnerT, data: GetT) -> bool:
        if data == self._default(owner):
            return True
        return self._proxied.field.omit_dump(owner, data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self._proxied.set(owner, self._default(owner))


@final
class DefaultCollectionAttr[
    OwnerT: HasProps,
    MutableCollectionT: Collection[Any],
    ValuesSetT: Iterable,
](
    ProxyProp[OwnerT, MutableCollectionT, ValuesSetT],
    SettableAttr[OwnerT, MutableCollectionT, ValuesSetT],
):
    """
    A collection attribute with a default value.
    """

    def __init__(
        self,
        proxied: CollectionOwnerAttr[OwnerT, MutableCollectionT, ValuesSetT],
        default: Callable[[], ValuesSetT] | Callable[[OwnerT], ValuesSetT],
        /,
    ):
        super().__init__(
            FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
            proxied=proxied,
        )
        self._proxied = proxied
        self._default: Callable[[OwnerT], ValuesSetT] = (
            default if len(signature(default).parameters) == 1 else lambda _: default()  # ty:ignore[invalid-assignment, missing-argument]
        )

    def _omit_dump(self, owner: OwnerT, data: MutableCollectionT) -> bool:
        if data == self._proxied._data_collection.new(self._default(owner)):
            return True
        return self._proxied.field.omit_dump(owner, data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.set(owner, self._default(owner))
