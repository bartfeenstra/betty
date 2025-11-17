"""
Requirements for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from betty.locale.localizable import AnyEnumeration, _
from betty.plugin import (
    ClassedPluginDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    HumanFacingPluginDefinition,
    PluginDefinition,
    PluginRepository,
    resolve_id,
)
from betty.plugin.static import StaticPluginRepository
from betty.requirement import AllRequirements, HasRequirement

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.app import App
    from betty.requirement import Requirement
    from betty.service_level import ServiceLevel

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_ClassedPluginDefinitionT = TypeVar(
    "_ClassedPluginDefinitionT", bound=ClassedPluginDefinition[Any]
)


async def new_dependencies_requirement(
    dependent: _ClassedPluginDefinitionT,
    plugins: Iterable[_ClassedPluginDefinitionT],
    *,
    app: App,
) -> Requirement | None:
    """
    Check a dependent's dependency requirements.
    """
    if not isinstance(dependent, DependentPluginDefinition):  # type: ignore[redundant-expr]
        return None
    plugins_by_id = {plugin.id: plugin for plugin in plugins}  # type: ignore[unreachable]
    try:
        dependency_requirements = []
        dependencies = []
        for dependency_identifier in dependent.depends_on:
            dependency = plugins_by_id[resolve_id(dependency_identifier)]
            dependency_requirement = await dependency.cls.requirement(app)
            if dependency_requirement is not None:
                dependency_requirements.append(dependency_requirement)
            dependencies.append(dependency)
    except RecursionError:
        raise CyclicDependencyError([dependent.id]) from None
    else:
        if not dependency_requirements:
            return None
        return AllRequirements(
            *dependency_requirements,
            summary=_(
                "{plugin_type_label} {plugin_label} depends on {dependency_labels}."
            ).format(
                plugin_type_label=dependent.type.label,
                plugin_label=dependent.label
                if isinstance(dependent, HumanFacingPluginDefinition)
                else dependent.id,
                dependency_labels=AnyEnumeration(
                    *(
                        dependency.label
                        if isinstance(dependency, HumanFacingPluginDefinition)
                        else dependency.id
                        for dependency in dependencies
                    ),
                ),
            ),
        )


async def get_requirement(
    plugin: PluginDefinition, service_level: ServiceLevel
) -> Requirement | None:
    """
    Get the requirement for the given plugin.
    """
    if isinstance(plugin, ClassedPluginDefinition) and issubclass(
        plugin.cls, HasRequirement
    ):
        return await plugin.cls.requirement(service_level)
    return None


async def new_requirement_met_plugin_repository(
    upstream: PluginRepository[_PluginDefinitionT], service_level: ServiceLevel, /
) -> PluginRepository[_PluginDefinitionT]:
    """
    Create a new plugin repository with only those plugins from the given repository whose requirements are met.
    """
    return StaticPluginRepository(
        upstream.plugin,
        *[
            plugin
            for plugin in upstream
            if (requirement := await get_requirement(plugin, service_level))
            and (requirement is None or requirement.is_met())  # type: ignore[redundant-expr]
        ],
    )
