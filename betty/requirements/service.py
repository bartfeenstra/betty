"""
Service requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from betty.requirement import UnmetRequirement

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizable import ResolvableLocalizable
    from betty.service import ServiceManager
    from betty.user.location import Locator


class UnmetServiceRequirement(UnmetRequirement):
    """
    Raised when a requirement on a service is not met.
    """

    def __init__(
        self,
        service: ServiceManager,
        message: ResolvableLocalizable,
        *,
        locators: Sequence[Locator] = (),
    ):
        super().__init__(message, locators=locators)
        self.service: Final[ServiceManager] = service
        """
        The service for which the error was raised.
        """
