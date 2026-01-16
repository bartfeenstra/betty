import pickle
from collections.abc import Awaitable
from typing import cast

import pytest
from typing_extensions import override

from betty.config import Configurable
from betty.service import (
    Bootstrapped,
    BootstrappedError,
    NotBootstrappedError,
    ServiceFactory,
    ServiceInitializedError,
    ServiceProvider,
    Shutdownable,
    ShutdownStack,
    StaticService,
    _AsynchronousServiceManager,
    _SynchronousServiceManager,
    service,
)
from betty.test_utils.config import DummyConfiguration


class TestBootstrapped:
    class _DummyBootstrapped(Bootstrapped):
        def set_bootstrapped(self, bootstrapped: bool) -> None:
            self._bootstrapped = bootstrapped

    async def test_assert_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        sut.set_bootstrapped(True)
        sut.assert_bootstrapped()

    async def test_assert_bootstrapped_should_error_if_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        with pytest.raises(NotBootstrappedError):
            sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped_should_error_if_bootstrapped(
        self,
    ) -> None:
        sut = self._DummyBootstrapped()
        sut.set_bootstrapped(True)
        with pytest.raises(BootstrappedError):
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


class _ServiceProviderWithSharedServices(ServiceProvider):
    def __init__(self):
        super().__init__()
        self.my_first_asynchronous_service_initialized = False
        self.my_first_synchronous_service_initialized = False

    @service(shared=True)
    async def my_first_asynchronous_service(self) -> object:
        self.my_first_asynchronous_service_initialized = True
        return object()

    @service(shared=True)
    def my_first_synchronous_service(self) -> object:
        self.my_first_synchronous_service_initialized = True
        return object()


class _ConfigurableServiceProvider(Configurable[DummyConfiguration], ServiceProvider):
    pass


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

    async def test_bootstrap__should_initialize_shared_services(self) -> None:
        sut = _ServiceProviderWithSharedServices()
        await sut.bootstrap()
        assert sut.my_first_asynchronous_service_initialized
        assert sut.my_first_synchronous_service_initialized
        await sut.shutdown()

    async def test_bootstrap__should_mark_configuration_immutable(self) -> None:
        async with _ConfigurableServiceProvider(
            configuration=DummyConfiguration()
        ) as sut:
            assert sut.configuration.is_immutable

    async def test_shutdown__should_mark_configuration_mutable(self) -> None:
        async with _ConfigurableServiceProvider(
            configuration=DummyConfiguration()
        ) as sut:
            pass
        assert sut.configuration.is_mutable

    async def test_shutdown(self) -> None:
        sut = ServiceProvider()
        await sut.bootstrap()
        await sut.shutdown()
        assert not sut.bootstrapped

    async def test___getstate____and___setstate__(self) -> None:
        async with ServiceProvider() as sut:
            unpickled_sut = cast(ServiceProvider, pickle.loads(pickle.dumps(sut)))
        await unpickled_sut.shutdown()

    async def test___getstate____not_bootstrapped_should_error(self) -> None:
        sut = ServiceProvider()
        with pytest.raises(NotBootstrappedError):
            pickle.dumps(sut)


class _AsynchronousServiceProvider(ServiceProvider):
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


