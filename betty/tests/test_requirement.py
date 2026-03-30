from __future__ import annotations

from typing import override

import pytest

from betty.requirement import (
    RequirableDecorator,
    UnmetRequirement,
)
from betty.service.level import (
    DownstreamServiceLevel,
    ServiceLevel,
)


class _ServiceLevel(ServiceLevel):
    pass


class _DownstreamServiceLevel(DownstreamServiceLevel):
    pass


async def _requirement(services: ServiceLevel, /) -> _ServiceLevel:
    if isinstance(services, _ServiceLevel):
        return services
    raise UnmetRequirement("")


class TestRequirableDecorator:
    class _RequirableDecorator(
        RequirableDecorator[tuple[_ServiceLevel, _ServiceLevel]]
    ):
        @override
        async def _check(
            self, services: ServiceLevel, /
        ) -> tuple[_ServiceLevel, _ServiceLevel]:
            if isinstance(services, _ServiceLevel):
                return services, services
            raise UnmetRequirement("uh-oh")

    async def test___call____with_services_and_unmet_requirement(self) -> None:
        with pytest.raises(UnmetRequirement):
            await self._RequirableDecorator()(ServiceLevel())

    async def test___call____with_services_and_met_requirement(self) -> None:
        services = _ServiceLevel()
        assert await self._RequirableDecorator()(services) == (services, services)

    async def test___call____with_decorated_and_unmet_requirement(self) -> None:
        with pytest.raises(UnmetRequirement):
            await self._RequirableDecorator()(lambda services: (services, services))(
                ServiceLevel()
            )

    async def test___call____with_decorated_and_met_requirement(self) -> None:
        services = _ServiceLevel()
        assert await self._RequirableDecorator()(
            lambda services_pair: (services_pair, services_pair)
        )(services) == ((services, services), (services, services))
