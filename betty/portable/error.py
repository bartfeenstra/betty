"""
Errors for the portable data API.
"""

from __future__ import annotations

from typing import final

from betty.exception import HumanFacingException


@final
class NotDumpable(HumanFacingException):
    """
    Raised when data is not dumpable.
    """
