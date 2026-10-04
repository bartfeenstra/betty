"""
Errors for the portable data API.
"""

from __future__ import annotations

from typing import final

from betty.user.error import UserFacingError


@final
class NotPortable(UserFacingError):
    """
    Raised when data is not portable.
    """


@final
class NotDumpable(UserFacingError):
    """
    Raised when data is not dumpable.
    """
