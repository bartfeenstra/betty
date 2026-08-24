from __future__ import annotations

from collections.abc import Callable
from typing import override

import pytest

from betty.classtools import AlreadyInitialized
from betty.functools import LazyReCallable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service import Service, ServiceManager
from betty.service_level import HasServiceLevel, ResolvableServiceLevel, ServiceLevel


class _DummyServiceManager[OwnerT: ResolvableServiceLevel](
    ServiceManager[OwnerT, object, object, Callable[[], object], object]
):
    @override
    def _new_service_getter(self, owner: OwnerT, /) -> Callable[[], object]:
        def _factory() -> object:
            factory = self._get_service_or_factory(owner)
            if isinstance(factory, Service):
                return factory.service
            return factory(owner)

        return LazyReCallable(_factory)

    @override
    def _get_service(self, service: Callable[[], object], /) -> object:
        return service()


class TestServiceManager:
    def test_get(self) -> None:
        service = object()

        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                return service

        assert _Owner.my_first_service.get(_Owner(services=ServiceLevel())) is service

    async def test_pre_init_owner__initialized_already(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        async with owner:
            with pytest.raises(AlreadyInitialized):
                _Owner.my_first_service.pre_init_owner(owner)

    async def test_override(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            def __init__(self, my_first_service: object, /):
                super().__init__(services=ServiceLevel())
                type(self).my_first_service.override(self, Service(my_first_service))

            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service = object()
        owner = _Owner(service)
        async with owner:
            assert owner.my_first_service is service

    async def test_override__initialized_already(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        async with owner:
            with pytest.raises(AlreadyInitialized):
                _Owner.my_first_service.override(owner, Service(object()))
