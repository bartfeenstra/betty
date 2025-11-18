"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from contextlib import contextmanager
from graphlib import TopologicalSorter
from importlib import metadata
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Self,
    TypeAlias,
    cast,
    final,
)

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.concurrent import AsynchronizedLock
from betty.exception import HumanFacingException
from betty.json.schema import Enum
from betty.locale.localizable import CountableLocalizable, Paragraph, _, do_you_mean
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import internal, threadsafe

if TYPE_CHECKING:
    import builtins
    from collections.abc import (
        Awaitable,
        Callable,
        Collection,
        Iterable,
        Iterator,
        Mapping,
        MutableMapping,
        Sequence,
        Set,
    )

    from betty.app import App
    from betty.locale.localizable import Localizable
    from betty.project import Project
    from betty.project.extension import Extension, ExtensionDefinition
    from betty.service_level import ServiceLevel

_PluginT = TypeVar("_PluginT")


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """


class PluginRepositoryUnavailable(PluginError):
    """
    The requested plugin repository is not available.
    """


class PluginDefinition:
    """
    A plugin definition.
    """

    type: ClassVar[PluginTypeDefinition[Self]]

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
    ):
        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(id)
        self._id = id

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        return self._id


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_PluginDefinitionCoT = TypeVar(
    "_PluginDefinitionCoT",
    bound=PluginDefinition,
    default=PluginDefinition,
    covariant=True,
)


@final
class PluginTypeDefinition(Generic[_PluginDefinitionCoT]):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
        label: Localizable,
        repositories: Collection[PluginRepositoryDefinition[_PluginDefinitionCoT]]
        | PluginRepositoryDefinition[_PluginDefinitionCoT]
        | None = None,
    ):
        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(id)
        self._id = id
        self._label = label
        if repositories is None:
            repositories = []
        elif isinstance(repositories, PluginRepositoryDefinition):
            repositories = [repositories]
        else:
            repositories = list(repositories)
        self._defined_repositories = repositories
        self._repositories = self._defined_repositories

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @property
    def label(self) -> Localizable:
        """
        The plugin type label.
        """
        return self._label

    @property
    def repositories(
        self,
    ) -> Collection[PluginRepositoryDefinition[_PluginDefinitionCoT]]:
        """
        The plugin repositories for this type.
        """
        return self._repositories

    def add_repository(
        self, repository: PluginRepositoryDefinition[_PluginDefinitionCoT], /
    ) -> None:
        """
        Add a plugin repository for this type.
        """
        return self._defined_repositories.append(repository)

    @contextmanager
    def override_repositories(
        self, plugins: PluginRepository[_PluginDefinitionCoT]
    ) -> Iterator[None]:
        """
        Temporarily override the repositories for this plugin type.
        """
        self._repositories = [GlobalPluginRepositoryDefinition(lambda: plugins)]
        yield
        self._repositories = self._defined_repositories

    @property
    def repositories_overridden(self) -> bool:
        """
        Whether the repositories are currently overridden.
        """
        return self._defined_repositories != self._repositories


def plugin_types() -> Mapping[MachineName, type[PluginDefinition]]:
    """
    Get the available plugin types.
    """
    return {
        plugin.type.id: plugin
        for entry_point in metadata.entry_points(group="betty.plugin")
        if (plugin := entry_point.load())
    }


class ClassedPlugin:
    """
    A plugin class that can expose its plugin.
    """

    plugin: ClassVar[ClassedPluginDefinition[Self]]


_ClassedPluginT = TypeVar("_ClassedPluginT", bound=ClassedPlugin, default=ClassedPlugin)


class HumanFacingPluginDefinition(PluginDefinition):
    """
    A definition of a plugin that is human-facing.
    """

    def __init__(
        self,
        *args: Any,
        label: Localizable,
        description: Localizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._label = label
        self._description = description

    @property
    def label(self) -> Localizable:
        """
        The human-readable short plugin label (singular).
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long plugin description.
        """
        return self._description


class CountableHumanFacingPluginDefinition(HumanFacingPluginDefinition):
    """
    A definition of a plugin that is human-facing, and of which instances are countable.
    """

    def __init__(
        self,
        *args: Any,
        label_plural: Localizable,
        label_countable: CountableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._label_plural = label_plural
        self._label_countable = label_countable

    @property
    def label_plural(self) -> Localizable:
        """
        The human-readable short plugin label (plural).
        """
        return self._label_plural

    @property
    def label_countable(self) -> CountableLocalizable:
        """
        The human-readable short plugin label (countable).
        """
        return self._label_countable


class OrderedPluginDefinition(PluginDefinition):
    """
    A definition of plugin that can declare its order with respect to other plugins.
    """

    def __init__(
        self,
        *,
        comes_before: Set[PluginIdentifier] | None = None,
        comes_after: Set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._comes_before = (
            set()
            if comes_before is None
            else {resolve_id(plugin) for plugin in comes_before}
        )
        self._comes_after = (
            set()
            if comes_after is None
            else {resolve_id(plugin) for plugin in comes_after}
        )

    @property
    def comes_before(self) -> Set[MachineName]:
        """
        Get the plugins that this plugin comes before.

        The returned plugins come after this plugin.
        """
        return self._comes_before

    @property
    def comes_after(self) -> Set[MachineName]:
        """
        Get the plugins that this plugin comes after.

        The returned plugins come before this plugin.
        """
        return self._comes_after


_OrderedPluginDefinitionT = TypeVar(
    "_OrderedPluginDefinitionT", bound=OrderedPluginDefinition
)


class DependentPluginDefinition(OrderedPluginDefinition):
    """
    A definition of a plugin that can declare its dependency on other plugins.
    """

    def __init__(
        self,
        *,
        depends_on: Set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._depends_on = (
            set()
            if depends_on is None
            else {resolve_id(plugin) for plugin in depends_on}
        )
        self._comes_after.update(self._depends_on)

    @property
    def depends_on(self) -> Set[MachineName]:
        """
        The plugins this one depends on.

        All plugins will automatically be added to :py:meth:`betty.plugin.OrderedPluginDefinition.comes_after`.
        """
        return self._depends_on


_DependentPluginDefinitionT = TypeVar(
    "_DependentPluginDefinitionT", bound=DependentPluginDefinition
)


class ClassedPluginDefinition(Generic[_PluginT], PluginDefinition):
    """
    A definition of a plugin that is based around a class.
    """

    plugin_type_cls: ClassVar[type]

    def __init__(
        self,
        *,
        cls: builtins.type[_PluginT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._cls = cls
        if cls is not None:
            self._set_cls(cls)

    @property
    def cls(self) -> builtins.type[_PluginT]:
        """
        The plugin class.
        """
        assert self._cls is not None
        return self._cls

    def _set_cls(self, cls: builtins.type[_PluginT]) -> None:
        cls.plugin = self  # type: ignore[attr-defined]

    def __call__(self, cls: builtins.type[_PluginT]) -> builtins.type[_PluginT]:
        """
        Set the plugin's class.
        """
        assert self._cls is None
        self._set_cls(cls)
        self._cls = cls
        return cls


ResolvablePluginDefinition: TypeAlias = _PluginDefinitionT | type[_ClassedPluginT]
PluginIdentifier: TypeAlias = (
    MachineName | ResolvablePluginDefinition[_PluginDefinitionT, _ClassedPluginT]
)


def resolve_definition(definition: ResolvablePluginDefinition, /) -> PluginDefinition:
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition
    return definition.plugin


def resolve_id(plugin_id: PluginIdentifier, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, str):
        return plugin_id
    return resolve_definition(plugin_id).id


class PluginNotFound(PluginError, HumanFacingException):
    """
    Raised when a plugin cannot be found.
    """

    def __init__(
        self,
        plugin_type: PluginTypeDefinition,
        plugin_not_found: MachineName,
        available_plugins: Sequence[PluginIdentifier],
        /,
    ):
        super().__init__(
            Paragraph(
                _('Could not find a(n) {plugin_type} plugin "{plugin_id}".').format(
                    plugin_type=plugin_type.label, plugin_id=plugin_not_found
                ),
                do_you_mean(
                    *[
                        f'"{resolve_id(available_plugin)}"'
                        for available_plugin in available_plugins
                    ]
                ),
            )
        )


class PluginRepository(Generic[_PluginDefinitionCoT], ABC):
    """
    Discover and manage plugins.
    """

    def __init__(
        self,
        plugin: type[_PluginDefinitionCoT],
        /,
    ):
        self._plugin = plugin
        self._plugin_id_schema: Enum | None = None

    @abstractmethod
    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionCoT:
        """
        Get a single plugin by its ID.

        :raises PluginNotFound: if no plugin can be found for the given ID.
        """

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    @abstractmethod
    def __iter__(self) -> Iterator[_PluginDefinitionCoT]:
        pass

    def __getitem__(self, plugin_id: MachineName) -> _PluginDefinitionCoT:
        return self.get(plugin_id)

    @property
    def plugin_id_schema(self) -> Enum:
        """
        Get the JSON schema for the IDs of the plugins in this repository.
        """
        if self._plugin_id_schema is None:
            label = self._plugin.type.label.localize(DEFAULT_LOCALIZER)
            self._plugin_id_schema = Enum(
                *[plugin.id for plugin in self],  # noqa A002
                def_name=kebab_case_to_lower_camel_case(self._plugin.type.id),
                title=label,
                description=f"A {label} plugin ID",
            )
        return self._plugin_id_schema


@internal
class PluginRepositoryDefinition(Generic[_PluginDefinitionT], ABC):
    """
    A plugin repository definition.
    """

    # @todo Rename this to resolve() or something. Let's avoid implementing __call__() anywhere
    # @todo except if an object MUST be used where Callable is expected.
    # @todo
    # @todo
    # @todo
    # @todo
    # @todo
    # @todo
    # @todo
    # @todo
    # @todo
    @abstractmethod
    async def __call__(
        self, service_level: ServiceLevel, /
    ) -> PluginRepository[_PluginDefinitionT] | None:
        """
        Get the repository for this plugin type.
        """


@final
class GlobalPluginRepositoryDefinition(
    PluginRepositoryDefinition[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Define a plugin repository that is available globally.
    """

    def __init__(
        self,
        repository: Callable[[], Awaitable[PluginRepository[_PluginDefinitionT]]]
        | Callable[[], PluginRepository[_PluginDefinitionT]]
        | PluginRepository[_PluginDefinitionT],
        /,
    ):
        self._repository = repository

    @override
    async def __call__(
        self, service_level: ServiceLevel, /
    ) -> PluginRepository[_PluginDefinitionT] | None:
        if isinstance(self._repository, PluginRepository):
            return self._repository
        return await ensure_await(self._repository())


