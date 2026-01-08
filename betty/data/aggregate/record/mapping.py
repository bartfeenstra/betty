"""
Key-value mapping record data types.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, TypeVar, final

from betty.data.aggregate.record import RecordDefinition
from betty.data.indicator.selector import Key

_MutableMappingT = TypeVar("_MutableMappingT", bound=MutableMapping[str, Any])


@final
class TypedMappingDefinition(RecordDefinition[_MutableMappingT, Key]):
    """
    A typed mapping definition.

    Actual values do not have to be :py:class:`typing.TypedDict`. They can be any mapping, but like typed dicts, values
    are limited to the defined elements.
    """
