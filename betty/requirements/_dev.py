from __future__ import annotations

from typing import Final, final, override

from betty.about import is_dev, version
from betty.requirement import RequirableDecorator, UnmetRequirement
from betty.service_level import ServiceLevel


@final
class _DevRequirement(RequirableDecorator):
    @override
    async def _check[ServiceLevelT: ServiceLevel](
        self, services: ServiceLevelT, /
    ) -> ServiceLevelT:
        if is_dev:
            return services
        raise UnmetRequirement(
            f"This requires a Betty development installation, but Betty {version} is installed."
        )


require_dev: Final[_DevRequirement] = _DevRequirement()
