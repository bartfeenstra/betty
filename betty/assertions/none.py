"""
``None`` assertions.
"""

from __future__ import annotations

from types import NoneType

from betty.assertions.type import assert_type

assert_none = assert_type(NoneType)
"""
Assert that a value is ``None``.
"""
