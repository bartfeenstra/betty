"""
Collection data types.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVar

from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element

if TYPE_CHECKING:
    from betty.data import DataDefinition
    from betty.locale.localizable import LocalizableLike
    from betty.portable import Porter

_CollectionT = TypeVar("_CollectionT", bound=Collection)
_ElementCoT = TypeVar("_ElementCoT", bound=Element[Any], covariant=True)


class CollectionDefinition(AggregateDefinition[_CollectionT, _ElementCoT]):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_CollectionT] | None = None,
        item: DataDefinition,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        porter: Porter[_CollectionT] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description, porter=porter)
        self._item = item

    @property
    def item(self) -> DataDefinition:
        """
        The definition of the items contained by this collection.
        """
        return self._item
