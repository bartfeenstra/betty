"""
Boolean data assertions.
"""

from __future__ import annotations

from betty.assertions.type import assert_type

assert_bool = assert_type(bool)
"""
Assert that a value is a Python ``bool``.
"""
