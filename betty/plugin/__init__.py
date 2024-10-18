"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TypeVar,
    Generic,
    Self,
    overload,
    TYPE_CHECKING,
    TypeAlias,
    Iterable,
)

from typing_extensions import override

from betty.error import UserFacingError
from betty.factory import TargetFactory, Factory, new
from betty.locale.localizable import _, join, do_you_mean
from betty.machine_name import MachineName

if TYPE_CHECKING:
    from graphlib import TopologicalSorter
    from betty.locale.localizable import Localizable
    from collections.abc import AsyncIterator, Sequence, Mapping, Iterable, Iterator


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
    """

    pass


class Plugin(ABC):
    """
    A plugin.

    Plugins are identified by their :py:meth:`IDs <betty.plugin.Plugin.plugin_id>` as well as their types.
    Each must be able to uniquely identify the plugin within a plugin repository.

    To test your own subclasses, use :py:class:`betty.test_utils.plugin.PluginTestBase`.
    """

    @classmethod
    @abstractmethod
    def plugin_id(cls) -> MachineName:
        """
        Get the plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        pass

    @classmethod
    @abstractmethod
    def plugin_label(cls) -> Localizable:
        """
        Get the human-readable short plugin label.
        """
        pass

    @classmethod
    def plugin_description(cls) -> Localizable | None:
        """
        Get the human-readable long plugin description.
        """
        return None


_PluginT = TypeVar("_PluginT", bound=Plugin)


class OrderedPlugin(Generic[_PluginT], Plugin):
    """
    A plugin that can declare its order with respect to other plugins.
    """

    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[_PluginT]]:
        """
        Get the plugins that this plugin comes before.

        The returned plugins come after this plugin.
        """
        return set()

    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[_PluginT]]:
        """
        Get the plugins that this plugin comes after.

        The returned plugins come before this plugin.
        """
        return set()


class DependentPlugin(Generic[_PluginT], Plugin):
    """
    A plugin that can declare its dependency on other plugins.
    """

    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[_PluginT]]:
        """
        The plugins this one depends on.
        """
        return set()


class ShorthandPluginBase(Plugin):
    """
    Allow shorthand declaration of plugins.
    """

    _plugin_id: MachineName
    _plugin_label: Localizable
    _plugin_description: Localizable | None = None

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls._plugin_id

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return cls._plugin_label

    @override
    @classmethod
    def plugin_description(cls) -> Localizable | None:
        return cls._plugin_description


PluginIdentifier: TypeAlias = type[_PluginT] | MachineName


class PluginNotFound(PluginError, UserFacingError):
    """
    Raised when a plugin cannot be found.
    """

    @classmethod
    def new(
        cls, plugin_id: MachineName, available_plugins: Sequence[type[Plugin]]
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            join(
                _('Could not find a plugin "{plugin_id}".').format(plugin_id=plugin_id),
                do_you_mean(
                    *[f'"{plugin.plugin_id()}"' for plugin in available_plugins]
                ),
            )
        )


_PluginMixinOneT = TypeVar("_PluginMixinOneT")
_PluginMixinTwoT = TypeVar("_PluginMixinTwoT")
_PluginMixinThreeT = TypeVar("_PluginMixinThreeT")


class PluginIdToTypeMap(Generic[_PluginT]):
    """
    Map plugin IDs to their types.
    """

    def __init__(self, id_to_type_map: Mapping[MachineName, type[_PluginT]]):
        self._id_to_type_map = id_to_type_map

    @classmethod
    async def new(cls, plugins: PluginRepository[_PluginT]) -> Self:
        """
        Create a new instance.
        """
        return cls({plugin.plugin_id(): plugin async for plugin in plugins})

    def get(self, plugin_identifier: MachineName | type[_PluginT]) -> type[_PluginT]:
        """
        Get the type for the given plugin identifier.
        """
        if isinstance(plugin_identifier, type):
            return plugin_identifier
        try:
            return self._id_to_type_map[plugin_identifier]
        except KeyError:
            raise PluginNotFound.new(
                plugin_identifier, list(self._id_to_type_map.values())
            ) from None

    def __getitem__(
        self, plugin_identifier: MachineName | type[_PluginT]
    ) -> type[_PluginT]:
        return self.get(plugin_identifier)

    def __iter__(self) -> Iterator[MachineName]:
        yield from self._id_to_type_map

    def values(self) -> Iterator[type[_PluginT]]:
        return self._id_to_type_map.values()


