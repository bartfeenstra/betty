import asyncio
from collections import defaultdict

from pathlib import Path

from reactives import reactive

from betty.importlib import import_any

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points
from typing import Type, Set, Optional, Any, List, Dict, Sequence

import betty
from betty.dispatch import Dispatcher, TargetedDispatcher


class Extension:
    """
    Integrate optional functionality with the Betty app.

    Extensions that take configuration must implement betty.extension.ConfigurableExtension.
    """

    def __init__(self, app: 'betty.app.App'):
        self._app = app

    async def __aenter__(self):
        pass  # pragma: no cover

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # pragma: no cover

    @classmethod
    def name(cls) -> str:
        return '%s.%s' % (cls.__module__, cls.__name__)

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
    def assets_directory_path(self) -> Optional[Path]:
        return None


@reactive
class Extensions:
    def __getitem__(self, extension_type: Type[Extension]) -> Extension:
        raise NotImplementedError

    def __iter__(self) -> Sequence[Sequence[Extension]]:
        raise NotImplementedError

    def flatten(self) -> Sequence[Extension]:
        for batch in self:
            yield from batch

    def __contains__(self, extension_type: Type[Extension]) -> bool:
        raise NotImplementedError


@reactive
class Configuration:
    def __init__(self):
        pass


class ConfigurableExtension(Extension):
    def __init__(self, app: 'betty.app.App', configuration: Configuration):
        super().__init__(app)
        self._configuration = configuration

    @classmethod
    def default_configuration(cls) -> Configuration:
        """
        Builds a default configuration object.

        Returns
        -------
        betty.extension.Configuration
            A reactive object specific to this extension.
        """

        raise NotImplementedError

    @classmethod
    def configuration_from_dict(cls, configuration_dict: Dict) -> Configuration:
        """
        Validate and convert the extension's configuration dictionary to a configuration object.

        Returns
        -------
        betty.extension.Configuration
            A reactive object specific to this extension.

        Raises
        ------
        betty.config.ConfigurationValueError
        """

        raise NotImplementedError

    @classmethod
    def configuration_to_dict(cls, configuration: Configuration) -> Dict:
        """
        Convert a configuration object for this extension to a configuration dictionary.

        Returns
        -------
        Dict[str, Any]
        """

        raise NotImplementedError


class ExtensionDispatcher(Dispatcher):
    def __init__(self, extensions: Extensions):
        self._extensions = extensions

    def dispatch(self, target_type: Type, target_method_name: str) -> TargetedDispatcher:
        async def _dispatch(*args, **kwargs) -> List[Any]:
            return [
                await asyncio.gather(*[
                    getattr(target_extension, target_method_name)(*args, **kwargs) for
                    target_extension in target_extension_batch if isinstance(target_extension, target_type)
                ]) for target_extension_batch in self._extensions
            ]
        return _dispatch


def _build_extension_type_graph(extension_types: Set[Type[Extension]]) -> Dict:
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