@final
@internal
class AppPluginRepositoryDefinition(
    PluginRepositoryDefinition[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Define a plugin repository that is available when an :py:class:`betty.app.App` is available.
    """

    def __init__(
        self,
        repository: Callable[[App], Awaitable[PluginRepository[_PluginDefinitionT]]]
        | Callable[[App], PluginRepository[_PluginDefinitionT]],
        /,
    ):
        self._repository = repository

    @override
    async def __call__(
        self, service_level: ServiceLevel, /
    ) -> PluginRepository[_PluginDefinitionT] | None:
        from betty.project import Project

        if service_level is None:
            return None
        if isinstance(service_level, Project):
            service_level = service_level.app
        return await ensure_await(self._repository(service_level))


@final
@internal
class ProjectPluginRepositoryDefinition(
    PluginRepositoryDefinition[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Define a plugin repository that is available when a :py:class:`betty.project.Project` is available.
    """

    def __init__(
        self,
        repository: Callable[[Project], Awaitable[PluginRepository[_PluginDefinitionT]]]
        | Callable[[Project], PluginRepository[_PluginDefinitionT]],
        /,
    ):
        self._repository = repository

    @override
    async def __call__(
        self, service_level: ServiceLevel, /
    ) -> PluginRepository[_PluginDefinitionT] | None:
        from betty.project import Project

        if not isinstance(service_level, Project):
            return None
        return await ensure_await(self._repository(service_level))


@final
class ExtensionPluginRepositoryDefinition(
    PluginRepositoryDefinition[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Define a plugin repository that is available when a specific :py:class:`betty.project.extension.Extension` is available.
    """

    def __init__(
        self,
        extension: PluginIdentifier[ExtensionDefinition, Extension],
        repository: Callable[
            [Extension], Awaitable[PluginRepository[_PluginDefinitionT]]
        ]
        | Callable[[Extension], PluginRepository[_PluginDefinitionT]],
        /,
    ):
        self._extension_id = resolve_id(extension)
        self._repository = repository

    @override
    async def __call__(
        self, service_level: ServiceLevel, /
    ) -> PluginRepository[_PluginDefinitionT] | None:
        from betty.project import Project

        if not isinstance(service_level, Project):
            return None
        extensions = await service_level.extensions
        if self._extension_id not in extensions:
            return None
        return await ensure_await(self._repository(extensions[self._extension_id]))


@threadsafe
class PluginRepositoryProvider:
    """
    Provide plugin repositories.
    """

    def __init__(self, *args: Any, service_level: ServiceLevel, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._service_level = service_level
        self._plugin_repositories: MutableMapping[
            PluginDefinition, PluginRepository
        ] = {}
        self._lock = AsynchronizedLock.new_threadsafe()

    async def plugins(
        self, plugin: type[_PluginDefinitionT] | MachineName, /
    ) -> PluginRepository[_PluginDefinitionT]:
        """
        Get the plugin repository for a plugin type.
        """
        if isinstance(plugin, str):
            plugin = cast(type[_PluginDefinitionT], plugin_types()[plugin])
        if plugin.type.repositories_overridden:
            return await self._build(plugin, plugin.type.repositories)
        if plugin not in self._plugin_repositories:  # type: ignore[comparison-overlap]
            async with self._lock:
                if plugin not in self._plugin_repositories:  # type: ignore[comparison-overlap]
                    self._plugin_repositories[plugin] = await self._build(  # type: ignore[index]
                        plugin,
                        plugin.type.repositories,  # type: ignore[arg-type]
                    )
        return self._plugin_repositories[plugin]  # type: ignore[index,return-value]

    async def _build(
        self,
        plugin: type[_PluginDefinitionT],
        definitions: Iterable[PluginRepositoryDefinition[_PluginDefinitionT]],
    ) -> PluginRepository[_PluginDefinitionT]:
        from betty.plugin.proxy import ProxyPluginRepository

        repositories = [
            repository
            for definition in definitions
            if (repository := await definition(self._service_level))
            and repository is not None
        ]
        if len(repositories) == 1:
            return repositories[0]
        return ProxyPluginRepository(plugin, *repositories)


_global_plugins = PluginRepositoryProvider(service_level=None)
plugins = _global_plugins.plugins


class CyclicDependencyError(PluginError):
    """
    Raised when plugins define a cyclic dependency, e.g. two plugins depend on each other.
    """

    def __init__(self, plugin_ids: Iterable[MachineName], /):
        plugin_names = ", ".join(plugin_ids)
        super().__init__(
            f"The following plugins have cyclic dependencies: {plugin_names}"
        )


async def sort_ordered_plugin_graph(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    plugins: Iterable[_OrderedPluginDefinitionT],
    /,
) -> TopologicalSorter[MachineName]:
    """
    Build a graph of the given plugins.
    """
    sorter = TopologicalSorter[MachineName]()
    plugins = sorted(plugins, key=lambda plugin: plugin.id)
    for plugin in plugins:
        sorter.add(plugin.id)
        for before_identifier in map(resolve_id, plugin.comes_before):
            before = plugin_repository[before_identifier]
            if before in plugins:
                sorter.add(before.id, plugin.id)
        for after_identifier in map(resolve_id, plugin.comes_after):
            after = plugin_repository[after_identifier]
            if after in plugins:
                sorter.add(plugin.id, after.id)
    return sorter


async def expand_plugin_dependencies(
    plugin_repository: PluginRepository[_DependentPluginDefinitionT],
    plugins: Iterable[_DependentPluginDefinitionT],
    /,
) -> set[_DependentPluginDefinitionT]:
    """
    Expand a collection of plugins to include their dependencies.
    """
    dependencies = set()
    for plugin in plugins:
        dependencies.add(plugin)
        dependencies.update(
            await expand_plugin_dependencies(
                plugin_repository,
                [plugin_repository.get(depends_on) for depends_on in plugin.depends_on],
            )
        )
    return dependencies


async def sort_dependent_plugin_graph(
    plugin_repository: PluginRepository[_DependentPluginDefinitionT],
    plugins: Iterable[_DependentPluginDefinitionT],
    /,
) -> TopologicalSorter[MachineName]:
    """
    Sort a dependent plugin graph.
    """
    return await sort_ordered_plugin_graph(
        plugin_repository, await expand_plugin_dependencies(plugin_repository, plugins)
    )


def _collect_plugin_graph(
    graph: Mapping[_PluginDefinitionT, set[_PluginDefinitionT]],
    origin: _PluginDefinitionT,
) -> Iterator[_PluginDefinitionT]:
    yield from graph[origin]
    for target in graph[origin]:
        yield from _collect_plugin_graph(graph, target)


def get_comes_before(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    origin: _OrderedPluginDefinitionT,
    /,
) -> set[_OrderedPluginDefinitionT]:
    """
    Get all other plugins the given plugin comes before.
    """
    graph = defaultdict(set)
    for plugin in plugin_repository:
        for comes_before_id in plugin.comes_before:
            comes_before = plugin_repository[comes_before_id]
            graph[plugin].add(comes_before)
        for comes_after_id in plugin.comes_after:
            comes_after = plugin_repository[comes_after_id]
            graph[comes_after].add(plugin)
    return set(_collect_plugin_graph(graph, origin))


def get_comes_after(
    plugin_repository: PluginRepository[_OrderedPluginDefinitionT],
    origin: _OrderedPluginDefinitionT,
    /,
) -> set[_OrderedPluginDefinitionT]:
    """
    Get all other plugins the given plugin comes after.
    """
    graph = defaultdict(set)
    for plugin in plugin_repository:
        for comes_after_id in plugin.comes_after:
            comes_after = plugin_repository[comes_after_id]
            graph[plugin].add(comes_after)
        for comes_before_id in plugin.comes_before:
            comes_before = plugin_repository[comes_before_id]
            graph[comes_before].add(plugin)
    return set(_collect_plugin_graph(graph, origin))
