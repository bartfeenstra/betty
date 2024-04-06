from collections import defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, Generic
from typing_extensions import override

from betty.concurrent import AsynchronizedLock, _Lock
from betty.service import (
    ServiceContainer,
    ServiceId,
    ServiceFactory,
    Service,
    ServiceNotFound,
    ServiceContainerBuilder,
    CyclicDependency,
    ServiceContainerNotStarted,
    ServiceContainerStarted,
    ServiceContextT,
)


class _ServiceContainerBase(
    ServiceContainer[ServiceContextT], Generic[ServiceContextT]
):
    def __init__(
        self,
        service_factories: Mapping[ServiceId, ServiceFactory[ServiceContextT]],
        entered_service_context_managers: MutableSequence[AsyncContextManager[Service]],
        services: MutableMapping[ServiceId, Any],
        locks: MutableMapping[ServiceId, _Lock],
        locks_lock: _Lock,
        *,
        service_context: ServiceContextT | None = None,
    ):
        self._service_factories = service_factories
        self._entered_service_context_managers = entered_service_context_managers
        self._services = services
        self._locks = locks
        self._locks_lock = locks_lock
        self._started = False
        self._context = service_context

    async def _lock(self, service_id: ServiceId) -> _Lock:
        async with self._locks_lock:
            return self._locks[service_id]

    def _assert_started(self) -> None:
        if not self._started:
            raise ServiceContainerNotStarted()

    def _assert_not_started(self) -> None:
        if self._started:
            raise ServiceContainerStarted()

    @override
    @property
    def context(self) -> ServiceContextT:
        return self._context  # type: ignore[return-value]

    async def start(self) -> None:
        self._assert_not_started()
        assert not self._started
        self._started = True

    async def stop(self) -> None:
        self._assert_started()

    @override
    async def get(self, service_id: ServiceId) -> Service:
        self._assert_started()
        async with await self._lock(service_id):
            try:
                return self._services[service_id]
            except KeyError:
                self._services[service_id] = await self._initialize(service_id)
        return self._services[service_id]

    async def _initialize(self, service_id: ServiceId) -> Service:
        raise NotImplementedError(type(self))


class DefaultServiceContainer(
    _ServiceContainerBase[ServiceContextT], Generic[ServiceContextT]
):
    def __init__(
        self,
        service_factories: Mapping[ServiceId, ServiceFactory[ServiceContextT]],
        *,
        service_context: ServiceContextT | None = None,
    ):
        super().__init__(
            service_factories,
            [],
            {},
            defaultdict(AsynchronizedLock.threading),
            AsynchronizedLock.threading(),
            service_context=service_context,
        )

    @override
    async def _initialize(self, service_id: ServiceId) -> Service:
        async with _ServiceInitializingServiceContainer(
            self._service_factories,
            self._entered_service_context_managers,
            self._services,
            self._locks,
            self._locks_lock,
            service_context=self._context,
        ) as services:
            return await services.initialize(service_id)

    async def stop(self) -> None:
        await super().stop()
        # @todo We should probably sort these topologically based on dependencies before exiting them
        for entered_service_context_manager in self._entered_service_context_managers:
            await entered_service_context_manager.__aexit__(None, None, None)


class _ServiceInitializingServiceContainer(
    _ServiceContainerBase[ServiceContextT], Generic[ServiceContextT]
):
    def __init__(
        self,
        service_factories: Mapping[ServiceId, ServiceFactory[ServiceContextT]],
        entered_service_context_managers: MutableSequence[AsyncContextManager[Service]],
        services: MutableMapping[ServiceId, Any],
        locks: MutableMapping[ServiceId, _Lock],
        locks_lock: _Lock,
        *,
        service_context: ServiceContextT | None = None,
    ):
        super().__init__(
            service_factories,
            entered_service_context_managers,
            services,
            locks,
            locks_lock,
            service_context=service_context,
        )
        self._seen: MutableSequence[ServiceId] = []

    @override
    async def get(self, service_id: ServiceId) -> Service:
        if service_id in self._seen:
            raise CyclicDependency((*self._seen, service_id))
        self._seen.append(service_id)
        return await super().get(service_id)

    @override
    async def _initialize(self, service_id: ServiceId) -> Service:
        try:
            service_factory = self._service_factories[service_id]
        except KeyError:
            raise ServiceNotFound(service_id, self._service_factories.keys())
        service_context = service_factory(self)
        service = await service_context.__aenter__()
        self._entered_service_context_managers.append(service_context)
        return service

    async def initialize(self, service_id: ServiceId) -> Service:
        self._seen.append(service_id)
        return await self._initialize(service_id)


class DefaultServiceContainerBuilder(
    ServiceContainerBuilder[ServiceContextT], Generic[ServiceContextT]
):
    def __init__(self, *, service_context: ServiceContextT | None = None):
        self._service_factories: MutableMapping[
            ServiceId, ServiceFactory[ServiceContextT]
        ] = {}
        self._context = service_context

    @override
    def define(
        self,
        service_id: ServiceId,
        *,
        service: Service | None = None,
        service_factory: ServiceFactory[ServiceContextT] | None = None,
    ) -> None:
        if service_factory is None:

            @asynccontextmanager
            async def service_factory(
                _: ServiceContainer[ServiceContextT],
            ) -> AsyncIterator[Service]:
                yield service

        assert service_factory is not None
        self._service_factories[service_id] = service_factory

    @override
    def build(self) -> ServiceContainer[ServiceContextT]:
        return DefaultServiceContainer(
            self._service_factories, service_context=self._context
        )
