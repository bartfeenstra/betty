from __future__ import annotations

from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service import Service, ServiceProvider
from betty.service_level import ServiceLevel
from betty.services.simple import AsynchronousServiceManager


class TestAsynchronousServiceManager:
    async def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        service_provider = Cls(services=ServiceLevel())
        assert await service_provider.my_first_service is my_first_service_value

    async def test_get__with_factory(self) -> None:
        my_first_service_value = object()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                lambda _: my_first_service_value
            )

        service_provider = Cls(services=ServiceLevel())
        assert await service_provider.my_first_service is my_first_service_value

    async def test_get__with_life_cycle(self) -> None:
        my_first_service_value = LifeCycle()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        async with Cls(services=ServiceLevel()) as service_provider:
            actual = await service_provider.my_first_service
            assert actual is my_first_service_value
            assert actual.bootstrapped
