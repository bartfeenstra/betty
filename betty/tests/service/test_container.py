from collections.abc import Awaitable
from typing import Any, Self

import pytest
from typing_extensions import override

from betty.config import Configurable
from betty.locale.localizable import LocalizableLike
from betty.requirement import Requirement, StaticRequirement
from betty.service.bootstrap import NotBootstrappedError
from betty.service.container import (
    ServiceContainer,
    ServiceFactory,
    ServiceInitializedError,
    ServiceManager,
    StaticService,
    _AsynchronousServiceManager,
    _SynchronousServiceManager,
    service,
)
from betty.service.level import ServiceLevel
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class _ServiceProvider(ServiceContainer):
    @override
    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: LocalizableLike, /
    ) -> Requirement | Self:
        return StaticRequirement(DUMMY_LOCALIZABLE)


class _ConfigurableServiceProvider(Configurable[DummyConfiguration], _ServiceProvider):
    pass


class _AsynchronousServiceProvider(_ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    async def my_first_asynchronous_service(self) -> object:
        return self._init_service


class _SynchronousServiceProvider(_ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service
    def my_first_synchronous_service(self) -> object:
        return self._init_service


class _AsynchronousServiceProviderWithOverride(_ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_asynchronous_service.override(self, service)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceProviderWithOverride(_ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_synchronous_service.override(self, service)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _AsynchronousServiceProviderWithOverrideFactory(_ServiceProvider):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_AsynchronousServiceProviderWithOverrideFactory", Awaitable[object]
        ],
    ):
        super().__init__()
        type(self).my_first_asynchronous_service.override_factory(self, service_factory)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceProviderWithOverrideFactory(_ServiceProvider):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_SynchronousServiceProviderWithOverrideFactory", object
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


class TestServiceContainer:
    async def test___aenter__(self) -> None:
        async with _ServiceProvider() as sut:
            assert sut.bootstrapped

    async def test___aexit__(self) -> None:
        async with _ServiceProvider() as sut:
            pass
        assert not sut.bootstrapped

    async def test___del__(self) -> None:
        sut = _ServiceProvider()
        await sut.bootstrap()
        with pytest.warns():
            del sut

    async def test_bootstrap(self) -> None:
        sut = _ServiceProvider()
        await sut.bootstrap()
        try:
            assert sut.bootstrapped
        finally:
            await sut.shutdown()

    async def test_bootstrap__should_mark_configuration_immutable(self) -> None:
        async with _ConfigurableServiceProvider(
            configuration=DummyConfiguration()
        ) as sut:
            assert sut.configuration.immutable

    async def test_shutdown__should_mark_configuration_mutable(self) -> None:
        async with _ConfigurableServiceProvider(
            configuration=DummyConfiguration()
        ) as sut:
            pass
        assert sut.configuration.mutable

    async def test_shutdown(self) -> None:
        sut = _ServiceProvider()
        await sut.bootstrap()
        await sut.shutdown()
        assert not sut.bootstrapped


class TestStaticService:
    def test___call__(self) -> None:
        service = object()
        services = _ServiceProvider()
        sut = StaticService[ServiceContainer, object](service)
        assert sut(services) is service


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
        with pytest.raises(NotBootstrappedError):
            await type(services).my_first_asynchronous_service.get(services)

    async def test_get__instance_attr_with_asynchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _AsynchronousServiceProviderWithOverride(service) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_asynchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()

        async def _service_factory(
            _: _AsynchronousServiceProviderWithOverrideFactory,
        ) -> object:
            return service

        async with _AsynchronousServiceProviderWithOverrideFactory(
            _service_factory
        ) as services:
            assert (
                await type(services).my_first_asynchronous_service.get(services)
                is service
            )

    async def test_get__instance_attr_with_synchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _SynchronousServiceProvider(object()) as services:
            assert type(services).my_first_synchronous_service.get(services) is type(
                services
            ).my_first_synchronous_service.get(services)

    async def test_get__instance_attr_with_synchronous_method_without_bootstrapped(
        self,
    ) -> None:
        services = _SynchronousServiceProvider(object())
        with pytest.raises(NotBootstrappedError):
            type(services).my_first_synchronous_service.get(services)  # noqa: B018

    async def test_get__instance_attr_with_synchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithOverride(service) as services:
            assert type(services).my_first_synchronous_service.get(services) is service

    async def test_get__instance_attr_with_synchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithOverrideFactory(
            lambda _: service
        ) as services:
            assert type(services).my_first_synchronous_service.get(services) is service

    async def test___get____with_class_attr(self) -> None:
        _AsynchronousServiceProvider.my_first_asynchronous_service  # noqa B018

    async def test___get____with_instance_attr_with_asynchronous_method(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(service) as services:
            assert await services.my_first_asynchronous_service is service

    async def test___get____with_instance_attr_with_synchronous_method(self) -> None:
        service = object()
        async with _SynchronousServiceProvider(service) as services:
            assert services.my_first_synchronous_service is service

    async def test_override(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(object()) as services:
            type(services).my_first_asynchronous_service.override(services, service)
            assert await services.my_first_asynchronous_service is service

    async def test_override__with_override_with_initialized_already(self) -> None:
        async with _AsynchronousServiceProviderWithOverride(object()) as services:
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
            services: _AsynchronousServiceProviderWithOverride,
        ) -> object:
            return object()

        async with _AsynchronousServiceProviderWithOverride(object()) as services:
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
