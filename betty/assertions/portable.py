"""
Portable data assertions.
"""

from __future__ import annotations

from typing import Any

from betty.assertions.mapping import assert_mapping
from betty.assertions.sequence import assert_sequence
from betty.assertions.str import assert_str
from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.pipeline import Vent
from betty.portable import PortableData, is_portable_scalar
from betty.typing import is_runtime_checkable_mapping, is_runtime_checkable_sequence


def assert_portable_data(value: Any, /) -> PortableData:
    """
    Assert that a value is portable data.
    """
    if is_portable_scalar(value):
        return value
    if is_runtime_checkable_sequence(value):
        return assert_portable_sequence(value)
    if is_runtime_checkable_mapping(value):
        return assert_portable_mapping(value)
    raise HumanFacingException(
        _(
            "This must consist of none/null, booleans, numbers, strings, or sequences or string-keyed mappings of all of those."
        )
    )


assert_portable_sequence = Vent(assert_sequence(assert_portable_data))
assert_portable_mapping = Vent(
    assert_mapping(assert_portable_data, assert_str(minimum_length=1))
)
