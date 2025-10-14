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
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self, TypeAlias

from typing_extensions import TypeVar

from betty.exception import UserFacingException
from betty.json.schema import Enum
from betty.locale.localizable import CountableLocalizable, Join, _, do_you_mean
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name
from betty.string import kebab_case_to_lower_camel_case
from betty.user import UserFacing

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterable, Iterator, Mapping, Sequence

    from betty.locale.localizable import Localizable

_PluginT = TypeVar("_PluginT")


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """


class PluginDefinition:
    """
    A plugin definition.
    """

    type: ClassVar[PluginTypeDefinition]

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
    ):
        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName.new(id)
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
    "_PluginDefinitionCoT", bound=PluginDefinition, covariant=True
)


class PluginTypeDefinition:
    """
    A plugin type definition.
    """

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
        label: Localizable,
    ):
        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName.new(id)
        self._id = id
        self._label = label

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


class ClassedPlugin:
    """
    A plugin class that can expose its plugin.
    """

    plugin: ClassVar[ClassedPluginDefinition[Self]]


_ClassedPluginT = TypeVar("_ClassedPluginT", bound=ClassedPlugin, default=ClassedPlugin)


class ClassedPluginTypeDefinition(PluginTypeDefinition):
    """
    A plugin type definition for classed plugins.
    """

    def __init__(
        self,
        *,
        cls: type,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._cls = cls

    @property
    def cls(self) -> type:
        """
        The base class for all plugins of this type.
        """
        return self._cls


class UserFacingPluginDefinition(UserFacing, PluginDefinition):
    """
    A definition of a plugin that is user-facing.
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


class CountableUserFacingPluginDefinition(UserFacingPluginDefinition):
    """
    A definition of a plugin that is user-facing, and of which instances are countable.
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
        comes_before: set[PluginIdentifier] | None = None,
        comes_after: set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._comes_before = (
            set()
            if comes_before is None
            else {resolve_identifier(plugin) for plugin in comes_before}
        )
        self._comes_after = (
            set()
            if comes_after is None
            else {resolve_identifier(plugin) for plugin in comes_after}
        )

    @property
    def comes_before(self) -> set[MachineName]:
        """
        Get the plugins that this plugin comes before.

        The returned plugins come after this plugin.
        """
        return self._comes_before

    @property
    def comes_after(self) -> set[MachineName]:
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
        depends_on: set[PluginIdentifier] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._depends_on = (
            set()
            if depends_on is None
            else {resolve_identifier(plugin) for plugin in depends_on}
        )

    @property
    def depends_on(self) -> set[MachineName]:
        """
        The plugins this one depends on.

        To declare whether this plugin comes before or after its dependencies, use
        :py:meth:`betty.plugin.OrderedPluginDefinition.comes_before` and/or
        :py:meth:`betty.plugin.OrderedPluginDefinition.comes_after`.
        """
        return self._depends_on


_DependentPluginDefinitionT = TypeVar(
    "_DependentPluginDefinitionT", bound=DependentPluginDefinition
)


class ClassedPluginDefinition(Generic[_PluginT], PluginDefinition):
    """
    A definition of a plugin that is based around a class.
    """

    type: ClassVar[ClassedPluginTypeDefinition]

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


PluginIdentifier: TypeAlias = MachineName | _PluginDefinitionT | type[_ClassedPluginT]


def resolve_identifier(identifier: PluginIdentifier, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(identifier, type) and issubclass(identifier, ClassedPlugin):
        return identifier.plugin.id
    if isinstance(identifier, PluginDefinition):
        return identifier.id
    return identifier


class PluginNotFound(PluginError, UserFacingException):
    """
    Raised when a plugin cannot be found.
    """

    @classmethod
    def new(
        cls,
        plugin_not_found: MachineName,
        available_plugins: Sequence[PluginIdentifier],
        /,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            Join(
                " ",
                _('Could not find a plugin "{plugin_id}".').format(
                    plugin_id=plugin_not_found
                ),
                do_you_mean(
                    *[
                        f'"{resolve_identifier(available_plugin)}"'
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
        for before_identifier in map(resolve_identifier, plugin.comes_before):
            before = plugin_repository[before_identifier]
            if before in plugins:
                sorter.add(before.id, plugin.id)
        for after_identifier in map(resolve_identifier, plugin.comes_after):
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
