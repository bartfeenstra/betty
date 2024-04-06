from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from betty.service import (
    ServiceNotFound,
    ServiceContainer,
    CyclicDependency,
    ServiceContainerStarted,
    ServiceContainerNotStarted,
)
from betty.service._default import DefaultServiceContainerBuilder


class DummyService:
    pass


class DummyDependentService:
    def __init__(self, dependency: DummyService):
        pass


class DummyLeftHandCyclicDependencyService:
    def __init__(self, dependency: DummyRightHandCyclicDependencyService):
        pass


class DummyRightHandCyclicDependencyService:
    def __init__(self, dependency: DummyLeftHandCyclicDependencyService):
        pass


class TestDefaultServiceContainerBuilderAndDefaultServiceContainer:
    async def test_without_services(self) -> None:
        builder = DefaultServiceContainerBuilder[None]()
        builder.build()

    async def test_starting_a_started_container_should_error(self) -> None:
        builder = DefaultServiceContainerBuilder[None]()
        services = builder.build()
        async with services:
            with pytest.raises(ServiceContainerStarted):
                await services.start()

    async def test_stopping_a_not_started_container_should_error(self) -> None:
        builder = DefaultServiceContainerBuilder[None]()
        services = builder.build()
        with pytest.raises(ServiceContainerNotStarted):
            await services.stop()

    async def test_with_unknown_service(self) -> None:
        builder = DefaultServiceContainerBuilder[None]()
        async with builder.build() as services:
            with pytest.raises(ServiceNotFound):
                await services.get("UnknownServiceId")

    async def test_with_as_is_service(self) -> None:
        service_id = "MyFirstService"
        service = DummyService()
        builder = DefaultServiceContainerBuilder[None]()
        builder.define(service_id, service=service)
        async with builder.build() as services:
            assert await services.get(service_id) is service

    async def test_with_service_factory(self) -> None:
        service_id = "MyFirstService"
        service = DummyService()
        builder = DefaultServiceContainerBuilder[None]()
        setup = False
        teardown = False

        @asynccontextmanager
        async def _service_factory(
            _: ServiceContainer[None],
        ) -> AsyncIterator[DummyService]:
            nonlocal setup
            nonlocal teardown
            setup = True
            yield service
            teardown = True

        builder.define(service_id, service_factory=_service_factory)
        async with builder.build() as services:
            assert await services.get(service_id) is service
            assert setup
            assert not teardown
        assert teardown

    async def test_with_context(self) -> None:
        context = object()
        service_id = "MyFirstService"
        builder = DefaultServiceContainerBuilder[object](service_context=context)

        @asynccontextmanager
        async def _service_factory(
            services: ServiceContainer[object],
        ) -> AsyncIterator[None]:
            assert services.context is context
            yield

        builder.define(service_id, service_factory=_service_factory)
        async with builder.build() as services:
            await services.get(service_id)

    async def test_with_dependency(self) -> None:
        dependency_service_id = "MyFirstDependency"
        dependent_service_id = "MyFirstDependent"
        dependency = DummyService()

        @asynccontextmanager
        async def _new_dummy_dependent_service(
            services: ServiceContainer[None],
        ) -> AsyncIterator[DummyDependentService]:
            yield DummyDependentService(await services.get(dependency_service_id))

        builder = DefaultServiceContainerBuilder[None]()
        builder.define(dependency_service_id, service=dependency)
        builder.define(
            dependent_service_id, service_factory=_new_dummy_dependent_service
        )
        async with builder.build() as services:
            assert isinstance(
                await services.get(dependent_service_id), DummyDependentService
            )

    async def test_with_cyclic_dependency(self) -> None:
        left_hand_dependency_service_id = "MyFirstLeftHandDependency"
        right_hand_dependency_service_id = "MyFirstRightHandDependency"

        @asynccontextmanager
        async def _new_dummy_left_hand_dependency_service(
            services: ServiceContainer[None],
        ) -> AsyncIterator[DummyLeftHandCyclicDependencyService]:
            yield DummyLeftHandCyclicDependencyService(
                await services.get(right_hand_dependency_service_id)
            )

        @asynccontextmanager
        async def _new_dummy_right_hand_dependency_service(
            services: ServiceContainer[None],
        ) -> AsyncIterator[DummyRightHandCyclicDependencyService]:
            yield DummyRightHandCyclicDependencyService(
                await services.get(left_hand_dependency_service_id)
            )

        builder = DefaultServiceContainerBuilder[None]()
        builder.define(
            left_hand_dependency_service_id,
            service_factory=_new_dummy_left_hand_dependency_service,
        )
        builder.define(
            right_hand_dependency_service_id,
            service_factory=_new_dummy_right_hand_dependency_service,
        )
        async with builder.build() as services:
            with pytest.raises(CyclicDependency):
                await services.get(left_hand_dependency_service_id)
