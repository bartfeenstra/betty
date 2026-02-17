"""
Handle requirements on extensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Concatenate, overload

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


@overload
def require_extension[ExtensionT: Extension](
    extension_id: type[ExtensionT] | ResolvableId[ExtensionDefinition], /
) -> Requirement[ExtensionT]:
    pass


@overload
def require_extension[ExtensionT: Extension, **P, ReturnT](
    extension_id: type[ExtensionT] | ResolvableId[ExtensionDefinition],
    f: Callable[Concatenate[ExtensionT, P], Awaitable[ReturnT] | ReturnT]
    | Callable[Concatenate[Any, ExtensionT, P], Awaitable[ReturnT] | ReturnT],
    /,
) -> CallableRequirement[ExtensionT, P, ReturnT]:
    pass


@overload
def require_extension[ExtensionT: Extension](
    extension_id: type[ExtensionT] | ResolvableId[ExtensionDefinition],
    services: ServiceLevel,
    /,
) -> Awaitable[ExtensionT]:
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
async def _require_extension[ExtensionT: Extension](
    project: Project,
    target: str,
    extension_id: type[ExtensionT] | ResolvableId[ExtensionDefinition],
) -> ExtensionT:
    extensions = await project.plugins.plugins(ExtensionDefinition)
    try:
        extension = extensions[resolve_id(extension_id)]
    except PluginNotFound as error:
        raise UnmetRequirement(error) from error
    project_extensions = await project.extensions
    if extension_id in project_extensions:
        return project_extensions[extension_id]  # ty:ignore[invalid-return-type]
    raise UnmetRequirement(
        _(
            "{target} requires the {extension} extension. Enable it in your project configuration, and try again."
        ).format(target=target, extension=extension.label)
    )
