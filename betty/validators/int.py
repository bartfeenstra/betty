"""
Integral number validators.
"""

from __future__ import annotations

from betty.validators.number import IsNumberType

is_int = IsNumberType(type=int)
"""
Validate that a value is a Python ``int``.
"""
