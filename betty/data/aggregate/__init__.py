"""
Aggregate data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from betty.data import DataDefinition
from betty.data.indicator.selector import Element

if TYPE_CHECKING:
    from collections.abc import Sequence

_DataClsT = TypeVar("_DataClsT")
_ElementT = TypeVar("_ElementT", bound=Element[Any], default=Element[Any])


class AggregateDefinition(
    DataDefinition[_DataClsT], ABC, Generic[_DataClsT, _ElementT]
):
    """
    Define an aggregate data type, e.g. data that consists of other parts.
    """

    @abstractmethod
    def elements(self, data: _DataClsT) -> Sequence[tuple[_ElementT, DataDefinition]]:
        """
        The selectors and definitions for all elements contained by the data.
        """
