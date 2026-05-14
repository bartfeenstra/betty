from __future__ import annotations

from collections.abc import Callable
from typing import override

import pytest

from betty.functools import LazyReCallable
from betty.service import (
    Service,
    ServiceAlreadyInitialized,
    ServiceManager,
    ServiceProvider,
)
from betty.service_level import ServiceLevel


class _DummyServiceManager[ServiceProviderT: ServiceProvider](
    ServiceManager[ServiceProviderT, object, object, Callable[[], object], object]
):
    @override
    def _new_service_getter(
        self, service_provider: ServiceProviderT, /
    ) -> Callable[[], object]:
        def _factory() -> object:
            factory = self._get_service_or_factory(service_provider)
            if isinstance(factory, Service):
                return factory.service
            return factory(service_provider)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], object], /) -> object:
        return service()


class TestServiceManager:
    def test_get(self) -> None:
        service = object()

        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                return service

        assert (
            _ServiceProvider.my_first_service.get(
                _ServiceProvider(services=ServiceLevel())
            )
            is service
        )

    def test_init_property_owner__initialized_already(self) -> None:
        class _ServiceProvider(ServiceProvider):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service_provider = _ServiceProvider(services=ServiceLevel())
        with pytest.raises(ServiceAlreadyInitialized):
            _ServiceProvider.my_first_service.init_property_owner(service_provider)

    def test_override(self) -> None:
        class _ServiceProvider(ServiceProvider):
            def __init__(self, my_first_service: object, /):
                type(self).my_first_service.override(self, Service(my_first_service))
                super().__init__(services=ServiceLevel())

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

        service_provider = _ServiceProvider(services=ServiceLevel())
        with pytest.raises(ServiceAlreadyInitialized):
            _ServiceProvider.my_first_service.override(
                service_provider, Service(object())
            )


class TestServiceProvider:
    def test_services(self) -> None:
        services = ServiceLevel()
        sut = ServiceProvider(services=services)
        assert sut.services is services
