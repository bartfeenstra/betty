"""
Integral number validators.
"""

from __future__ import annotations

from betty.validators.number import IsNumber

is_int = IsNumber(type=int)
"""
Validate that a value is a Python ``int``.
"""
