"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib import metadata
from typing import TYPE_CHECKING, ClassVar, Generic, final

from typing_extensions import TypeVar

from betty.locale.localizable import LocalizableLike, _, ensure_localizable
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name

if TYPE_CHECKING:
    import builtins
    from collections.abc import Collection, Iterator, Mapping

    from betty.locale.localizable import Localizable
    from betty.plugin.discovery import PluginDiscovery


class Plugin:
    """
    A plugin class that can expose its plugin.

    ``__init__()`` is considered private to the :py:mod:`factory <betty.factory>` API. That means you MUST use the
    factory API to create new instances.
    """

    plugin: ClassVar[PluginDefinition]


_PluginCoT = TypeVar("_PluginCoT", bound=Plugin, default=Plugin, covariant=True)


class PluginDefinition(Generic[_PluginCoT]):
    """
    A plugin definition.
    """

    plugin_type_cls: ClassVar[type[Plugin]]

    type: ClassVar[PluginTypeDefinition]

    def __init__(self, plugin_id: MachineName, /):
        if not validate_machine_name(plugin_id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(plugin_id)
        self._id = plugin_id
        self._cls: type[_PluginCoT] | None = None

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        return self._id

    @property
    def cls(self) -> builtins.type[_PluginCoT]:
        """
        The plugin class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """
        if self._cls is None:
            raise ValueError("This definition was not yet used to decorate a class.")
        assert self._cls is not None
        return self._cls

    def __call__(self, cls: builtins.type[_PluginCoT]) -> builtins.type[_PluginCoT]:
        """
        Set the plugin's class.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        if self._cls is not None:
            raise ValueError("This definition was already used to decorate a class.")
        assert self._cls is None
        cls.plugin = self
        self._cls = cls
        return cls

    @property
    def reference_label(self) -> Localizable:
        """
        The label to reference this plugin with.
        """
        return _('"{plugin_id}"').format(plugin_id=self.id)

    @property
    def reference_label_with_type(self) -> Localizable:
        """
        The label to reference this plugin with, including the plugin type.
        """
        return _('{plugin_type} "{plugin_id}"').format(
            plugin_type=self.type.label,
            plugin_id=self.id,
        )


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
        id: MachineName,  # noqa A002
        label: LocalizableLike,
        *,
        discoveries: Collection[PluginDiscovery[_PluginDefinitionT]]
        | PluginDiscovery[_PluginDefinitionT]
        | None = None,
    ):
        from betty.plugin.discovery import PluginDiscovery

        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(id)
        self._id = id
        self._label = ensure_localizable(label)
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


_plugin_types: Mapping[MachineName, type[PluginDefinition]] | None = None


def plugin_types() -> Mapping[MachineName, type[PluginDefinition]]:
    """
    Get the available plugin types.
    """
    global _plugin_types

    if _plugin_types is None:
        _plugin_types = {
            plugin.type.id: plugin
            for entry_point in metadata.entry_points(group="betty.plugin")
            if (plugin := entry_point.load())
        }
    return _plugin_types
