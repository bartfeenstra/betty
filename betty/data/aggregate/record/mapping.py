"""
Key-value mapping record data types.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, final

from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Key


@final
class TypedMappingDefinition[MutableMappingT: MutableMapping[str, Any]](
    RecordDefinition[MutableMappingT, Key]
):
    """
    A typed mapping definition.

    Actual values do not have to be :py:class:`typing.TypedDict`. They can be any mapping, but like typed dicts, values
    are limited to the defined elements.
    """
