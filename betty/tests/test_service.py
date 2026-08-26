from __future__ import annotations

from collections.abc import Callable
from typing import override

import pytest

from betty.classtools import ObjectAlreadyInitialized
from betty.functools import LazyReCallable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.prop import HasProps
from betty.service import Service, ServiceManager, ServiceManufacturer, new
from betty.service_level import HasServiceLevel, ResolvableServiceLevel, ServiceLevel


class _DummyServiceManager[OwnerT: ResolvableServiceLevel](
    ServiceManager[OwnerT, object, object, Callable[[], object]]
):
    @override
    def _init_manufacturer(
        self,
        owner: OwnerT,
        manufacturer: ServiceManufacturer[object, ServiceLevel, OwnerT],
        /,
    ) -> Callable[[], object]:
        return LazyReCallable(lambda: new(manufacturer, owner))

    @override
    def _resolve(self, resolver: Callable[[], object], /) -> object:
        return resolver()


class TestServiceManager:
    def test_get(self) -> None:
        service = object()

        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            @staticmethod
            def my_first_service() -> object:
                return service

        assert _Owner.my_first_service.get(_Owner(services=ServiceLevel())) is service

    async def test_post_init_owner__initialized_already(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            @staticmethod
            def my_first_service() -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        async with owner:
            with pytest.raises(ObjectAlreadyInitialized):
                _Owner.my_first_service.pre_init_owner(owner)

    async def test_set(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            def __init__(self, my_first_service: object, /):
                super().__init__(services=ServiceLevel())
                self.my_first_service = Service(my_first_service)

            @_DummyServiceManager
            @staticmethod
            def my_first_service() -> object:
                raise NotImplementedError

        service = object()
        owner = _Owner(service)
        async with owner:
            assert owner.my_first_service is service

    async def test_set__initialized_already(self) -> None:
        class _Owner(HasServiceLevel, ManagedLifeCycle, HasProps):
            @_DummyServiceManager
            @staticmethod
            def my_first_service() -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        async with owner:
            with pytest.raises(ObjectAlreadyInitialized):
                owner.my_first_service = Service(object())
