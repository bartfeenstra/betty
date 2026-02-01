"""
Handle requirements on projects.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar

from betty.asyncio import resolve_await
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.service.requirement import ServiceLevelKwargs, UnmetRequirement

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.project import Project
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_P = ParamSpec("_P")


class RequireProjectKwargs(ServiceLevelKwargs):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.project.require_project`.
    """

    project: Project


def require_project(
    f: Callable[Concatenate[RequireProjectKwargs, _P], Awaitable[_T] | _T],
) -> Callable[Concatenate[ServiceLevelKwargs, _P], Awaitable[_T]]:
    """
    Decorate a service level callable to require an :py:class:`betty.project.Project`.
    """

    @wraps(f)
    async def _require_project(
        *args: _P.args, services: ServiceLevel, **kwargs: _P.kwargs
    ) -> _T:
        from betty.project import Project

        if isinstance(services, Project):
            return await resolve_await(f(*args, project=services, **kwargs))
        raise UnmetRequirement(
            _("{subject} requires a project.").format(subject=fully_qualified_name(f))
        )

    return _require_project
