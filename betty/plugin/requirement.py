"""
Requirements for plugins.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Self, cast, final

from typing_extensions import TypeVar, override

from betty.functools import unique
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import AllEnumeration
from betty.plugin import PluginDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.error import PluginError, PluginNotFound, UnmetRequirement
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.repository import PluginRepository
from betty.plugin.resolve import ResolvableDefinition, resolve_definition, resolve_id
from betty.requirement import AllRequirements, HasRequirement

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, MutableSequence

    from betty.machine_name import MachineName
    from betty.requirement import Requirement
    from betty.service.level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


async def new_dependencies_requirement(
    dependent: _PluginDefinitionT,
    plugins: Iterable[_PluginDefinitionT],
    *,
    services: ServiceLevel,
) -> Requirement | None:
    """
    Check a dependent's dependency requirements.
    """
    if not isinstance(dependent, DependentPluginDefinition):
        return None
    plugins_by_id = {plugin.id: plugin for plugin in plugins}
    try:
        dependencies: MutableSequence[tuple[_PluginDefinitionT, Requirement]] = []
        for dependency_identifier in dependent.depends_on:
            dependency = plugins_by_id[resolve_id(dependency_identifier)]
            if issubclass(dependency.cls, HasRequirement):
                dependency_requirement = await dependency.cls.requirement(services)
                if dependency_requirement is not None:
                    dependencies.append((dependency, dependency_requirement))
    except RecursionError:
        raise CyclicDependencyError([dependent.id]) from None
    else:
        if not dependencies:
            return None
        return AllRequirements.new(
            *unique(dependency[1] for dependency in dependencies),
            summary=_("{dependent} depends on {dependencies}.").format(
                dependent=dependent.reference_label_with_type,
                dependencies=AllEnumeration(
                    *(
                        dependency.label
                        if isinstance(dependency, HumanFacingPluginDefinition)  # type: ignore[redundant-expr]
                        else dependency[0].id
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
    plugin: ResolvableDefinition, services: ServiceLevel
) -> Requirement | None:
    """
    Get the requirement for the given plugin.
    """
    plugin = resolve_definition(plugin)
    if issubclass(plugin.cls, HasRequirement):
        return await plugin.cls.requirement(services)
    return None


@final
class CheckRequirementRepository(PluginRepository[_PluginDefinitionT]):
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
        services: ServiceLevel,
        /,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            plugin_type,
            [
                (plugin, await get_requirement(plugin, services))
                for plugin in cast(
                    list[_PluginDefinitionT],
                    list(
                        map(
                            resolve_definition,  # type: ignore[arg-type]
                            plugins,
                        )
                    ),
                )
            ],
        )

    @override
    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        try:
            plugin, requirement = self._plugins_and_requirements[plugin_id]
            if requirement:
                raise UnmetRequirement(plugin, requirement)
            return plugin
        except KeyError:
            raise PluginNotFound(self.type.type(), plugin_id, list(self)) from None

    @override
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        for plugin, requirement in self._plugins_and_requirements.values():
            if not requirement:
                yield plugin
