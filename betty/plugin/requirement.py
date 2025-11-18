"""
Requirements for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

from typing_extensions import override

from betty.locale.localizable import AnyEnumeration, _
from betty.plugin import (
    ClassedPluginDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    HumanFacingPluginDefinition,
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
    UnmetPluginRequirement,
    resolve_id,
)
from betty.requirement import AllRequirements, HasRequirement

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from betty.app import App
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


class PluginRequirementRepository(
    PluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    A plugin repository that checks plugins' requirements.
    """

    def __init__(
        self,
        plugin: type[_PluginDefinitionT],
        plugins: Mapping[MachineName, tuple[_PluginDefinitionT, Requirement | None]],
        /,
    ):
        super().__init__(plugin)
        self._plugins = plugins

    @classmethod
    async def new(
        cls,
        upstream: PluginRepository[_PluginDefinitionT],
        service_level: ServiceLevel,
        /,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            upstream.plugin,
            {
                plugin.id: (plugin, await get_requirement(plugin, service_level))
                for plugin in upstream
            },
        )

    @override
    def get(self, plugin_id: MachineName) -> _PluginDefinitionT:
        try:
            plugin, requirement = self._plugins[plugin_id]
            if requirement and not requirement.is_met():
                raise UnmetPluginRequirement(plugin, requirement)
            return plugin
        except KeyError:
            raise PluginNotFound.new(plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        for plugin, requirement in self._plugins.values():
            if requirement and requirement.is_met():
                yield plugin
