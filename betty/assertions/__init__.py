"""
Assertions to validate and convert arbitrary data.
"""

from __future__ import annotations

from betty.exception import HumanFacingException


class _HumanFacingValueError(HumanFacingException, ValueError):
    pass
