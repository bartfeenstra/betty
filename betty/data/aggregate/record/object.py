"""
Object data types.
"""

from __future__ import annotations

from typing import TypeVar

from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Attr

_DataClsT = TypeVar("_DataClsT")


class ObjectDefinition(RecordDefinition[_DataClsT, Attr]):
    """
    An object definition.
    """