class _AsynchronousServiceProviderWithOverride(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_asynchronous_service.override(self, service)

    @service
    async def my_first_asynchronous_service(self) -> object:
        raise NotImplementedError


class _SynchronousServiceProviderWithOverride(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        type(self).my_first_synchronous_service.override(self, service)

    @service
    def my_first_synchronous_service(self) -> object:
        raise NotImplementedError


class _AsynchronousServiceProviderWithOverrideFactory(ServiceProvider):
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


class _SynchronousServiceProviderWithOverrideFactory(ServiceProvider):
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


class _AsynchronousSharedServiceProvider(ServiceProvider):
    def __init__(self, service: object):
        super().__init__()
        self._init_service = service

    @service(shared=True)
    async def my_first_asynchronous_service(self) -> object:
        return self._init_service


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


class TestServiceManager:
    async def test_get__with_asynchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _AsynchronousServiceProvider(object()) as service_provider:
            assert await type(service_provider).my_first_asynchronous_service.get(
                service_provider
            ) is await type(service_provider).my_first_asynchronous_service.get(
                service_provider
            )

    async def test_get__with_asynchronous_method_without_bootstrapped(
        self,
    ) -> None:
        service_provider = _AsynchronousServiceProvider(object())
        with pytest.raises(NotBootstrappedError):
            await type(service_provider).my_first_asynchronous_service.get(
                service_provider
            )

    async def test_get__instance_attr_with_asynchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _AsynchronousServiceProviderWithOverride(
            service
        ) as service_provider:
            assert (
                await type(service_provider).my_first_asynchronous_service.get(
                    service_provider
                )
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
        ) as service_provider:
            assert (
                await type(service_provider).my_first_asynchronous_service.get(
                    service_provider
                )
                is service
            )

    async def test_get__instance_attr_with_synchronous_method_with_bootstrapped(
        self,
    ) -> None:
        async with _SynchronousServiceProvider(object()) as service_provider:
            assert type(service_provider).my_first_synchronous_service.get(
                service_provider
            ) is type(service_provider).my_first_synchronous_service.get(
                service_provider
            )

    async def test_get__instance_attr_with_synchronous_method_without_bootstrapped(
        self,
    ) -> None:
        service_provider = _SynchronousServiceProvider(object())
        with pytest.raises(NotBootstrappedError):
            type(service_provider).my_first_synchronous_service.get(service_provider)  # noqa: B018

    async def test_get__instance_attr_with_synchronous_method_with_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithOverride(service) as service_provider:
            assert (
                type(service_provider).my_first_synchronous_service.get(
                    service_provider
                )
                is service
            )

    async def test_get__instance_attr_with_synchronous_method_with_factory_override(
        self,
    ) -> None:
        service = object()
        async with _SynchronousServiceProviderWithOverrideFactory(
            lambda _: service
        ) as service_provider:
            assert (
                type(service_provider).my_first_synchronous_service.get(
                    service_provider
                )
                is service
            )

    async def test___get____with_class_attr(self) -> None:
        _AsynchronousServiceProvider.my_first_asynchronous_service  # noqa: B018

    async def test___get____with_instance_attr_with_asynchronous_method(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(service) as service_provider:
            assert await service_provider.my_first_asynchronous_service is service

    async def test___get____with_instance_attr_with_synchronous_method(self) -> None:
        service = object()
        async with _SynchronousServiceProvider(service) as service_provider:
            assert service_provider.my_first_synchronous_service is service

    async def test_get_state__not_bootstrapped_should_error(self) -> None:
        service_provider = _AsynchronousServiceProvider(object())
        with pytest.raises(NotBootstrappedError):
            type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )

    async def test_get_state__minimal(self) -> None:
        async with _AsynchronousServiceProvider(object()) as service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {}

    async def test_get_state__with_shared(self) -> None:
        service = object()
        async with _AsynchronousSharedServiceProvider(service) as service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {
                "_my_first_asynchronous_service": service,
            }

    async def test_get_state__with_shared_with_overridden(self) -> None:
        service = object()
        service_provider = _AsynchronousSharedServiceProvider(object())
        type(service_provider).my_first_asynchronous_service.override(
            service_provider,
            service,  # type: ignore[arg-type]
        )
        async with service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {
                "_my_first_asynchronous_service": service,
            }

    async def test_get_state__without_shared_with_overridden(self) -> None:
        service = object()
        service_provider = _AsynchronousServiceProvider(object())
        type(service_provider).my_first_asynchronous_service.override(
            service_provider, service
        )
        async with service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {
                "_my_first_asynchronous_service": service,
            }

    async def test_get_state__with_shared_with_overridden_factory(self) -> None:
        service = object()

        async def _factory(
            service_provider: _AsynchronousSharedServiceProvider,
        ) -> object:
            return service

        service_provider = _AsynchronousSharedServiceProvider(object())
        type(service_provider).my_first_asynchronous_service.override_factory(
            service_provider, _factory
        )
        async with service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {
                "_my_first_asynchronous_service": service,
            }

    async def test_get_state__without_shared_with_overridden_factory(self) -> None:
        async def _factory(service_provider: _AsynchronousServiceProvider) -> object:
            return object()

        service_provider = _AsynchronousServiceProvider(object())
        type(service_provider).my_first_asynchronous_service.override_factory(
            service_provider, _factory
        )
        async with service_provider:
            state = type(service_provider).my_first_asynchronous_service.get_state(
                service_provider
            )
            assert state == {
                "_my_first_asynchronous_service_factory_override": _factory,
            }

    async def test_is_shared(self) -> None:
        async with _AsynchronousSharedServiceProvider(object()) as service_provider:
            assert type(service_provider).my_first_asynchronous_service.is_shared

    async def test_override(self) -> None:
        service = object()
        async with _AsynchronousServiceProvider(object()) as service_provider:
            type(service_provider).my_first_asynchronous_service.override(
                service_provider, service
            )
            assert await service_provider.my_first_asynchronous_service is service

    async def test_override__with_override_with_initialized_already(self) -> None:
        async with _AsynchronousServiceProviderWithOverride(
            object()
        ) as service_provider:
            with pytest.raises(ServiceInitializedError):
                type(service_provider).my_first_asynchronous_service.override(
                    service_provider, object()
                )

    async def test_override_factory(self) -> None:
        service = object()

        async def _factory(
            service_provider: _AsynchronousServiceProvider,
        ) -> object:
            return service

        async with _AsynchronousServiceProvider(object()) as service_provider:
            type(service_provider).my_first_asynchronous_service.override_factory(
                service_provider, _factory
            )
            assert await service_provider.my_first_asynchronous_service is service

    async def test_override_factory__with_override_with_initialized_already(
        self,
    ) -> None:
        async def _factory(
            service_provider: _AsynchronousServiceProviderWithOverride,
        ) -> object:
            return object()

        async with _AsynchronousServiceProviderWithOverride(
            object()
        ) as service_provider:
            with pytest.raises(ServiceInitializedError):
                type(service_provider).my_first_asynchronous_service.override_factory(
                    service_provider, _factory
                )


class TestStaticService:
    def test___call__(self) -> None:
        service = object()
        service_provider = ServiceProvider()
        sut = StaticService[ServiceProvider, object](service)
        assert sut(service_provider) is service
