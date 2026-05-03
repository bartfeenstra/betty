"""
Aggregate data types.
"""

from __future__ import annotations

from typing import Any

from betty.data import DataDefinition
from betty.indicator.selector import Element


class AggregateDefinition[DataClsT, ElementT: Element[Any] = Element[Any]](
    DataDefinition[DataClsT]
):
    """
    Define an aggregate data type, e.g. data that consists of other parts.
    """
