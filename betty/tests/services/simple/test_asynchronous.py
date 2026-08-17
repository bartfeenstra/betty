from __future__ import annotations

import pytest

from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service import Service
from betty.services.simple import AsynchronousServiceManager


class TestAsynchronousServiceManager:
    async def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class _Owner(HasProps):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner()
        assert await owner.my_first_service is my_first_service_value

    async def test_get__with_factory(self) -> None:
        my_first_service_value = object()

        class _Owner(HasProps):
            my_first_service = AsynchronousServiceManager(
                lambda _: my_first_service_value
            )

        owner = _Owner()
        assert await owner.my_first_service is my_first_service_value

    async def test_get__with_life_cycle_without_managed_life_cycle_owner(self) -> None:
        my_first_service_value = LifeCycle()

        class _Owner(HasProps):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner()
        with pytest.raises(TypeError):
            await owner.my_first_service

    async def test_get__with_life_cycle_with_managed_life_cycle_owner(self) -> None:
        my_first_service_value = LifeCycle()

        class _Owner(HasProps, ManagedLifeCycle):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner()
        async with owner:
            actual = await owner.my_first_service
            assert actual is my_first_service_value
            assert actual.bootstrapped
