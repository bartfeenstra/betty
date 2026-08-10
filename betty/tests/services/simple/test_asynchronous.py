from __future__ import annotations

from betty.life_cycle import LifeCycle
from betty.service import HasServices, Service
from betty.service_level import ServiceLevel
from betty.services.simple import AsynchronousServiceManager


class TestAsynchronousServiceManager:
    async def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class _Owner(HasServices):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner(services=ServiceLevel())
        assert await owner.my_first_service is my_first_service_value

    async def test_get__with_factory(self) -> None:
        my_first_service_value = object()

        class _Owner(HasServices):
            my_first_service = AsynchronousServiceManager(
                lambda _: my_first_service_value
            )

        owner = _Owner(services=ServiceLevel())
        assert await owner.my_first_service is my_first_service_value

    async def test_get__with_life_cycle(self) -> None:
        my_first_service_value = LifeCycle()

        class _Owner(HasServices):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        async with _Owner(services=ServiceLevel()) as service_provider:
            actual = await service_provider.my_first_service
            assert actual is my_first_service_value
            assert actual.bootstrapped
