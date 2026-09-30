"""
Floating-point number validators.
"""

from __future__ import annotations

from betty.validators.number import IsNumberType

is_float = IsNumberType(type=float)
"""
Validate that a value is a Python number.
"""
