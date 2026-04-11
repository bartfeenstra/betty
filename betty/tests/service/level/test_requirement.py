from __future__ import annotations

import pytest

from betty.requirement import UnmetRequirement
from betty.service.level import DownstreamServiceLevel, ServiceLevel
from betty.service.level.requirement import (
    RequirableServiceLevel,
    ServiceLevelRequirement,
)


class _ServiceLevel(ServiceLevel):
    pass


class _DownstreamServiceLevel(DownstreamServiceLevel):
    pass


class TestServiceLevelRequirement:
    def test_services(self) -> None:
        assert ServiceLevelRequirement(_ServiceLevel).services is _ServiceLevel

    async def test___call____unmet(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        with pytest.raises(UnmetRequirement):
            await sut(ServiceLevel())

    async def test___call____met(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        services = _ServiceLevel()
        assert await sut(services) is services

    async def test___call____chained_unmet(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        with pytest.raises(UnmetRequirement):
            await sut(_DownstreamServiceLevel(upstream=ServiceLevel()))

    async def test___call____chained_met(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        services = _ServiceLevel()
        assert await sut(_DownstreamServiceLevel(upstream=services)) is services


class TestRequirableServiceLevel:
    def test_require(self) -> None:
        class _RequirableServiceLevel(RequirableServiceLevel):
            pass

        assert _RequirableServiceLevel.require.services is _RequirableServiceLevel
