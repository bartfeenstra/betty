"""
Errors for the portable data API.
"""

from __future__ import annotations

from typing import final

from betty.error import Error


@final
class NotPortable(Error):
    """
    Raised when data is not portable.
    """


@final
class NotDumpable(Error):
    """
    Raised when data is not dumpable.
    """
