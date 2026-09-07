"""
Key-value mapping record data types.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, final

from betty.datas.aggregate.record import RecordDefinition
from betty.indicator.operator import Key
from betty.portable import Porter


@final
class TypedMappingDefinition[
    MutableMappingT: MutableMapping[str, Any],
    PorterT: Porter[MutableMapping] = Porter,
](RecordDefinition[MutableMappingT, Key, PorterT]):
    """
    A typed mapping definition.

    Actual values do not have to be :py:class:`typing.TypedDict`. They can be any mapping, but like typed dicts, values
    are limited to the defined elements.
    """
