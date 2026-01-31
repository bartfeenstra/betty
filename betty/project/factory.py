"""
Functionality for creating new class instances that depend on projects.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, overload

from typing_extensions import TypeVar

from betty.asyncio import resolve_await
from betty.factory import FactoryError
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.project import Project
from betty.requirement import Requirement
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


_T = TypeVar("_T")
_P = ParamSpec("_P")


@overload
def require_project(
    factory: Callable[Concatenate[Project, _P], Awaitable[_T]],
    /,
) -> Callable[Concatenate[ServiceLevel, _P], Awaitable[_T]]:
    pass


@overload
def require_project(
    factory: Callable[Concatenate[Project, _P], _T],
    /,
) -> Callable[Concatenate[ServiceLevel, _P], Awaitable[_T]]:
    pass


def require_project(factory, /):
    """
    Decorate a factory that requires a project to accept any service level.
    """

    @wraps(factory)
    async def _require_project(arg0: Any, arg1: Any = None) -> _T:
        # Compare the arguments to support functions, class methods, and instance methods.
        if isinstance(arg0, ServiceLevel):
            assert arg1 is None
            services = arg0
            args = []
        else:
            assert isinstance(arg1, ServiceLevel)
            services = arg1
            args = [arg0]
        services = await Project.requires(services, repr(factory))
        if isinstance(services, Requirement):
            raise FactoryError(services.localize(DEFAULT_LOCALIZER))
        return await resolve_await(factory(*args, services))

    return _require_project
