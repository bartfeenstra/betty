"""
Floating-point number validators.
"""

from __future__ import annotations

from betty.validators.number import IsNumber

is_float = IsNumber(type=float)
"""
Validate that a value is a Python ``float``.
"""
