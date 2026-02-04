from collections.abc import Awaitable, Callable
from typing import TypeAlias

import pytest

from betty.service.level import ServiceLevel
from betty.service.requirement import Requirement, UnmetRequirement


class _RequiredServiceLevel(ServiceLevel):
    pass


async def _require(services: ServiceLevel, target: str, /) -> _RequiredServiceLevel:
    if isinstance(services, _RequiredServiceLevel):
        return services
    raise UnmetRequirement("")


@Requirement(_require)
def _require_target_sync(services: _RequiredServiceLevel, /) -> _RequiredServiceLevel:
    return services


@Requirement(_require)
async def _require_target_async(
    services: _RequiredServiceLevel, /
) -> _RequiredServiceLevel:
    return services


class _RequireTargetClassMethod:
    @classmethod
    @Requirement(_require)
    async def target(cls, services: _RequiredServiceLevel, /) -> _RequiredServiceLevel:
        return services


class _RequireTargetInstanceMethod:
    @Requirement(_require)
    async def target(self, services: _RequiredServiceLevel, /) -> _RequiredServiceLevel:
        return services


_targets = pytest.mark.parametrize(
    "target",
    [
        _require_target_sync,
        _require_target_async,
        _RequireTargetClassMethod.target,
        _RequireTargetInstanceMethod().target,
    ],
)
_Target: TypeAlias = Callable[[ServiceLevel], Awaitable[_RequiredServiceLevel]]


class TestRequirement:
    async def test___call____with_services_with_requirement_unmet(self) -> None:
        sut = Requirement(_require)
        with pytest.raises(UnmetRequirement):
            assert await sut(ServiceLevel())

    async def test___call____with_services_with_requirement_met(self) -> None:
        sut = Requirement(_require)
        services = _RequiredServiceLevel()
        assert await sut(services) is services

    async def test___call____with__decorated_callable_with_requirement_unmet(
        self,
    ) -> None:
        def _require_target(
            services: _RequiredServiceLevel, /
        ) -> _RequiredServiceLevel:
            return services

        sut = Requirement(_require)
        with pytest.raises(UnmetRequirement):
            await sut(_require_target)(ServiceLevel())

    async def test___call____with__decorated_callable_with_requirement_met(
        self,
    ) -> None:
        def _require_target(
            services: _RequiredServiceLevel, /
        ) -> _RequiredServiceLevel:
            return services

        sut = Requirement(_require)
        services = _RequiredServiceLevel()
        assert await sut(_require_target)(services) is services


class TestCallableRequirement:
    @_targets
    async def test___call____with_requirement_unmet(self, target: _Target) -> None:
        with pytest.raises(UnmetRequirement):
            await target(ServiceLevel())

    @_targets
    async def test___call____with_requirement_met(self, target: _Target) -> None:
        services = _RequiredServiceLevel()
        assert await target(services) is services
