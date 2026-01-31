"""
Requirements for services.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate, Generic

from typing_extensions import ParamSpec, TypedDict, TypeVar

from betty.asyncio import resolve_await
from betty.extension import Extension, ExtensionDefinition
from betty.importlib import fully_qualified_name
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.requirement import Requirement, UnmetRequirement

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.app import App
    from betty.project import Project
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_P = ParamSpec("_P")
_ExtensionT = TypeVar("_ExtensionT", bound=Extension, default=Extension)


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
        else:
            app = await App.requires(services, fully_qualified_name(f))
            if isinstance(app, Requirement):
                raise UnmetRequirement(app)
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

        project = await Project.requires(services, fully_qualified_name(f))
        if isinstance(project, Requirement):
            raise UnmetRequirement(project)
        return await resolve_await(f(*args, project=project, **kwargs))

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
            extension_cls = (await project.plugins(ExtensionDefinition))[
                resolve_id(extension_id)
            ].cls
            extension = await extension_cls.requires(project, fully_qualified_name(f))
            if isinstance(extension, Requirement):
                raise UnmetRequirement(extension)
            return await resolve_await(f(*args, extension=extension, **kwargs))

        return __require_extension

    return _require_extension
