from collections.abc import Awaitable
from typing import Any, override

import pytest

from betty.life_cycle import NotYetBootstrapped
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service.provider import (
    ServiceFactory,
    ServiceInitializedError,
    ServiceManager,
    _AsynchronousServiceManager,
    _SynchronousServiceManager,
    service,
)
from betty.test_utils.service.level import DummyDataManufacturable


class _DataManufacturableManagedLifeCycle(DummyDataManufacturable, ManagedLifeCycle):
    pass


class _AsynchronousManagedLifeCycle(ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    async def my_first_asynchronous_service(self) -> object:
        return self._init_service


class _SynchronousManagedLifeCycle(ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    def my_first_synchronous_service(self) -> object:
        return self._init_service


class _AsynchronousManagedLifeCycleWithOverride(ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_asynchronous_service.override(self, service)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousManagedLifeCycleWithOverride(ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_synchronous_service.override(self, service)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _AsynchronousManagedLifeCycleWithOverrideFactory(ManagedLifeCycle):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_AsynchronousManagedLifeCycleWithOverrideFactory", Awaitable[object]
        ],
    ):
        super().__init__()
        type(self).my_first_asynchronous_service.override_factory(self, service_factory)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousManagedLifeCycleWithOverrideFactory(ManagedLifeCycle):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_SynchronousManagedLifeCycleWithOverrideFactory", object
        ],
    ):
        super().__init__()
        type(self).my_first_synchronous_service.override_factory(self, service_factory)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _DummyServiceManager(ServiceManager[Any, None, None]):
    @override
    def _get(self, instance: Any) -> None:
        return None


class TestManagedLifeCycle:
    def test(self) -> None:
        ManagedLifeCycle()


class TestServiceManager:
    def test_name(self) -> None:
        def my_first_service(_: Any) -> None:
            return None

        sut = _DummyServiceManager(my_first_service)
        assert sut.name == "my_first_service"

    async def test_get__with_asynchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _AsynchronousManagedLifeCycle(object()) as services:
            assert await type(services).my_first_asynchronous_service.get(
                services
            ) is await type(services).my_first_asynchronous_service.get(services)

    async def test_get__with_asynchronous_method_without_bootstrapped(
        self,
    ) -> None:
        services = _AsynchronousManagedLifeCycle(object())
        with pytest.raises(NotYetBootstrapped):
            await type(services).my_first_asynchronous_service.get(services)

    async def test_get__instance_attr_with_asynchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _AsynchronousManagedLifeCycleWithOverride(service) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_asynchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()

        async def _service_factory(
            _: _AsynchronousManagedLifeCycleWithOverrideFactory,
        ) -> object:
            return service

        async with _AsynchronousManagedLifeCycleWithOverrideFactory(
            _service_factory
        ) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_synchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _SynchronousManagedLifeCycle(object()) as services:
            assert type(services).my_first_synchronous_service.get(services) is type(
                services
            ).my_first_synchronous_service.get(services)

    async def test_get__instance_attr_with_synchronous_method_without_bootstrapped(
        self,
    ) -> None:
        services = _SynchronousManagedLifeCycle(object())
        with pytest.raises(NotYetBootstrapped):
            type(services).my_first_synchronous_service.get(services)  # noqa: B018

    async def test_get__instance_attr_with_synchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousManagedLifeCycleWithOverride(service) as services:
            assert type(services).my_first_synchronous_service.get(services) is service

    async def test_get__instance_attr_with_synchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousManagedLifeCycleWithOverrideFactory(
            lambda _: service
        ) as services:
            assert type(services).my_first_synchronous_service.get(services) is service

    async def test___get____with_class_attr(self) -> None:
        _AsynchronousManagedLifeCycle.my_first_asynchronous_service  # noqa: B018

    async def test___get____with_instance_attr_with_asynchronous_method(self) -> None:
        service = object()
        async with _AsynchronousManagedLifeCycle(service) as services:
            assert await services.my_first_asynchronous_service is service

    async def test___get____with_instance_attr_with_synchronous_method(self) -> None:
        service = object()
        async with _SynchronousManagedLifeCycle(service) as services:
            assert services.my_first_synchronous_service is service

    async def test_override(self) -> None:
        service = object()
        async with _AsynchronousManagedLifeCycle(object()) as services:
            type(services).my_first_asynchronous_service.override(services, service)
            assert await services.my_first_asynchronous_service is service

    async def test_override__with_override_with_initialized_already(self) -> None:
        async with _AsynchronousManagedLifeCycleWithOverride(object()) as services:
            with pytest.raises(ServiceInitializedError):
                type(services).my_first_asynchronous_service.override(
                    services, object()
                )

    async def test_override_factory(self) -> None:
        service = object()

        async def _factory(
            services: _AsynchronousManagedLifeCycle,
        ) -> object:
            return service

        async with _AsynchronousManagedLifeCycle(object()) as services:
            type(services).my_first_asynchronous_service.override_factory(
                services, _factory
            )
            assert await services.my_first_asynchronous_service is service

    async def test_override_factory__with_override_with_initialized_already(
        self,
    ) -> None:
        async def _factory(
            services: _AsynchronousManagedLifeCycleWithOverride,
        ) -> object:
            return object()

        async with _AsynchronousManagedLifeCycleWithOverride(object()) as services:
            with pytest.raises(ServiceInitializedError):
                type(services).my_first_asynchronous_service.override_factory(
                    services, _factory
                )


async def test_service__with_asynchronous_method() -> None:
    assert isinstance(
        _AsynchronousManagedLifeCycle.my_first_asynchronous_service,
        _AsynchronousServiceManager,
    )


async def test_service__with_synchronous_method() -> None:
    assert isinstance(
        _SynchronousManagedLifeCycle.my_first_synchronous_service,
        _SynchronousServiceManager,
    )
