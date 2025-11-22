"""
An API for providing application-wide services.
"""

from betty.typing import internal


@internal
class ServiceError(RuntimeError):
    """
    A service API error.
    """
