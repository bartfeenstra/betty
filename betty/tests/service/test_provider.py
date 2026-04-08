from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, override

import pytest

from betty.functools import LazyReCallable
from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.service.provider import (
    AsynchronousServiceManager,
    Service,
    ServiceInitializedError,
    ServiceManager,
    ServiceProvider,
    SynchronousServiceManager,
    service,
)
from betty.universe import UNIVERSE

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


class _DummyServiceManager[ServiceProviderT: ServiceProvider](
    ServiceManager[ServiceProviderT, object, object, Callable[[], object], object]
):
    @override
    def _new_service_getter(
        self, services: ServiceLevel, instance: ServiceProviderT, /
    ) -> Callable[[], object]:
        def _factory() -> object:
            factory = self._get_service_or_factory(instance)
            if isinstance(factory, Service):
                return factory.service
            return factory(instance)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], object], /) -> object:
        return service()


class TestServiceManager:
    def test___get____class(self) -> None:
        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        assert isinstance(_ServiceProvider.my_first_service, _DummyServiceManager)
        assert _ServiceProvider.my_first_service is _ServiceProvider.my_first_service

    def test___get____instance(self) -> None:
        service = object()

        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                return service

        assert _ServiceProvider(services=UNIVERSE).my_first_service is service

    def test___set_name__(self) -> None:
        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

    def test_get(self) -> None:
        service = object()

        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                return service

        assert (
            _ServiceProvider.my_first_service.get(_ServiceProvider(services=UNIVERSE))
            is service
        )

    def test_init__initialized_already(self) -> None:
        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service_provider = _ServiceProvider(services=UNIVERSE)
        with pytest.raises(ServiceInitializedError):
            _ServiceProvider.my_first_service.init(UNIVERSE, service_provider)

    def test_override(self) -> None:
        class _ServiceProvider(ServiceProvider):
            def __init__(self, my_first_service: object, /):
                type(self).my_first_service.override(self, Service(my_first_service))
                super().__init__(services=UNIVERSE)

            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service = object()
        service_provider = _ServiceProvider(service)
        assert service_provider.my_first_service is service

    def test_override__initialized_already(self) -> None:
        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service_provider = _ServiceProvider(services=UNIVERSE)
        with pytest.raises(ServiceInitializedError):
            _ServiceProvider.my_first_service.override(
                service_provider, Service(object())
            )


class TestAsynchronousServiceManager:
    async def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        service_provider = Cls(services=UNIVERSE)
        assert await service_provider.my_first_service is my_first_service_value

    async def test_get__with_factory(self) -> None:
        my_first_service_value = object()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                lambda _: my_first_service_value
            )

        service_provider = Cls(services=UNIVERSE)
        assert await service_provider.my_first_service is my_first_service_value

    async def test_get__with_life_cycle(self) -> None:
        my_first_service_value = LifeCycle()

        class Cls(ManagedLifeCycle, ServiceProvider):
            my_first_service = AsynchronousServiceManager(
                Service(my_first_service_value)
            )

        async with Cls(services=UNIVERSE) as service_provider:
            actual = await service_provider.my_first_service
            assert actual is my_first_service_value
            assert actual.bootstrapped


class TestSynchronousServiceManager:
    def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class Cls(ServiceProvider):
            my_first_service = SynchronousServiceManager(
                Service(my_first_service_value)
            )

        service_provider = Cls(services=UNIVERSE)
        assert service_provider.my_first_service is my_first_service_value

    def test_get__with_factory(self) -> None:
        my_first_service = object()

        class Cls(ServiceProvider):
            my_first_service = SynchronousServiceManager(lambda _: my_first_service)

        service_provider = Cls(services=UNIVERSE)
        assert service_provider.my_first_service is my_first_service


async def test_service__with_asynchronous_service() -> None:
    my_first_service = object()

    class Cls(ServiceProvider):
        @service
        async def my_first_service(self) -> object:
            return my_first_service

    assert await Cls(services=UNIVERSE).my_first_service is my_first_service


def test_service__with_synchronous_service() -> None:
    my_first_service = object()

    class Cls(ServiceProvider):
        @service
        def my_first_service(self) -> object:
            return my_first_service

    assert Cls(services=UNIVERSE).my_first_service is my_first_service
