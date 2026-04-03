from collections.abc import Awaitable
from typing import Any, override

import pytest

from betty.life_cycle import NotYetBootstrapped
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service.provider import (
    ServiceFactory,
    ServiceInitializedError,
    ServiceManager,
    ServiceProvider,
    _AsynchronousServiceManager,
    _SynchronousServiceManager,
    service,
)
from betty.test_utils.service.level import DummyDataManufacturable


class _DataManufacturableManagedLifeCycle(DummyDataManufacturable, ManagedLifeCycle):
    pass


class _AsynchronousServiceProvider(ServiceProvider, ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    async def my_first_asynchronous_service(self) -> object:
        return self._init_service


class _SynchronousServiceProvider(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    def my_first_synchronous_service(self) -> object:
        return self._init_service


class _AsynchronousServiceWithOverrideProvider(ServiceProvider, ManagedLifeCycle):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_asynchronous_service.override(self, service)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceWithOverrideProvider(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_synchronous_service.override(self, service)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _AsynchronousServiceWithOverrideFactoryProvider(
    ServiceProvider, ManagedLifeCycle
):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_AsynchronousServiceWithOverrideFactoryProvider", Awaitable[object]
        ],
    ):
        super().__init__()
        type(self).my_first_asynchronous_service.override_factory(self, service_factory)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceWithOverrideFactoryProvider(ServiceProvider):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_SynchronousServiceWithOverrideFactoryProvider", object
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
        async with _AsynchronousServiceProvider(object()) as services:
            assert await type(services).my_first_asynchronous_service.get(
                services
            ) is await type(services).my_first_asynchronous_service.get(services)

    async def test_get__with_asynchronous_method_without_bootstrapped(
        self,
    ) -> None:
        services = _AsynchronousServiceProvider(object())
        with pytest.raises(NotYetBootstrapped):
            await type(services).my_first_asynchronous_service.get(services)

    async def test_get__instance_attr_with_asynchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _AsynchronousServiceWithOverrideProvider(service) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_asynchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()

        async def _service_factory(
            _: _AsynchronousServiceWithOverrideFactoryProvider,
        ) -> object:
            return service

        async with _AsynchronousServiceWithOverrideFactoryProvider(
            _service_factory
        ) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_synchronous_method_with_bootstrapped(
        self,
    ) -> None:
        services = _SynchronousServiceProvider(object())
        assert type(services).my_first_synchronous_service.get(services) is type(
            services
        ).my_first_synchronous_service.get(services)

    async def test_get__instance_attr_with_synchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        services = _SynchronousServiceWithOverrideProvider(service)
        assert type(services).my_first_synchronous_service.get(services) is service

    async def test_get__instance_attr_with_synchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()
        services = _SynchronousServiceWithOverrideFactoryProvider(lambda _: service)
        assert type(services).my_first_synchronous_service.get(services) is service

    async def test___get____with_class_attr(self) -> None:
        _AsynchronousServiceProvider.my_first_asynchronous_service  # noqa: B018

    async def test___get____with_instance_attr_with_asynchronous_method(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(service) as services:
            assert await services.my_first_asynchronous_service is service

    async def test___get____with_instance_attr_with_synchronous_method(self) -> None:
        service = object()
        services = _SynchronousServiceProvider(service)
        assert services.my_first_synchronous_service is service

    async def test_override(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(object()) as services:
            type(services).my_first_asynchronous_service.override(services, service)
            assert await services.my_first_asynchronous_service is service

    async def test_override__with_override_with_initialized_already(self) -> None:
        async with _AsynchronousServiceWithOverrideProvider(object()) as services:
            with pytest.raises(ServiceInitializedError):
                type(services).my_first_asynchronous_service.override(
                    services, object()
                )

    async def test_override_factory(self) -> None:
        service = object()

        async def _factory(
            services: _AsynchronousServiceProvider,
        ) -> object:
            return service

        async with _AsynchronousServiceProvider(object()) as services:
            type(services).my_first_asynchronous_service.override_factory(
                services, _factory
            )
            assert await services.my_first_asynchronous_service is service

    async def test_override_factory__with_override_with_initialized_already(
        self,
    ) -> None:
        async def _factory(
            services: _AsynchronousServiceWithOverrideProvider,
        ) -> object:
            return object()

        async with _AsynchronousServiceWithOverrideProvider(object()) as services:
            with pytest.raises(ServiceInitializedError):
                type(services).my_first_asynchronous_service.override_factory(
                    services, _factory
                )


async def test_service__with_asynchronous_method() -> None:
    assert isinstance(
        _AsynchronousServiceProvider.my_first_asynchronous_service,
        _AsynchronousServiceManager,
    )


async def test_service__with_synchronous_method() -> None:
    assert isinstance(
        _SynchronousServiceProvider.my_first_synchronous_service,
        _SynchronousServiceManager,
    )
