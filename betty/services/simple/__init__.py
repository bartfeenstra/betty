"""
Simple services.
"""

from __future__ import annotations

from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, overload

from betty.prop import HasProps
from betty.services.simple.asynchronous import AsynchronousServiceManager
from betty.services.simple.synchronous import SynchronousServiceManager

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.asyncio import ReAwaitable, ResolvableAwaitable
    from betty.service import ServiceManager


@overload
def service[OwnerT: HasProps, ServiceT](
    factory: Callable[[OwnerT], Awaitable[ServiceT]], /
) -> ServiceManager[
    OwnerT,
    ServiceT,
    ReAwaitable[ServiceT],
    ReAwaitable[ServiceT],
    ResolvableAwaitable[ServiceT],
]:
    pass


@overload
def service[OwnerT: HasProps, ServiceT](
    factory: Callable[[OwnerT], ServiceT], /
) -> ServiceManager[OwnerT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT]:
    pass


def service(factory):
    """
    Decorate a service factory method.

    The factory method is replaced with a :py:class:`service manager <betty.service.ServiceManager>` which
    lazily initializes the service when it is accessed.

    The decorated factory method should return a new service instance.
    """
    service_manager_cls = (
        AsynchronousServiceManager
        if iscoroutinefunction(factory)
        else SynchronousServiceManager
    )
    return update_wrapper(
        service_manager_cls(factory),  # ty:ignore[invalid-argument-type]
        factory,
    )
