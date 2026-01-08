"""
Aggregate data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from typing_extensions import override

from betty.data import DataDefinition
from betty.data.indicator.selector import Element
from betty.exception import reraise_with_indicator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.service.level import ServiceLevel

_DataT = TypeVar("_DataT")
_ElementT = TypeVar("_ElementT", bound=Element[Any])


class AggregateDefinition(DataDefinition[_DataT], ABC, Generic[_DataT, _ElementT]):
    """
    Define an aggregate data type, e.g. data that consists of other parts.
    """

    @abstractmethod
    def elements(self, data: _DataT) -> Sequence[tuple[_ElementT, DataDefinition]]:
        """
        The selectors and definitions for all elements contained by the data.
        """

    @override
    async def hydrate(self, data: _DataT, services: ServiceLevel, /) -> None:
        for selector, element in self.elements(data):
            with reraise_with_indicator(selector):
                await element.hydrate(selector.get(data), services)
        await super().hydrate(data, services)
