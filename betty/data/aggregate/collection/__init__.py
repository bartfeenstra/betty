"""
Collection data types.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import override

from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element

if TYPE_CHECKING:
    from betty.data import DataDefinition
    from betty.locale.localizable import LocalizableLike
    from betty.portable import Porter
    from betty.service.level import ServiceLevel

_CollectionT = TypeVar("_CollectionT", bound=Collection)
_ElementT = TypeVar("_ElementT", bound=Element[Any])


class CollectionDefinition(AggregateDefinition[_CollectionT, _ElementT]):
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
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            porter=porter,
            empty=lambda data: not len(data),
        )
        self._item = item

    @property
    def item(self) -> DataDefinition:
        """
        The definition of the items contained by this collection.
        """
        return self._item

    @override
    async def _hydrate_element(
        self, services: ServiceLevel, data: Any, selector: _ElementT, /
    ) -> None:
        await self._item.hydrate(services, data)
