"""
Requirements for services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypedDict

from betty.exception import HumanFacingException

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


@final
class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """


class ServiceLevelKwargs(TypedDict):
    """
    The keyword arguments for service-level-dependent callables.
    """

    services: ServiceLevel
