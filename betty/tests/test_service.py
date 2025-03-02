from typing import Awaitable

import pytest
from typing_extensions import override

from betty.service import (
    ServiceProvider,
    Bootstrapped,
    ShutdownStack,
    Shutdownable,
    service,
    StaticService,
    ServiceFactory,
)


class TestBootstrapped:
    class _DummyBootstrapped(Bootstrapped):
        def set_bootstrapped(self, bootstrapped: bool) -> None:
            self._bootstrapped = bootstrapped

    async def test_assert_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        with pytest.raises(RuntimeError):
            sut.assert_bootstrapped()
        sut.set_bootstrapped(True)
        sut.assert_bootstrapped()

    async def test_assert_bootstrapped_should_error_if_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        with pytest.raises(RuntimeError), pytest.warns():
            sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped_should_error_if_bootstrapped(
        self,
    ) -> None:
        sut = self._DummyBootstrapped()
        sut.set_bootstrapped(True)
        with pytest.raises(RuntimeError), pytest.warns():
            sut.assert_not_bootstrapped()

    async def test_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        assert not sut.bootstrapped
        sut.set_bootstrapped(True)
        assert sut.bootstrapped


class TestShutdownStack:
    @pytest.mark.parametrize(
        "expected_wait",
        [
            True,
            False,
        ],
    )
    async def test_shutdown(self, expected_wait: bool) -> None:
        carrier = []

        async def _shutdown(*, wait: bool) -> None:
            nonlocal carrier
            carrier.append(wait)

        class _Shutdownable(Shutdownable):
            @override
            async def shutdown(self, *, wait: bool = True) -> None:
                nonlocal carrier
                carrier.append(wait)

        sut = ShutdownStack()
        sut.append(_shutdown)
        sut.append(_Shutdownable())
        await sut.shutdown(wait=expected_wait)
        assert carrier == [expected_wait, expected_wait]

    async def test_shutdown_without_callbacks_without_wait(self) -> None:
        sut = ShutdownStack()
        await sut.shutdown(wait=False)

    async def test_shutdown_without_callbacks_with_wait(self) -> None:
        sut = ShutdownStack()
        await sut.shutdown(wait=True)


class TestServiceProvider:
    async def test___aenter__(self) -> None:
        async with ServiceProvider() as sut:
            assert sut.bootstrapped

    async def test___aexit__(self) -> None:
        async with ServiceProvider() as sut:
            pass
        assert not sut.bootstrapped

    async def test___del__(self) -> None:
        sut = ServiceProvider()
        await sut.bootstrap()
        with pytest.warns():
            del sut

    async def test_bootstrap(self) -> None:
        sut = ServiceProvider()
        await sut.bootstrap()
        try:
            assert sut.bootstrapped
        finally:
            await sut.shutdown()

    async def test_shutdown(self) -> None:
        sut = ServiceProvider()
        await sut.bootstrap()
        await sut.shutdown()
        assert not sut.bootstrapped


class _AsynchronousServiceProvider(ServiceProvider):
    @service
    async def my_first_asynchronous_service(self) -> object:
        return object()


class _SynchronousServiceProvider(ServiceProvider):
    @service
    def my_first_synchronous_service(self) -> object:
        return object()


class _AsynchronousServiceProviderWithInit(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_asynchronous_service.override(self, service)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceProviderWithInit(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_synchronous_service.override(self, service)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _AsynchronousServiceProviderWithInitFactory(ServiceProvider):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_AsynchronousServiceProviderWithInitFactory", Awaitable[object]
        ],
    ):
        super().__init__()
        type(self).my_first_asynchronous_service.override_factory(self, service_factory)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceProviderWithInitFactory(ServiceProvider):
    def __init__(
        self,
        service_factory: ServiceFactory[
            "_SynchronousServiceProviderWithInitFactory", object
        ],
    ):
        super().__init__()
        type(self).my_first_synchronous_service.override_factory(self, service_factory)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class TestService:
    async def test_get_class_attr_with_asynchronous_method(self) -> None:
        _AsynchronousServiceProvider.my_first_asynchronous_service  # noqa: B018

    async def test_get_instance_attr_with_asynchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _AsynchronousServiceProvider() as service_provider:
            assert (
                await service_provider.my_first_asynchronous_service
                is await service_provider.my_first_asynchronous_service
            )

    async def test_get_instance_attr_with_asynchronous_method_without_bootstrapped(
        self,
    ) -> None:
        service_provider = _AsynchronousServiceProvider()
        with pytest.raises(RuntimeError):
            await service_provider.my_first_asynchronous_service

    async def test_get_instance_attr_with_asynchronous_method_with_init(
        self,
    ) -> None:
        service = object()
        async with _AsynchronousServiceProviderWithInit(service) as service_provider:
            assert await service_provider.my_first_asynchronous_service is service

    async def test_get_instance_attr_with_asynchronous_method_with_init_factory(
        self,
    ) -> None:
        service = object()

        async def _service_factory(
            _: _AsynchronousServiceProviderWithInitFactory,
        ) -> object:
            return service

        async with _AsynchronousServiceProviderWithInitFactory(
            _service_factory
        ) as service_provider:
            assert await service_provider.my_first_asynchronous_service is service

    async def test_get_class_attr_with_synchronous_method(self) -> None:
        _SynchronousServiceProvider.my_first_synchronous_service  # noqa: B018

    async def test_get_instance_attr_with_synchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _SynchronousServiceProvider() as service_provider:
            assert (
                service_provider.my_first_synchronous_service
                is service_provider.my_first_synchronous_service
            )

    async def test_get_instance_attr_with_synchronous_method_without_bootstrapped(
        self,
    ) -> None:
        service_provider = _SynchronousServiceProvider()
        with pytest.raises(RuntimeError):
            service_provider.my_first_synchronous_service  # noqa: B018

    async def test_get_instance_attr_with_synchronous_method_with_init(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithInit(service) as service_provider:
            assert service_provider.my_first_synchronous_service is service

    async def test_get_instance_attr_with_synchronous_method_with_init_factory(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithInitFactory(
            lambda _: service
        ) as service_provider:
            assert service_provider.my_first_synchronous_service is service


class TestStaticService:
    def test___call__(self) -> None:
        service = object()
        service_provider = ServiceProvider()
        sut = StaticService[ServiceProvider, object](service)
        assert sut(service_provider) is service
