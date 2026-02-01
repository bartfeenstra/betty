"""
Requirements for services.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate, Generic, final

from typing_extensions import ParamSpec, TypedDict, TypeVar

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.app import App
    from betty.project import Project
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_P = ParamSpec("_P")
_ExtensionT = TypeVar("_ExtensionT", bound=Extension, default=Extension)


@final
class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """


class ServiceLevelKwargs(TypedDict):
    """
    The keyword arguments for service-level-dependent callables.
    """

    services: ServiceLevel


class RequireAppKwargs(ServiceLevelKwargs):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.require_app`.
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


class RequireProjectKwargs(ServiceLevelKwargs):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.require_project`.
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


class RequireExtensionKwargs(ServiceLevelKwargs, Generic[_ExtensionT]):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.require_extension`.
    """

    extension: _ExtensionT


def require_extension(
    extension_id: ResolvableId[ExtensionDefinition], /
) -> Callable[
    [Callable[Concatenate[RequireExtensionKwargs, _P], Awaitable[_T] | _T]],
    Callable[Concatenate[ServiceLevelKwargs, _P], Awaitable[_T]],
]:
    """
    Decorate a service level callable to require an :py:class:`betty.extension.Extension`.
    """

    def _require_extension(
        f: Callable[Concatenate[RequireExtensionKwargs, _P], Awaitable[_T] | _T],
    ) -> Callable[Concatenate[ServiceLevelKwargs, _P], Awaitable[_T]]:
        @require_project
        @wraps(f)
        async def __require_extension(
            *args: _P.args, project: Project, **kwargs: _P.kwargs
        ) -> _T:
            extension = (await project.plugins(ExtensionDefinition))[
                resolve_id(extension_id)
            ]
            extensions = await project.extensions
            if extension_id not in extensions:
                raise UnmetRequirement(
                    _(
                        "{subject} requires the {extension} extension. Enable it in your project configuration, and try again."
                    ).format(subject=fully_qualified_name(f), extension=extension.label)
                )
            return await resolve_await(
                f(*args, extension=extensions[extension], **kwargs)
            )

        return __require_extension

    return _require_extension
