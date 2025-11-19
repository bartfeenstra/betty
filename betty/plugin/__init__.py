"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from contextlib import contextmanager
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

from typing_extensions import TypeVar

from betty.concurrent import AsynchronizedLock
from betty.exception import HumanFacingException
from betty.json.schema import Enum
from betty.locale.localizable import CountableLocalizable, Paragraph, _, do_you_mean
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import threadsafe

if TYPE_CHECKING:
    import builtins
    from collections.abc import (
        Collection,
        Iterable,
        Iterator,
        Mapping,
        MutableMapping,
        Sequence,
    )

    from betty.locale.localizable import Localizable
    from betty.plugin.discovery import PluginDiscovery
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
class PluginTypeDefinition(Generic[_PluginDefinitionT]):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
        label: Localizable,
        discoveries: Collection[PluginDiscovery[_PluginDefinitionT]]
        | PluginDiscovery[_PluginDefinitionT]
        | None = None,
    ):
        from betty.plugin.discovery import PluginDiscovery

        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(id)
        self._id = id
        self._label = label
        if discoveries is None:
            discoveries = []
        elif isinstance(discoveries, PluginDiscovery):
            discoveries = [discoveries]
        else:
            discoveries = list(discoveries)
        self._defined_discoveries = discoveries
        self._discoveries = self._defined_discoveries

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
    def discoveries(
        self,
    ) -> Collection[PluginDiscovery[_PluginDefinitionT]]:
        """
        The plugin discoveries for this type.
        """
        return self._discoveries

    def add_discovery(self, discovery: PluginDiscovery[_PluginDefinitionT], /) -> None:
        """
        Add a plugin discovery for this type.
        """
        return self._defined_discoveries.append(discovery)

    @contextmanager
    def override_discoveries(self, *plugins: _PluginDefinitionT) -> Iterator[None]:
        """
        Temporarily override the discoveries for this plugin type.
        """
        from betty.plugin.discovery.static import StaticDiscovery

        self._discoveries = [StaticDiscovery(*plugins)]
        yield
        self._discoveries = self._defined_discoveries

    @property
    def discoveries_overridden(self) -> bool:
        """
        Whether the discoveries are currently overridden.
        """
        return self._defined_discoveries != self._discoveries


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
        plugin_type: PluginTypeDefinition[_PluginDefinitionT],
        plugin_not_found: MachineName,
        available_plugins: Sequence[PluginIdentifier[_PluginDefinitionT]],
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


@final
class PluginRepository(Generic[_PluginDefinitionT]):
    """
    Discover and manage plugins.
    """

    def __init__(
        self, plugin_type: type[_PluginDefinitionT], *plugins: _PluginDefinitionT
    ):
        self._plugin_type = plugin_type
        self._plugins = {plugin.id: plugin for plugin in plugins}
        self._plugin_id_schema: Enum | None = None

    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginNotFound: if no plugin can be found for the given ID.
        """
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound(
                self._plugin_type.type, plugin_id, list(self)
            ) from None

    def __len__(self) -> int:
        return len(self._plugins)

    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        yield from self._plugins.values()

    def __getitem__(self, plugin_id: MachineName) -> _PluginDefinitionT:
        return self.get(plugin_id)

    @property
    def plugin_id_schema(self) -> Enum:
        """
        Get the JSON schema for the IDs of the plugins in this repository.
        """
        if self._plugin_id_schema is None:
            label = self._plugin_type.type.label.localize(DEFAULT_LOCALIZER)
            self._plugin_id_schema = Enum(
                *[plugin.id for plugin in self],  # noqa A002
                def_name=kebab_case_to_lower_camel_case(self._plugin_type.type.id),
                title=label,
                description=f"A {label} plugin ID",
            )
        return self._plugin_id_schema


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
        if plugin.type.discoveries_overridden:
            return await self._build(plugin, plugin.type.discoveries)
        if plugin not in self._plugin_repositories:  # type: ignore[comparison-overlap]
            async with self._lock:
                if plugin not in self._plugin_repositories:  # type: ignore[comparison-overlap]
                    self._plugin_repositories[plugin] = await self._build(  # type: ignore[index]
                        plugin,
                        plugin.type.discoveries,  # type: ignore[arg-type]
                    )
        return self._plugin_repositories[plugin]  # type: ignore[index,return-value]

    async def _build(
        self,
        plugin: type[_PluginDefinitionT],
        discoveries: Iterable[PluginDiscovery[_PluginDefinitionT]],
    ) -> PluginRepository[_PluginDefinitionT]:
        from betty.plugin.discovery import discover

        return PluginRepository(
            plugin, *await discover(self._service_level, *discoveries)
        )


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
