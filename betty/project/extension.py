"""Provide Betty's extension API."""

from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from collections import defaultdict
from importlib.metadata import entry_points, EntryPoint
from typing import (
    Any,
    TypeVar,
    Iterable,
    TYPE_CHECKING,
    Generic,
    Iterator,
    Sequence,
    Self,
    final,
)

from typing_extensions import override

from betty.asyncio import gather
from betty.config import Configurable, Configuration
from betty.dispatch import Dispatcher, TargetedDispatcher
from betty.importlib import import_any
from betty.locale.localizable import _, Localizable, call, plain
from betty.requirement import Requirement, AllRequirements

if TYPE_CHECKING:
    from betty.project import Project
    from pathlib import Path

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ExtensionError(BaseException):
    """
    A generic extension API error.
    """

    pass  # pragma: no cover


class ExtensionTypeError(ExtensionError, ValueError):
    """
    A generic error regarding an extension type.
    """

    pass  # pragma: no cover


class ExtensionTypeImportError(ExtensionTypeError, ImportError):
    """
    Raised when an alleged extension type cannot be imported.
    """

    def __init__(self, extension_type_name: str):
        super().__init__(
            f'Cannot find and import an extension with name "{extension_type_name}".'
        )


class ExtensionTypeInvalidError(ExtensionTypeError, ImportError):
    """
    Raised for types that are not valid extension types.
    """

    def __init__(self, extension_type: type):
        super().__init__(
            f"{extension_type.__module__}.{extension_type.__name__} is not an extension type class. Extension types must extend {Extension.__module__}.{Extension.__name__}."
        )


class CyclicDependencyError(ExtensionError, RuntimeError):
    """
    Raised when extensions define a cyclic dependency, e.g. two extensions depend on each other.
    """

    def __init__(self, extension_types: Iterable[type[Extension]]):
        extension_names = ", ".join([extension.name() for extension in extension_types])
        super().__init__(
            f"The following extensions have cyclic dependencies: {extension_names}"
        )


@final
class Dependencies(AllRequirements):
    """
    Check a dependent's dependency requirements.
    """

    def __init__(self, dependent_type: type[Extension]):
        dependency_requirements = []
        for dependency_type in dependent_type.depends_on():
            try:
                dependency_requirement = dependency_type.enable_requirement()
            except RecursionError:
                raise CyclicDependencyError([dependency_type]) from None
            else:
                dependency_requirements.append(dependency_requirement)
        super().__init__(*dependency_requirements)
        self._dependent_type = dependent_type

    @classmethod
    def for_dependent(cls, dependent_type: type[Extension]) -> Self:
        """
        Create a new requirement for the given dependent.
        """
        return cls(dependent_type)

    @override
    async def summary(self) -> Localizable:
        return _("{dependent_label} requires {dependency_labels}.").format(
            dependent_label=format_extension_type(self._dependent_type),
            dependency_labels=call(
                lambda localizer: ", ".join(
                    (
                        format_extension_type(extension_type).localize(localizer)
                        for extension_type in self._dependent_type.depends_on()
                    ),
                ),
            ),
        )


@final
class Dependents(Requirement):
    """
    Check a dependency's dependent requirements.
    """

    def __init__(self, dependency: Extension, dependents: Sequence[Extension]):
        super().__init__()
        self._dependency = dependency
        self._dependents = dependents

    @override
    async def summary(self) -> Localizable:
        return _("{dependency_label} is required by {dependency_labels}.").format(
            dependency_label=format_extension_type(type(self._dependency)),
            dependent_labels=call(
                lambda localizer: ", ".join(
                    [
                        format_extension_type(type(dependent)).localize(localizer)
                        for dependent in self._dependents
                    ]
                )
            ),
        )

    @override
    async def is_met(self) -> bool:
        # This class is never instantiated unless there is at least one enabled dependent, which means this requirement
        # is always met.
        return True

    @classmethod
    def for_dependency(cls, dependency: Extension) -> Self:
        """
        Create a new requirement for the given dependency.
        """
        dependents = [
            dependency.project.extensions[extension_type]
            for extension_type in discover_extension_types()
            if dependency.__class__ in extension_type.depends_on()
            and extension_type in dependency.project.extensions
        ]
        return cls(dependency, dependents)


class Extension(ABC):  # noqa B024
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
    def name(cls) -> str:
        """
        The machine name.
        """
        return "%s.%s" % (cls.__module__, cls.__name__)

    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        """
        The extensions this one depends on, and comes after.
        """
        return set()

    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        """
        The extensions that this one comes after.

        The other extensions may or may not be enabled.
        """
        return set()

    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
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
        return Dependencies.for_dependent(cls)

    def disable_requirement(self) -> Requirement:
        """
        Define the requirement for this extension to be disabled.

        This defaults to the extension's dependents.
        """
        return Dependents.for_dependency(self)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        """
        Return the path on disk where the extension's assets are located.

        This may be anywhere in your Python package.
        """
        return None


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


