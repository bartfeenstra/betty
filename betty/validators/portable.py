"""
Portable data validation.
"""

from __future__ import annotations

from typing import Any

from betty.localizables.gettext import _
from betty.pipeline import Vent
from betty.portable import PortableData, is_portable_scalar
from betty.typing import is_runtime_checkable_mapping, is_runtime_checkable_sequence
from betty.validation import Invalid
from betty.validators.mapping import is_mapping
from betty.validators.sequence import is_sequence
from betty.validators.str import is_str_min_len


def is_portable_data(value: Any, /) -> PortableData:
    """
    Assert that a value is portable data.
    """
    if is_portable_scalar(value):
        return value
    if is_runtime_checkable_sequence(value):
        return assert_portable_sequence(value)
    if is_runtime_checkable_mapping(value):
        return assert_portable_mapping(value)
    raise Invalid(
        value,
        message=_(
            "This must consist of none/null, booleans, numbers, strings, or sequences or string-keyed mappings of all of those."
        ),
    )


assert_portable_sequence = Vent(is_sequence(values=is_portable_data))
assert_portable_mapping = Vent(
    is_mapping(keys=is_str_min_len(1), values=is_portable_data)
)
