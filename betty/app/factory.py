"""
Functionality for creating new class instances that depend on apps.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, overload

from typing_extensions import TypeVar

from betty.app import App
from betty.asyncio import ensure_await
from betty.factory import FactoryError
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.requirement import Requirement
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


_T = TypeVar("_T")
_P = ParamSpec("_P")


@overload
def require_app(
    factory: Callable[Concatenate[App, _P], Awaitable[_T]],
    /,
) -> Callable[Concatenate[ServiceLevel, _P], Awaitable[_T]]:
    pass


@overload
def require_app(
    factory: Callable[Concatenate[App, _P], _T],
    /,
) -> Callable[Concatenate[ServiceLevel, _P], Awaitable[_T]]:
    pass


def require_app(factory, /):
    """
    Decorate a factory that requires an app to accept any service level.
    """

    @wraps(factory)
    async def _require_app(arg0: Any, arg1: Any = None) -> _T:
        # Compare the arguments to support functions, class methods, and instance methods.
        if isinstance(arg0, ServiceLevel):
            assert arg1 is None
            services = arg0
            args = []
        else:
            assert isinstance(arg1, ServiceLevel)
            services = arg1
            args = [arg0]
        services = await App.requires(services, repr(factory))
        if isinstance(services, Requirement):
            raise FactoryError(services.localize(DEFAULT_LOCALIZER))
        return await ensure_await(factory(*args, services))

    return _require_app
