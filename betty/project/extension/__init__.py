"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

from typing_extensions import override

from betty.config import Configuration, DefaultConfigurable
from betty.locale.localizable import Localizable, _, call
from betty.plugin import (
    CyclicDependencyError,
    DependentPlugin,
    OrderedPlugin,
    PluginIdToTypeMapping,
    PluginRepository,
    sort_dependent_plugin_graph,
    sort_ordered_plugin_graph,
)
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.project.factory import ProjectDependentFactory
from betty.requirement import AllRequirements
from betty.service import ServiceProvider
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from graphlib import TopologicalSorter
    from pathlib import Path

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.project import Project
    from betty.requirement import Requirement

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Extension(
    OrderedPlugin["Extension"],
    DependentPlugin["Extension"],
    ServiceProvider,
    ProjectDependentFactory,
):
    """
    Integrate optional functionality with Betty :py:class:`betty.project.Project`s.

    Read more about :doc:`/development/plugin/extension`.

    To test your own subclasses, use :py:class:`betty.test_utils.project.extension.ExtensionTestBase`.
    """

    def __init__(self, project: Project):
        assert type(self) is not Extension
        super().__init__()
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        """
        Register event handlers with the project.
        """

    @property
    def project(self) -> Project:
        """
        The project this extension runs within.
        """
        return self._project

    @classmethod
    async def requirement(cls) -> Requirement:
        """
        Define the requirement for this extension to be enabled.

        This defaults to the extension's dependencies.
        """
        return await Dependencies.new(cls)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        """
        Return the path on disk where the extension's assets are located.

        This may be anywhere in your Python package.
        """
        return None


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


EXTENSION_REPOSITORY: PluginRepository[Extension] = EntryPointPluginRepository(
    "betty.extension"
)
"""
The project extension plugin repository.

Read more about :doc:`/development/plugin/extension`.
"""


class Theme(Extension):
    """
    An extension that is a front-end theme.
    """


class ConfigurableExtension(
    DefaultConfigurable[_ConfigurationT], Extension, Generic[_ConfigurationT]
):
    """
    A configurable extension.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())


async def sort_extension_type_graph(
    sorter: TopologicalSorter[type[Extension]],
    extension_types: Iterable[type[Extension]],
) -> None:
    """
    Sort an extension graph.
    """
    await sort_ordered_plugin_graph(
        sorter,
        EXTENSION_REPOSITORY,
        await sort_dependent_plugin_graph(
            sorter, EXTENSION_REPOSITORY, extension_types
        ),
    )


class Dependencies(AllRequirements):
    """
    Check a dependent's dependency requirements.
    """

    @private
    def __init__(
        self,
        dependent: type[Extension],
        extension_id_to_type_mapping: PluginIdToTypeMapping[Extension],
        dependency_requirements: Sequence[Requirement],
    ):
        super().__init__(*dependency_requirements)
        self._dependent = dependent
        self._extension_id_to_type_mapping = extension_id_to_type_mapping

    @classmethod
    async def new(cls, dependent: type[Extension]) -> Self:
        """
        Create a new instance.
        """
        try:
            dependency_requirements = [
                await (
                    await EXTENSION_REPOSITORY.get(dependency_identifier)
                    if isinstance(dependency_identifier, str)
                    else dependency_identifier
                ).requirement()
                for dependency_identifier in dependent.depends_on()
            ]
        except RecursionError:
            raise CyclicDependencyError([dependent]) from None
        else:
            return cls(
                dependent, await EXTENSION_REPOSITORY.mapping(), dependency_requirements
            )

    @override
    def summary(self) -> Localizable:
        return _("{dependent_label} requires {dependency_labels}.").format(
            dependent_label=self._dependent.plugin_label(),
            dependency_labels=call(
                lambda localizer: ", ".join(
                    self._extension_id_to_type_mapping[dependency_identifier]
                    .plugin_label()
                    .localize(localizer)
                    for dependency_identifier in self._dependent.depends_on()
                ),
            ),
        )
