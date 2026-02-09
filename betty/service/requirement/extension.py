"""
Handle requirements on extensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, overload

from typing_extensions import TypeVar

from betty.extension import Extension, ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.plugin import ResolvableId, resolve_id
from betty.plugin.error import PluginNotFound
from betty.service.requirement import CallableRequirement, Requirement, UnmetRequirement
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.project import Project
    from betty.service.level import ServiceLevel

_ReturnT = TypeVar("_ReturnT")
_P = ParamSpec("_P")
_ExtensionT = TypeVar("_ExtensionT", bound=Extension, default=Extension)


@overload
def require_extension(
    extension_id: type[_ExtensionT] | ResolvableId[ExtensionDefinition], /
) -> Requirement[_ExtensionT]:
    pass


@overload
def require_extension(
    extension_id: type[_ExtensionT] | ResolvableId[ExtensionDefinition],
    f: Callable[Concatenate[_ExtensionT, _P], Awaitable[_ReturnT] | _ReturnT]
    | Callable[Concatenate[Any, _ExtensionT, _P], Awaitable[_ReturnT] | _ReturnT],
    /,
) -> CallableRequirement[_ExtensionT, _P, _ReturnT]:
    pass


@overload
def require_extension(
    extension_id: type[_ExtensionT] | ResolvableId[ExtensionDefinition],
    services: ServiceLevel,
    /,
) -> Awaitable[_ExtensionT]:
    pass


def require_extension(extension_id, f=None):
    """
    Decorate a service level callable to require an :py:class:`betty.extension.Extension`.
    """
    requirement = Requirement(
        lambda services, target: _require_extension(services, target, extension_id)
    )
    if f is None:
        return requirement
    return requirement(f)


@require_project
async def _require_extension(
    project: Project,
    target: str,
    extension_id: type[_ExtensionT] | ResolvableId[ExtensionDefinition],
) -> _ExtensionT:
    extensions = project.plugin.plugins(ExtensionDefinition)
    try:
        extension = await extensions.plugin(resolve_id(extension_id))
    except PluginNotFound as error:
        raise UnmetRequirement(error) from error
    project_extensions = await project.extensions
    if extension_id in project_extensions:
        return project_extensions[extension_id]
    raise UnmetRequirement(
        _(
            "{target} requires the {extension} extension. Enable it in your project configuration, and try again."
        ).format(target=target, extension=extension.label)
    )
