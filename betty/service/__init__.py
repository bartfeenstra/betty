"""
Provide application service management.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence, Iterable
from types import TracebackType
from typing import TypeAlias, Any, Self, overload, AsyncContextManager, Generic, TypeVar

ServiceContextT = TypeVar("ServiceContextT")
ServiceId: TypeAlias = str
Service: TypeAlias = Any


class CyclicDependency(RuntimeError):
    def __init__(self, service_ids: Sequence[ServiceId]):
        assert len(service_ids) > 1
        traceback = []
        for index, service_id in enumerate(service_ids):
            traceback_line = f'- "{service_id}"'
            if index == 0:
                traceback_line += " (requested service)"
            if index == len(service_ids) - 1:
                traceback_line += " (cyclic dependency)"
            traceback.append(traceback_line)
        traceback_str = "\n".join(traceback)
        super().__init__(
            f"""
Cyclic service dependency detected for "{service_ids[0]}":
{traceback_str}
"""
        )


class ServiceNotFound(RuntimeError):
    def __init__(
        self, unknown_service_id: ServiceId, known_service_ids: Iterable[ServiceId]
    ):
        message = f'Unknown service "{unknown_service_id}".'
        known_service_ids = sorted(known_service_ids)
        if known_service_ids:
            message += " Did you mean one of:\n"
            message += "\n".join(
                (
                    f"- {known_service_id}"
                    for known_service_id in sorted(known_service_ids)
                )
            )
        else:
            message += " There are no available services."
        super().__init__(message)


class ServiceContainerNotStarted(RuntimeError):
    def __init__(self):
        super().__init__("This service container has not yet started.")


class ServiceContainerStarted(RuntimeError):
    def __init__(self):
        super().__init__("This service container has already started.")


class ServiceContainer(Generic[ServiceContextT]):
    """
    Define a service container.

    A service container allows access to whatever services are defined, and manages their resources.

    Implementations must be thread-safe.
    """

    @property
    def context(self) -> ServiceContextT:
        raise NotImplementedError

    async def get(self, service_id: ServiceId) -> Service:
        raise NotImplementedError(type(self))

    async def start(self) -> None:
        raise NotImplementedError(type(self))

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def stop(self) -> None:
        raise NotImplementedError(type(self))

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()


ServiceFactory: TypeAlias = Callable[
    [ServiceContainer[ServiceContextT]], AsyncContextManager[Service]
]


class ServiceContainerBuilder(Generic[ServiceContextT]):
    """
    Define a service container builder.

    A service container builder allows you to define the services to build a service container with.
    """

    @overload
    def define(
        self, service_id: ServiceId, *, service_factory: ServiceFactory[ServiceContextT]
    ) -> None:
        pass

    @overload
    def define(self, service_id: ServiceId, *, service: Service) -> None:
        pass

    def define(
        self,
        service_id: ServiceId,
        *,
        service: Service | None = None,
        service_factory: ServiceFactory[ServiceContextT] | None = None,
    ) -> None:
        raise NotImplementedError(type(self))

    def build(self) -> ServiceContainer[ServiceContextT]:
        raise NotImplementedError(type(self))