class PluginRepository(Generic[_PluginT], TargetFactory[_PluginT], ABC):
    """
    Discover and manage plugins.
    """

    def __init__(self, *, factory: Factory[_PluginT] | None = None):
        self._factory = factory or new

    async def resolve_identifier(
        self, plugin_identifier: PluginIdentifier[_PluginT]
    ) -> type[_PluginT]:
        """
        Resolve a plugin identifier to a plugin type.
        """
        if isinstance(plugin_identifier, type):
            return plugin_identifier
        return await self.get(plugin_identifier)

    async def resolve_identifiers(
        self, plugin_identifiers: Iterable[PluginIdentifier[_PluginT]]
    ) -> Sequence[type[_PluginT]]:
        """
        Resolve plugin identifiers to plugin types.
        """
        return [
            await self.resolve_identifier(plugin_identifier)
            for plugin_identifier in plugin_identifiers
        ]

    async def map(self) -> PluginIdToTypeMap[_PluginT]:
        """
        Get the plugin ID to type map.
        """
        return await PluginIdToTypeMap.new(self)

    @abstractmethod
    async def get(self, plugin_id: MachineName) -> type[_PluginT]:
        """
        Get a single plugin by its ID.

        :raises PluginNotFound: if no plugin can be found for the given ID.
        """
        pass

    @overload
    async def select(self) -> Sequence[type[_PluginT]]:
        pass

    @overload
    async def select(
        self, mixin_one: type[_PluginMixinOneT]
    ) -> Sequence[type[_PluginT & _PluginMixinOneT]]:
        pass

    @overload
    async def select(
        self, mixin_one: type[_PluginMixinOneT], mixin_two: type[_PluginMixinTwoT]
    ) -> Sequence[type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT]]:
        pass

    @overload
    async def select(
        self,
        mixin_one: type[_PluginMixinOneT],
        mixin_two: type[_PluginMixinTwoT],
        mixin_three: type[_PluginMixinThreeT],
    ) -> Sequence[
        type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT & _PluginMixinThreeT]
    ]:
        pass

    async def select(
        self,
        mixin_one: type[_PluginMixinOneT] | None = None,
        mixin_two: type[_PluginMixinTwoT] | None = None,
        mixin_three: type[_PluginMixinThreeT] | None = None,
    ) -> (
        Sequence[type[_PluginT]]
        | Sequence[type[_PluginT & _PluginMixinOneT]]
        | Sequence[type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT]]
        | Sequence[
            type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT & _PluginMixinThreeT]
        ]
    ):
        """
        Select a subset of the known plugins.

        When called without arguments, this returns all known plugins.
        When called with one or more arguments, this returns all known plugins
        that are also subclasses or **all** of the given mixins.

        This method is overloaded to provide for the majority use case of at most
        three mixins, because when using ``*args: *Ts``, we cannot unpack ``Ts`` into an
        :py:class:`basedtyping.Intersection` return type.
        """
        return [
            plugin
            async for plugin in self
            if self._select_plugin(plugin, mixin_one, mixin_two, mixin_three)
        ]

    def _select_plugin(
        self,
        plugin: type[_PluginT],
        mixin_one: type[_PluginMixinOneT] | None = None,
        mixin_two: type[_PluginMixinTwoT] | None = None,
        mixin_three: type[_PluginMixinThreeT] | None = None,
    ) -> bool:
        for mixin in (mixin_one, mixin_two, mixin_three):
            if mixin is None:
                continue
            if not issubclass(plugin, mixin):
                return False
        return True

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        pass

    @override
    async def new_target(self, cls: PluginIdentifier[_PluginT]) -> _PluginT:
        if isinstance(cls, str):
            cls = await self.get(cls)
        return await self._factory(cls)


class CyclicDependencyError(PluginError):
    """
    Raised when plugins define a cyclic dependency, e.g. two plugins depend on each other.
    """

    def __init__(self, plugin_types: Iterable[type[Plugin]]):
        plugin_names = ", ".join([plugin.plugin_id() for plugin in plugin_types])
        super().__init__(
            f"The following plugins have cyclic dependencies: {plugin_names}"
        )


async def sort_ordered_plugin_graph(
    sorter: TopologicalSorter[type[_PluginT]],
    plugins: PluginRepository[_PluginT & OrderedPlugin[_PluginT]],
    entry_point_plugins: Iterable[type[_PluginT & OrderedPlugin[_PluginT]]],
) -> None:
    """
    Build a graph of the given plugins.
    """
    entry_point_plugins = list(entry_point_plugins)
    for entry_point_plugin in entry_point_plugins:
        sorter.add(entry_point_plugin)
        for before_identifier in entry_point_plugin.comes_before():
            before = (
                await plugins.get(before_identifier)
                if isinstance(before_identifier, str)
                else before_identifier
            )
            if before in entry_point_plugins:
                sorter.add(before, entry_point_plugin)
        for after_identifier in entry_point_plugin.comes_after():
            after = (
                await plugins.get(after_identifier)
                if isinstance(after_identifier, str)
                else after_identifier
            )
            if after in entry_point_plugins:
                sorter.add(entry_point_plugin, after)


async def sort_dependent_plugin_graph(
    sorter: TopologicalSorter[type[_PluginT]],
    plugins: PluginRepository[_PluginT],
    entry_point_plugins: Iterable[type[_PluginT & DependentPlugin[_PluginT]]],
) -> None:
    """
    Build a graph of the given plugins and their dependencies.
    """
    for entry_point_plugin in entry_point_plugins:
        dependencies = entry_point_plugin.depends_on()
        sorter.add(
            entry_point_plugin,
            *(await plugins.resolve_identifiers(dependencies)),
        )
        await sort_dependent_plugin_graph(
            sorter,
            plugins,
            # We have not quite figured out how to type this correctly, so ignore any errors for now.
            dependencies,  # type: ignore[arg-type]
        )
