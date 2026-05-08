"""
Simple services.
"""

from __future__ import annotations

from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, overload

from betty.service import ServiceManager, ServiceProvider
from betty.service.simple.asynchronous import AsynchronousServiceManager
from betty.service.simple.synchronous import SynchronousServiceManager

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.asyncio import ReAwaitable, ResolvableAwaitable


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], Awaitable[ServiceT]], /
) -> ServiceManager[
    ServiceProviderT,
    ServiceT,
    ReAwaitable[ServiceT],
    ReAwaitable[ServiceT],
    ResolvableAwaitable[ServiceT],
]:
    pass


@overload
def service[ServiceProviderT: ServiceProvider, ServiceT](
    factory: Callable[[ServiceProviderT], ServiceT], /
) -> ServiceManager[
    ServiceProviderT, ServiceT, ServiceT, Callable[[], ServiceT], ServiceT
]:
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
    return update_wrapper(service_manager_cls(factory), factory)
