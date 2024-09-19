"""Provide Betty's extension API."""

from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from collections.abc import MutableMapping
from typing import (
    TypeVar,
    Iterable,
    TYPE_CHECKING,
    Generic,
    Self,
)

from typing_extensions import override

from betty.config import Configurable, Configuration
from betty.core import CoreComponent
from betty.plugin import Plugin, PluginRepository, PluginIdentifier
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.project.factory import ProjectDependentFactory

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.requirement import Requirement
    from betty.project import Project
    from pathlib import Path

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ExtensionError(BaseException):
    """
    A generic extension API error.
    """

    pass  # pragma: no cover


class CyclicDependencyError(ExtensionError, RuntimeError):
    """
    Raised when extensions define a cyclic dependency, e.g. two extensions depend on each other.
    """

    def __init__(self, extension_types: Iterable[type[Extension]]):
        extension_names = ", ".join(
            [extension.plugin_id() for extension in extension_types]
        )
        super().__init__(
            f"The following extensions have cyclic dependencies: {extension_names}"
        )


class Extension(Plugin, CoreComponent, ProjectDependentFactory):
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
    async def new(cls, project: Project) -> Self:
        return cls(project)

    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        """
        Register event handlers with the project.
        """
        pass

    @property
    def project(self) -> Project:
        """
        The project this extension runs within.
        """
        return self._project

    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        """
        The extensions this one depends on, and comes after.
        """
        return set()

    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        """
        The extensions that this one comes after.

        The other extensions may or may not be enabled.
        """
        return set()

    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
        """
        The extensions that this one comes before.

        The other extensions may or may not be enabled.
        """
        return set()

    @classmethod
    def enable_requirement(cls) -> Requirement:
        """
        Define the requirement for this extension to be enabled.

        This defaults to the extension's dependencies.
        """
        from betty.project.extension.requirement import Dependencies

        return Dependencies(cls)

    def disable_requirement(self) -> Requirement:
        """
        Define the requirement for this extension to be disabled.

        This defaults to the extension's dependents.
        """
        from betty.project.extension.requirement import Dependents

        return Dependents(self)

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

    pass  # pragma: no cover


class ConfigurableExtension(
    Extension, Generic[_ConfigurationT], Configurable[_ConfigurationT]
):
    """
    A configurable extension.
    """

    def __init__(self, project: Project):
        super().__init__(project)
        self._configuration = self.default_configuration()

    @classmethod
    @abstractmethod
    def default_configuration(cls) -> _ConfigurationT:
        """
        Get this extension's default configuration.
        """
        pass


ExtensionTypeGraph = MutableMapping[type[Extension], set[type[Extension]]]


async def build_extension_type_graph(
    extension_types: Iterable[type[Extension]],
) -> ExtensionTypeGraph:
    """
    Build a dependency graph of the given extension types.
    """
    extension_types_graph: ExtensionTypeGraph = defaultdict(set)
    # Add dependencies to the extension graph.
    for extension_type in extension_types:
        await _extend_extension_type_graph(extension_types_graph, extension_type)
    # Now all dependencies have been collected, extend the graph with optional extension orders.
    for extension_type in extension_types:
        for before_identifier in extension_type.comes_before():
            before = (
                await EXTENSION_REPOSITORY.get(before_identifier)
                if isinstance(before_identifier, str)
                else before_identifier
            )
            if before in extension_types_graph:
                extension_types_graph[before].add(extension_type)
        for after_identifier in extension_type.comes_after():
            after = (
                await EXTENSION_REPOSITORY.get(after_identifier)
                if isinstance(after_identifier, str)
                else after_identifier
            )
            if after in extension_types_graph:
                extension_types_graph[extension_type].add(after)

    return extension_types_graph


async def _extend_extension_type_graph(
    graph: ExtensionTypeGraph, extension_type: type[Extension]
) -> None:
    dependencies = [
        await EXTENSION_REPOSITORY.get(dependency_identifier)
        if isinstance(dependency_identifier, str)
        else dependency_identifier
        for dependency_identifier in extension_type.depends_on()
    ]
    # Ensure each extension type appears in the graph, even if they're isolated.
    graph.setdefault(extension_type, set())
    for dependency in dependencies:
        seen_dependency = dependency in graph
        graph[extension_type].add(dependency)
        if not seen_dependency:
            await _extend_extension_type_graph(graph, dependency)
