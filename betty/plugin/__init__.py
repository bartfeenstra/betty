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
    final,
)

from typing_extensions import TypeVar

from betty.exception import HumanFacingException
from betty.locale.localizable import CountableLocalizable, Paragraph, _, do_you_mean
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name

if TYPE_CHECKING:
    import builtins
    from collections.abc import (
        Collection,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )

    from betty.locale.localizable import Localizable
    from betty.plugin.discovery import PluginDiscovery

_PluginT = TypeVar("_PluginT")


class PluginError(Exception):
    """
    Any error originating from the Plugin API.
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
    def override_discovery(self, *plugins: _PluginDefinitionT) -> Iterator[None]:
        """
        Temporarily override the discoveries for this plugin type with the given plugins.
        """
        from betty.plugin.discovery.static import StaticDiscovery

        self._discoveries = [StaticDiscovery(*plugins)]
        yield
        self._discoveries = self._defined_discoveries

    @property
    def discovery_overridden(self) -> bool:
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


class CyclicDependencyError(PluginError):
    """
    Raised when plugins define a cyclic dependency, e.g. two plugins depend on each other.
    """

    def __init__(self, plugin_ids: Iterable[MachineName], /):
        plugin_names = ", ".join(plugin_ids)
        super().__init__(
            f"The following plugins have cyclic dependencies: {plugin_names}"
        )
