"""
Collection attributes with default values.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.owner import ProxyOwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.attrs.collection_attr import CollectionAttrAttr


@final
class DefaultCollectionAttr[
    OwnerT: HasProperties,
    MutableCollectionT: Collection[Any],
    ValuesSetT: Iterable,
](ProxyOwnerAttr[OwnerT, MutableCollectionT, ValuesSetT]):
    """
    A collection attribute with a default value.
    """

    def __init__(
        self,
        proxied: CollectionAttrAttr[OwnerT, MutableCollectionT, ValuesSetT],
        default: Callable[[], ValuesSetT],
        /,
    ):
        super().__init__(
            proxied,
            field=FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
        )
        self._proxied = proxied
        self._default = default

    def _omit_dump(self, data: MutableCollectionT) -> bool:
        if data == self._proxied._data_collection.new(self._default()):
            return True
        return self._proxied.field.omit_dump(data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.set(owner, self._default())
