"""
Errors for the portable data API.
"""

from __future__ import annotations

from typing import final

from betty.exception import HumanFacingException


@final
class NotPortable(HumanFacingException):
    """
    Raised when data is not portable.
    """
