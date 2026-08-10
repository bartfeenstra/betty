from __future__ import annotations

from collections.abc import Callable
from typing import override

import pytest

from betty.classtools import AlreadyInitialized
from betty.functools import LazyReCallable
from betty.service import HasServices, Service, ServiceManager
from betty.service_level import ServiceLevel


class _DummyServiceManager[OwnerT: HasServices](
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

        class _Owner(HasServices):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                return service

        assert _Owner.my_first_service.get(_Owner(services=ServiceLevel())) is service

    def test_pre_init_owner__initialized_already(self) -> None:
        class _Owner(HasServices):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        with pytest.raises(AlreadyInitialized):
            _Owner.my_first_service.pre_init_owner(owner)

    def test_override(self) -> None:
        class _Owner(HasServices):
            def __init__(self, my_first_service: object, /):
                type(self).my_first_service.override(self, Service(my_first_service))
                super().__init__(services=ServiceLevel())

            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        service = object()
        owner = _Owner(service)
        assert owner.my_first_service is service

    def test_override__initialized_already(self) -> None:
        class _Owner(HasServices):
            @_DummyServiceManager
            def my_first_service(self) -> object:
                raise NotImplementedError

        owner = _Owner(services=ServiceLevel())
        with pytest.raises(AlreadyInitialized):
            _Owner.my_first_service.override(owner, Service(object()))


class TestHasServices:
    def test___init__(self) -> None:
        class _Owner(HasServices):
            pass

        services = ServiceLevel()
        owner = _Owner(services=services)
        assert owner.services is services
