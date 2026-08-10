"""
Service level requirements.
"""

from __future__ import annotations

from typing import Final, final, override

from betty.importlib import fully_qualified_name
from betty.requirement import RequirableDecorator, UnmetRequirement
from betty.service_level import DownstreamServiceLevel, ServiceLevel


class _ServiceLevelRequirement:
    def __get__[ServiceLevelT: ServiceLevel](
        self, instance: ServiceLevelT, owner: type[ServiceLevelT]
    ):
        return ServiceLevelRequirement(owner)


@final
class ServiceLevelRequirement[ServiceLevelT: ServiceLevel](RequirableDecorator):
    """
    Check that a service level is available.
    """

    def __init__(self, services: type[ServiceLevelT], /):
        super().__init__()
        self.services: Final[type[ServiceLevelT]] = services
        """
        The required service level.
        """

    @override
    async def _check(self, services: ServiceLevel, /) -> ServiceLevelT:
        # @todo Make reusable
        # @todo
        # @todo
        # @todo
        if isinstance(services, self.services):
            return services
        if isinstance(services, DownstreamServiceLevel):
            return await self._check(services.upstream)
        raise UnmetRequirement(
            f"This requires a(n) {fully_qualified_name(self.services)}, but a(n) {services} was given."
        )


class RequirableServiceLevel(ServiceLevel):
    """
    A service level that can be required.
    """

    require: Final[_ServiceLevelRequirement] = _ServiceLevelRequirement()
