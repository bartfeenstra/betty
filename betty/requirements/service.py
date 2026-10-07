"""
Service requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from betty.requirement import UnmetRequirement

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.service import ServiceManager


class UnmetServiceRequirement(UnmetRequirement):
    """
    Raised when a requirement on a service is not met.
    """

    def __init__(self, service: ServiceManager, message: ResolvableLocalizable, /):
        super().__init__(message)
        self.service: Final[ServiceManager] = service
        """
        The service for which the error was raised.
        """
