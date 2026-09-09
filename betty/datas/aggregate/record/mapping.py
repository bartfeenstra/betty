"""
Key-value mapping record data types.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, final

from betty.datas.aggregate.record import RecordDefinition
from betty.indicator.operator import Key


@final
class TypedMappingDefinition[MappingT: Mapping[str, Any]](
    RecordDefinition[MappingT, Key]
):
    """
    A typed mapping definition.

    Actual values do not have to be :py:class:`typing.TypedDict`. They can be any mapping, but like typed dicts, values
    are limited to the defined elements.
    """
