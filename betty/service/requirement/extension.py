"""
Handle requirements on extensions.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate, Generic, ParamSpec

from typing_extensions import TypeVar

from betty.asyncio import resolve_await
from betty.extension import Extension, ExtensionDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.service.requirement import ServiceLevelKwargs, UnmetRequirement
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.project import Project

_T = TypeVar("_T")
_P = ParamSpec("_P")
_ExtensionT = TypeVar("_ExtensionT", bound=Extension, default=Extension)


class RequireExtensionKwargs(ServiceLevelKwargs, Generic[_ExtensionT]):
    """
    The keyword arguments for callables decorated with :py:func:`betty.service.requirement.extension.require_extension`.
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