class UserFacingExtension(Extension):
    """
    A sentinel to mark an extension as being visible to users (e.g. not internal).
    """

    @classmethod
    @abstractmethod
    def label(cls) -> Localizable:
        """
        Get the human-readable extension label.
        """
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> Localizable:
        """
        Get the human-readable extension description.
        """
        pass


class Theme(UserFacingExtension):
    """
    An extension that is a front-end theme.
    """

    pass  # pragma: no cover


@functools.singledispatch
def get_extension_type(
    extension_type_definition: str | type[Extension] | Extension,
) -> type[Extension]:
    """
    Get the extension type for an extension, extension type, or extension type name.
    """
    raise ExtensionTypeError(
        f'Cannot get the extension type for "{extension_type_definition}".'
    )


@get_extension_type.register(str)
def get_extension_type_by_name(extension_type_name: str) -> type[Extension]:
    """
    Get the extension type for an extension type name.
    """
    try:
        extension_type = import_any(extension_type_name)
    except ImportError:
        raise ExtensionTypeImportError(extension_type_name) from None
    return get_extension_type(extension_type)


@get_extension_type.register(type)
def get_extension_type_by_type(extension_type: type) -> type[Extension]:
    """
    Get the extension type for an extension type.
    """
    if issubclass(extension_type, Extension):
        return extension_type
    raise ExtensionTypeInvalidError(extension_type)


@get_extension_type.register(Extension)
def get_extension_type_by_extension(extension: Extension) -> type[Extension]:
    """
    Get the extension type for an extension.
    """
    return get_extension_type(type(extension))


def format_extension_type(extension_type: type[Extension]) -> Localizable:
    """
    Format an extension type to a human-readable label.
    """
    if issubclass(extension_type, UserFacingExtension):
        return call(
            lambda localizer: f"{extension_type.label().localize(localizer)} ({extension_type.name()})"
        )
    return plain(extension_type.name())


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
    def __getitem__(self, extension_type: type[_ExtensionT] | str) -> _ExtensionT:
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
    def __contains__(self, extension_type: type[Extension] | str | Any) -> bool:
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
    def __getitem__(self, extension_type: type[_ExtensionT] | str) -> _ExtensionT:
        if isinstance(extension_type, str):
            extension_type = import_any(extension_type)
        for extension in self.flatten():
            if type(extension) is extension_type:
                return extension  # type: ignore[return-value]
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
    def __contains__(self, extension_type: type[Extension] | str) -> bool:
        if isinstance(extension_type, str):
            try:
                extension_type = import_any(extension_type)
            except ImportError:
                return False
        return any(type(extension) is extension_type for extension in self.flatten())


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


def build_extension_type_graph(
    extension_types: Iterable[type[Extension]],
) -> ExtensionTypeGraph:
    """
    Build a dependency graph of the given extension types.
    """
    extension_types_graph: ExtensionTypeGraph = defaultdict(set)
    # Add dependencies to the extension graph.
    for extension_type in extension_types:
        _extend_extension_type_graph(extension_types_graph, extension_type)
    # Now all dependencies have been collected, extend the graph with optional extension orders.
    for extension_type in extension_types:
        for before in extension_type.comes_before():
            if before in extension_types_graph:
                extension_types_graph[before].add(extension_type)
        for after in extension_type.comes_after():
            if after in extension_types_graph:
                extension_types_graph[extension_type].add(after)

    return extension_types_graph


def _extend_extension_type_graph(
    graph: ExtensionTypeGraph, extension_type: type[Extension]
) -> None:
    dependencies = extension_type.depends_on()
    # Ensure each extension type appears in the graph, even if they're isolated.
    graph.setdefault(extension_type, set())
    for dependency in dependencies:
        seen_dependency = dependency in graph
        graph[extension_type].add(dependency)
        if not seen_dependency:
            _extend_extension_type_graph(graph, dependency)


def discover_extension_types() -> set[type[Extension]]:
    """
    Gather the available extension types.
    """
    betty_entry_points: Sequence[EntryPoint]
    betty_entry_points = entry_points(  # type: ignore[assignment, unused-ignore]
        group="betty.extensions",  # type: ignore[call-arg, unused-ignore]
    )
    return {
        import_any(betty_entry_point.value) for betty_entry_point in betty_entry_points
    }
