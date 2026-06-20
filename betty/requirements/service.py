"""
Service requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from betty.requirement import UnmetRequirement
from betty.service import ServiceError, ServiceManager

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.indicator import Indicator
    from betty.locale.localizable import ResolvableLocalizable


class UnmetServiceRequirement(UnmetRequirement, ServiceError):
    """
    Raised when a requirement on a service is not met.
    """

    def __init__(
        self,
        service: ServiceManager,
        message: ResolvableLocalizable,
        *,
        indicators: Sequence[Indicator] = (),
    ):
        super().__init__(message, indicators=indicators)
        self.service: Final[ServiceManager] = service
        """
        The service for which the error was raised.
        """
