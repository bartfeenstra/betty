from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Type, Set, Optional, Any, List, Dict, Sequence, TypeVar, Union, Iterable, TYPE_CHECKING, Generic

from betty.config import ConfigurationT, Configurable

from reactives.factory.type import ReactiveInstance

from betty import fs
from betty.requirement import Requirer, AllRequirements

if TYPE_CHECKING:
    from betty.app import App
try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

from betty.dispatch import Dispatcher, TargetedDispatcher
from betty.importlib import import_any
from reactives import reactive, scope


class CyclicDependencyError(BaseException):
    def __init__(self, extensions: Iterable[Type[Extension]]):
        extension_names = ', '.join([extension.name() for extension in extensions])
        super().__init__(f'The following extensions have cyclic dependencies: {extension_names}')


class Dependencies(AllRequirements):
    def __init__(self, extension_type: Type[Extension]):
        for dependency in extension_type.depends_on():
            try:
                dependency_requirements = [dependency.requires() for dependency in extension_type.depends_on()]
            except RecursionError:
                raise CyclicDependencyError([dependency])
        super().__init__(dependency_requirements)
        self._extension_type = extension_type

    @property
    def summary(self) -> str:
        dependency_names = ', '.join(map(lambda x: x.name(), self._extension_type.depends_on()))
        return f'{self._extension_type.name()} depends on {dependency_names}.'


class Extension(Requirer):
    """
    Integrate optional functionality with the Betty app.
    """

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

    @classmethod
    def requires(cls) -> AllRequirements:
        return AllRequirements([Dependencies(cls)] if cls.depends_on() else [])

    @classmethod
    def name(cls) -> str:
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def label(cls) -> str:
        raise NotImplementedError

    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return set()

    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return set()

    @classmethod
    def comes_before(cls) -> Set[Type[Extension]]:
        return set()

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return None

    @property
    def cache_directory_path(self) -> Path:
        return fs.CACHE_DIRECTORY_PATH / self.name()


ExtensionT = TypeVar('ExtensionT', bound=Extension)


class ConfigurableExtension(Extension, Generic[ConfigurationT], Configurable[ConfigurationT]):
    def __init__(self, *args, **kwargs):
        if 'configuration' not in kwargs or kwargs['configuration'] is None:
            kwargs['configuration'] = self.default_configuration()
        super().__init__(*args, **kwargs)

    @classmethod
    def default_configuration(cls) -> ConfigurationT:
        raise NotImplementedError


@reactive
class Extensions(ReactiveInstance):
    def __getitem__(self, extension_type: Union[Type[ExtensionT], str]) -> ExtensionT:
        raise NotImplementedError

    def __iter__(self) -> Sequence[Sequence[Extension]]:
        raise NotImplementedError

    def flatten(self) -> Sequence[Extension]:
        for batch in self:
            yield from batch

    def __contains__(self, extension_type: Union[Type[Extension], str]) -> bool:
        raise NotImplementedError


class ListExtensions(Extensions):
    def __init__(self, extensions: List[List[Extension]]):
        super().__init__()
        self._extensions = extensions

    @scope.register_self
    def __getitem__(self, extension_type: Union[Type[Extension], str]) -> Extension:
        if isinstance(extension_type, str):
            extension_type = import_any(extension_type)
        for extension in self.flatten():
            if type(extension) == extension_type:
                return extension
        raise KeyError(f'Unknown extension of type "{extension_type}"')

    @scope.register_self
    def __iter__(self) -> Sequence[Sequence[Extension]]:
        # Use a generator so we discourage calling code from storing the result.
        for batch in self._extensions:
            yield (extension for extension in batch)

    @scope.register_self
    def __contains__(self, extension_type: Union[Type[Extension], str]) -> bool:
        if isinstance(extension_type, str):
            try:
                extension_type = import_any(extension_type)
            except ImportError:
                return False
        for extension in self.flatten():
            if type(extension) == extension_type:
                return True
        return False


class ExtensionDispatcher(Dispatcher):
    def __init__(self, extensions: Extensions):
        self._extensions = extensions

    def dispatch(self, target_type: Type) -> TargetedDispatcher:
        target_method_names = [method_name for method_name in dir(target_type) if not method_name.startswith('_')]
        if len(target_method_names) != 1:
            raise ValueError(f"A dispatch's target type must have a single method to dispatch to, but {target_type} has {len(target_method_names)}.")
        target_method_name = target_method_names[0]

        async def _dispatch(*args, **kwargs) -> List[Any]:
            return [
                result
                for target_extension_batch
                in self._extensions
                for result
                in await asyncio.gather(*[
                    getattr(target_extension, target_method_name)(*args, **kwargs)
                    for target_extension in target_extension_batch
                    if isinstance(target_extension, target_type)
                ])
            ]
        return _dispatch


def build_extension_type_graph(extension_types: Set[Type[Extension]]) -> Dict:
    extension_types_graph = defaultdict(set)
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


def _extend_extension_type_graph(graph: Dict, extension_type: Type[Extension]) -> None:
    dependencies = extension_type.depends_on()
    # Ensure each extension type appears in the graph, even if they're isolated.
    graph.setdefault(extension_type, set())
    for dependency in dependencies:
        seen_dependency = dependency in graph
        graph[extension_type].add(dependency)
        if not seen_dependency:
            _extend_extension_type_graph(graph, dependency)


def discover_extension_types() -> Set[Type[Extension]]:
    return {import_any(entry_point.value) for entry_point in entry_points()['betty.extensions']}
