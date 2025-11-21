"""
Requirements for plugins.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar

from betty.locale.localizable import AnyEnumeration, _
from betty.plugin.classed import ClassedPluginDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.error import PluginError
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.resolve import resolve_id
from betty.requirement import AllRequirements

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.app import App
    from betty.machine_name import MachineName
    from betty.requirement import Requirement

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
            dependency_requirement = await dependency.cls.requirement(app=app)
            if dependency_requirement is not None:
                dependency_requirements.append(dependency_requirement)
            dependencies.append(dependency)
    except RecursionError:
        raise CyclicDependencyError([dependent.id]) from None
    else:
        if not dependency_requirements:
            return None
        return AllRequirements.new(
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


class CyclicDependencyError(PluginError):
    """
    Raised when plugins define a cyclic dependency, e.g. two plugins depend on each other.
    """

    def __init__(self, plugin_ids: Iterable[MachineName], /):
        plugin_names = ", ".join(plugin_ids)
        super().__init__(
            f"The following plugins have cyclic dependencies: {plugin_names}"
        )
