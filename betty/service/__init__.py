"""
An API for providing application-wide services.
"""

from __future__ import annotations

from betty.typing import internal


@internal
class ServiceError(RuntimeError):
    """
    A service API error.
    """
