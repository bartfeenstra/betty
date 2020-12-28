import asyncio
from collections import defaultdict
from typing import Type, Set, Optional, Any, List

from voluptuous import Schema

from betty.app import App
from betty.dispatch import Dispatcher, TargetedDispatcher
from betty.graph import Graph, tsort_grouped

NO_CONFIGURATION = None


class Extension:
    configuration_schema: Schema = Schema(None)

    async def __aenter__(self):
        pass  # pragma: no cover

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # pragma: no cover

    @classmethod
    def name(cls) -> str:
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def new_for_app(cls, app: App, configuration: Any = NO_CONFIGURATION):
        """
        Creates a new instance for a specific app.
        :param app: betty.app.App
        :param configuration: The configuration must be of the same type as returned by cls.configuration_schema.
        :return: Self
        """
        return cls()

    @classmethod
    def depends_on(cls) -> Set[Type['Extension']]:
        return set()

    @classmethod
    def comes_after(cls) -> Set[Type['Extension']]:
        return set()

    @classmethod
    def comes_before(cls) -> Set[Type['Extension']]:
        return set()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return None


class ExtensionDispatcher(Dispatcher):
    def __init__(self, extensions: List['Extension']):
        self._extensions = extensions

    def dispatch(self, target_type: Type, target_method_name: str) -> TargetedDispatcher:
        target_extensions = {type(extension): extension for extension in self._extensions if isinstance(extension, target_type)}
        target_extension_graph = build_extension_type_graph(set(target_extensions.keys()))

        async def _dispatch(*args, **kwargs) -> TargetedDispatcher:
            # @todo This must ensure group order!
            return await asyncio.gather(*[
                asyncio.gather(*[
                    getattr(target_extensions[target_extension_type], target_method_name)(*args, **kwargs) for target_extension_type in target_extension_type_group
                ]) for target_extension_type_group in tsort_grouped(target_extension_graph)
            ])
        return _dispatch


def build_extension_type_graph(extension_types: Set[Type[Extension]]) -> Graph:
    extension_types_graph = defaultdict(set)
    # Add dependencies to the extension graph.
    for extension_type in extension_types:
        _extend_extension_type_graph(extension_types_graph, extension_type)
    # Now all dependencies have been collected, extend the graph with optional extension orders.
    for extension_type in extension_types:
        for before in extension_type.comes_before():
            if before in extension_types_graph:
                extension_types_graph[extension_type].add(before)
        for after in extension_type.comes_after():
            if after in extension_types_graph:
                extension_types_graph[after].add(extension_type)

    return extension_types_graph


def _extend_extension_type_graph(graph: Graph, extension_type: Type['Extension']) -> None:
    dependencies = extension_type.depends_on()
    # Ensure each extension type appears in the graph, even if they're isolated.
    graph.setdefault(extension_type, set())
    for dependency in dependencies:
        seen_dependency = dependency in graph
        graph[dependency].add(extension_type)
        if not seen_dependency:
            _extend_extension_type_graph(graph, dependency)
