"""
Aggregate data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from betty.data import DataDefinition
from betty.data.indicator.selector import Element

if TYPE_CHECKING:
    from collections.abc import Sequence


class AggregateDefinition[DataClsT, ElementT: Element[Any] = Element[Any]](
    DataDefinition[DataClsT], ABC
):
    """
    Define an aggregate data type, e.g. data that consists of other parts.
    """

    @abstractmethod
    def elements(self, data: DataClsT) -> Sequence[tuple[ElementT, DataDefinition]]:
        """
        The selectors and definitions for all elements contained by the data.
        """
