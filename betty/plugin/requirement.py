"""
Requirements for plugins.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, final

from typing_extensions import override

from betty.locale.localizable import AllEnumeration, _
from betty.plugin import PluginDefinition
from betty.plugin.classed import ClassedPluginDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.error import PluginError, PluginNotFound, UnmetRequirement
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.repository import PluginRepository
from betty.plugin.resolve import (
    ResolvableDefinition,
    ResolvableId,
    resolve_definition,
    resolve_id,
)
from betty.requirement import AllRequirements, HasRequirement

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from betty.machine_name import MachineName
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
    service_level: ServiceLevel,
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
            dependency_requirement = await dependency.cls.requirement(service_level)
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
                dependency_labels=AllEnumeration(
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


async def get_requirement(
    plugin: ResolvableDefinition, service_level: ServiceLevel
) -> Requirement | None:
    """
    Get the requirement for the given plugin.
    """
    plugin = resolve_definition(plugin)
    if isinstance(plugin, ClassedPluginDefinition) and issubclass(
        plugin.cls, HasRequirement
    ):
        return await plugin.cls.requirement(service_level)
    return None


@final
class CheckRequirementRepository(
    PluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    A plugin repository that checks plugins' requirements.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
        plugins_and_requirements: Iterable[
            tuple[_PluginDefinitionT, Requirement | None]
        ],
        /,
    ):
        super().__init__(plugin_type)
        self._plugins_and_requirements = {
            plugin.id: (plugin, requirement)
            for plugin, requirement in plugins_and_requirements
        }

    @classmethod
    async def new(
        cls,
        plugin_type: type[_PluginDefinitionT],
        plugins: Iterable[ResolvableDefinition[_PluginDefinitionT]],
        service_level: ServiceLevel,
        /,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            plugin_type,
            [
                (plugin, await get_requirement(plugin, service_level))  # type: ignore[misc]
                for plugin in list(map(resolve_definition, plugins))  # type: ignore[arg-type]
            ],
        )

    @override
    def get(self, plugin_id: ResolvableId[_PluginDefinitionT], /) -> _PluginDefinitionT:
        plugin_id = resolve_id(plugin_id)
        try:
            plugin, requirement = self._plugins_and_requirements[plugin_id]
            if requirement:
                raise UnmetRequirement(plugin, requirement)
            return plugin
        except KeyError:
            raise PluginNotFound(self.type.type, plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        for plugin, requirement in self._plugins_and_requirements.values():
            if not requirement:
                yield plugin
