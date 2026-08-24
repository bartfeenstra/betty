from __future__ import annotations

from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service import Service
from betty.service_level import HasServiceLevel, ServiceLevel
from betty.services.simple import SynchronousServiceManager


class TestSynchronousServiceManager:
    async def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class _Owner(HasServiceLevel, HasProps, ManagedLifeCycle):
            my_first_service = SynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner(services=ServiceLevel())
        async with owner:
            assert owner.my_first_service is my_first_service_value

    async def test_get__with_factory(self) -> None:
        my_first_service = object()

        class _Owner(HasServiceLevel, HasProps, ManagedLifeCycle):
            my_first_service = SynchronousServiceManager(lambda _: my_first_service)

        owner = _Owner(services=ServiceLevel())
        async with owner:
            assert owner.my_first_service is my_first_service
