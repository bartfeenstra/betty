"""Provide Betty's extension API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Any,
    TypeVar,
    Iterable,
    TYPE_CHECKING,
    Generic,
    Iterator,
    final,
)

from typing_extensions import override

from betty.asyncio import gather, wait_to_thread
from betty.config import Configurable, Configuration
from betty.dispatch import Dispatcher, TargetedDispatcher
from betty.plugin import Plugin, PluginId, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
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


class Extension(Plugin):
    """
    Integrate optional functionality with the Betty app.
    """

    def __init__(self, project: Project, *args: Any, **kwargs: Any):
        assert type(self) is not Extension
        super().__init__(*args, **kwargs)
        self._project = project

    @property
    def project(self) -> Project:
        """
        The project this extension runs within.
        """
        return self._project

    @classmethod
    def depends_on(cls) -> set[PluginId]:
        """
        The extensions this one depends on, and comes after.
        """
        return set()

    @classmethod
    def comes_after(cls) -> set[PluginId]:
        """
        The extensions that this one comes after.

        The other extensions may or may not be enabled.
        """
        return set()

    @classmethod
    def comes_before(cls) -> set[PluginId]:
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

    def __init__(
        self, *args: Any, configuration: _ConfigurationT | None = None, **kwargs: Any
    ):
        assert type(self) is not ConfigurableExtension
        super().__init__(*args, **kwargs)
        self._configuration = configuration or self.default_configuration()

    @classmethod
    @abstractmethod
    def default_configuration(cls) -> _ConfigurationT:
        """
        Get this extension's default configuration.
        """
        pass


class Extensions(ABC):
    """
    Manage available extensions.
    """

    @abstractmethod
    def __getitem__(self, extension_id: PluginId) -> Extension:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Iterator[Extension]]:
        """
        Iterate over all extensions, in topologically sorted batches.

        Each item is a batch of extensions. Items are ordered because later items depend
        on earlier items. The extensions in each item do not depend on each other and their
        order has no meaning. However, implementations SHOULD sort the extensions in each
        item in a stable fashion for reproducability.
        """
        pass

    @abstractmethod
    def flatten(self) -> Iterator[Extension]:
        """
        Get a sequence of topologically sorted extensions.
        """
        pass

    @abstractmethod
    def __contains__(self, extension_id: PluginId) -> bool:
        pass


@final
class ListExtensions(Extensions):
    """
    Manage available extensions, backed by a list.
    """

    def __init__(self, extensions: list[list[Extension]]):
        super().__init__()
        self._extensions = extensions

    @override
    def __getitem__(self, extension_id: PluginId) -> Extension:
        extension_type = wait_to_thread(EXTENSION_REPOSITORY.get(extension_id))
        for extension in self.flatten():
            if type(extension) is extension_type:
                return extension
        raise KeyError(f'Unknown extension of type "{extension_type}"')

    @override
    def __iter__(self) -> Iterator[Iterator[Extension]]:
        # Use a generator so we discourage calling code from storing the result.
        for batch in self._extensions:
            yield (extension for extension in batch)

    @override
    def flatten(self) -> Iterator[Extension]:
        for batch in self:
            yield from batch

    @override
    def __contains__(self, extension_id: PluginId) -> bool:
        try:
            self[extension_id]
        except KeyError:
            return False
        else:
            return True


@final
class ExtensionDispatcher(Dispatcher):
    """
    Dispatch events to extensions.
    """

    def __init__(self, extensions: Extensions):
        self._extensions = extensions

    @override
    def dispatch(self, target_type: type[Any]) -> TargetedDispatcher:
        target_method_names = [
            method_name
            for method_name in dir(target_type)
            if not method_name.startswith("_")
        ]
        if len(target_method_names) != 1:
            raise ValueError(
                f"A dispatch's target type must have a single method to dispatch to, but {target_type} has {len(target_method_names)}."
            )
        target_method_name = target_method_names[0]

        async def _dispatch(*args: Any, **kwargs: Any) -> list[Any]:
            return [
                result
                for target_extension_batch in self._extensions
                for result in await gather(
                    *(
                        getattr(target_extension, target_method_name)(*args, **kwargs)
                        for target_extension in target_extension_batch
                        if isinstance(target_extension, target_type)
                    )
                )
            ]

        return _dispatch


ExtensionTypeGraph = dict[type[Extension], set[type[Extension]]]


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
        for before_id in extension_type.comes_before():
            before = await EXTENSION_REPOSITORY.get(before_id)
            if before in extension_types_graph:
                extension_types_graph[before].add(extension_type)
        for after_id in extension_type.comes_after():
            after = await EXTENSION_REPOSITORY.get(after_id)
            if after in extension_types_graph:
                extension_types_graph[extension_type].add(after)

    return extension_types_graph


async def _extend_extension_type_graph(
    graph: ExtensionTypeGraph, extension_type: type[Extension]
) -> None:
    dependencies = [
        await EXTENSION_REPOSITORY.get(dependency_id)
        for dependency_id in extension_type.depends_on()
    ]
    # Ensure each extension type appears in the graph, even if they're isolated.
    graph.setdefault(extension_type, set())
    for dependency in dependencies:
        seen_dependency = dependency in graph
        graph[extension_type].add(dependency)
        if not seen_dependency:
            await _extend_extension_type_graph(graph, dependency)
