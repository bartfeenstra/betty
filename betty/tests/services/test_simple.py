from __future__ import annotations

from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service_level import HasServiceLevel, ServiceLevel
from betty.services.simple import service


async def test_service__with_asynchronous_service() -> None:
    my_first_service = object()

    class _Owner(HasServiceLevel, HasProps, ManagedLifeCycle):
        @service
        async def my_first_service(self) -> object:
            return my_first_service

    owner = _Owner(services=ServiceLevel())
    async with owner:
        assert await owner.my_first_service is my_first_service


async def test_service__with_synchronous_service() -> None:
    my_first_service = object()

    class _Owner(HasServiceLevel, HasProps, ManagedLifeCycle):
        @service
        def my_first_service(self) -> object:
            return my_first_service

    owner = _Owner(services=ServiceLevel())
    async with owner:
        assert owner.my_first_service is my_first_service
