"""
Handle requirements on applications.
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

    from betty.app import App
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_P = ParamSpec("_P")


class RequireAppKwargs(ServiceLevelKwargs):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.app.require_app`.
    """

    app: App


def require_app(
    f: Callable[Concatenate[RequireAppKwargs, _P], Awaitable[_T] | _T],
) -> Callable[Concatenate[ServiceLevelKwargs, _P], Awaitable[_T]]:
    """
    Decorate a service level callable to require an :py:class:`betty.app.App`.
    """

    @wraps(f)
    async def _require_app(
        *args: _P.args, services: ServiceLevel, **kwargs: _P.kwargs
    ) -> _T:
        from betty.app import App
        from betty.project import Project

        if isinstance(services, Project):
            app = services.app
        elif isinstance(services, App):
            app = services
        else:
            raise UnmetRequirement(
                _("{subject} requires a running app.").format(
                    subject=fully_qualified_name(f)
                )
            )
        return await resolve_await(f(*args, app=app, **kwargs))

    return _require_app
