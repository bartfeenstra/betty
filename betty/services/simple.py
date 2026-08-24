"""
Simple services.
"""

from __future__ import annotations

from functools import update_wrapper
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, overload

from betty.services.asynchronous import AsynchronousServiceManager
from betty.services.synchronous import SynchronousServiceManager

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from betty.asyncio import ReAwaitable
    from betty.service import ResolvableServiceLevelHasServices, ServiceManager


@overload
def service[OwnerT: ResolvableServiceLevelHasServices, ServiceT](
    manufacturer: Callable[[OwnerT], Coroutine[Any, Any, ServiceT]],
    /,
    *,
    sync: bool = False,
) -> ServiceManager[OwnerT, ServiceT, ReAwaitable[ServiceT], ReAwaitable[ServiceT]]:
    pass


@overload
def service[OwnerT: ResolvableServiceLevelHasServices, ServiceT](
    manufacturer: Callable[[OwnerT], ServiceT], /
) -> ServiceManager[OwnerT, ServiceT, ServiceT, Callable[[], ServiceT]]:
    pass


def service(manufacturer, sync=False):
    """
    Decorate a service manufacturer method.

    The manufacturer method is replaced with a :py:class:`service manager <betty.service.ServiceManager>` which
    lazily initializes the service when it is accessed.

    The decorated manufacturer method should return a new service instance.
    """
    service_manager_cls = (
        SynchronousServiceManager
        if sync or not iscoroutinefunction(manufacturer)
        else AsynchronousServiceManager
    )
    return update_wrapper(
        service_manager_cls(manufacturer),  # ty:ignore[invalid-argument-type]
        manufacturer,
    )
