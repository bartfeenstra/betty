"""
Object data types.
"""

from __future__ import annotations

from typing import TypeVar

from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Attr

_DataT = TypeVar("_DataT")


class ObjectDefinition(RecordDefinition[_DataT, Attr]):
    """
    An object definition.
    """
