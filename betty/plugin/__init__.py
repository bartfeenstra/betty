"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib import metadata
from typing import TYPE_CHECKING, ClassVar, Generic, Self, final

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

    ``__init__()`` is considered private except to the :py:mod:`factory <betty.factory>` API. That means you MUST use the
    factory API to create new instances, unless you are the owner of the class.
    """

    plugin: ClassVar[PluginDefinition[Self]]


_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)


class PluginDefinition(Generic[_PluginT]):
    """
    A plugin definition.
    """

    type: ClassVar[PluginTypeDefinition[Self]]

    def __init__(
        self,
        id: MachineName,  # noqa A002
        cls: builtins.type[_PluginT] | None = None,
        /,
    ):
        if not validate_machine_name(id):  # type: ignore[redundant-expr]
            raise InvalidMachineName(id)
        self._id = id
        self._cls = cls
        if cls is not None:
            self._set_cls(cls)

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
    def cls(self) -> type[_PluginT]:
        """
        The plugin class.
        """
        assert self._cls is not None
        return self._cls

    def _set_cls(self, cls: type[_PluginT]) -> None:
        cls.plugin = self  # type: ignore[attr-defined]

    def __call__(self, cls: type[_PluginT]) -> type[_PluginT]:
        """
        Set the plugin's class.
        """
        assert self._cls is None
        self._set_cls(cls)
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
class PluginTypeDefinition(Generic[_PluginDefinitionT, _PluginT]):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        id: MachineName,  # noqa A002
        cls: type[_PluginT],
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
        self._cls = cls
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
    def cls(self) -> type[_PluginT]:
        """
        The plugin type's shared base class'.
        """
        return self._cls

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
