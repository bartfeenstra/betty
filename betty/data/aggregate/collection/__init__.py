"""
Collection data types.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any

from betty.data import DataDefinition
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element

if TYPE_CHECKING:
    from betty.data import Data
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import Porter


class CollectionDefinition[CollectionT: Collection, ElementT: Element[Any]](
    AggregateDefinition[CollectionT, ElementT]
):
    """
    A homogenous collection data definition.
    """

    def __init__(
        self,
        /,
        cls: type[CollectionT] | None = None,
        *,
        item: DataDefinition | type[Data],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[CollectionT] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description, porter=porter)
        self._item = item if isinstance(item, DataDefinition) else item.data()

    @property
    def item(self) -> DataDefinition:
        """
        The definition of the items contained by this collection.
        """
        return self._item
