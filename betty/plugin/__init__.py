"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import update_wrapper
from importlib import metadata
from typing import TYPE_CHECKING, Any, Final, Generic, Self, final

from typing_extensions import TypeVar

from betty.importlib import fully_qualified_name
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name

if TYPE_CHECKING:
    import builtins
    from collections.abc import Collection, Iterator, Mapping, MutableSequence

    from ty_extensions import Intersection

    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        LocalizableLike,
    )
    from betty.plugin.discovery import PluginDiscovery


_BaseClsCoT = TypeVar("_BaseClsCoT", default=object, covariant=True)


class PluginDefinition(Generic[_BaseClsCoT]):
    """
    A plugin definition.
    """

    def __init__(self, plugin_id: MachineName, /):
        if not validate_machine_name(plugin_id):
            raise InvalidMachineName(plugin_id)
        self._id = plugin_id
        self._cls: type[Intersection[_BaseClsCoT, Plugin[Self]]] | None = None

    @classmethod
    def type(cls) -> PluginTypeDefinition[_BaseClsCoT, Self]:
        """
        The plugin type definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )

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
    def cls(self) -> builtins.type[Intersection[_BaseClsCoT, Plugin[Self]]]:
        """
        The plugin class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """
        if self._cls is None:
            raise ValueError("This definition was not yet used to decorate a class.")
        assert self._cls is not None
        return self._cls

    def __call__(
        self, cls: builtins.type[Intersection[_BaseClsCoT, Plugin[Self]]]
    ) -> builtins.type[Intersection[_BaseClsCoT, Plugin[Self]]]:
        """
        Decorate a plugin class.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        if self._cls is not None:
            raise ValueError("This definition was already used to decorate a class.")
        assert self._cls is None
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))
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
            plugin_type=self.type().label,
            plugin_id=self.id,
        )


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
class PluginTypeDefinition(Generic[_BaseClsCoT, _PluginDefinitionT]):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        id: MachineName,  # noqa: A002
        *,
        base_cls: type[Intersection[_BaseClsCoT, Plugin[_PluginDefinitionT]]],
        label: LocalizableLike,
        label_plural: LocalizableLike,
        label_countable: CountableLocalizable,
        description: LocalizableLike | None = None,
        discovery: Collection[PluginDiscovery[_PluginDefinitionT]]
        | PluginDiscovery[_PluginDefinitionT]
        | None = None,
    ):
        from betty.plugin.discovery import PluginDiscovery

        if not validate_machine_name(id):
            raise InvalidMachineName(id)
        self._id = id
        self._base_cls = base_cls
        self._label = ensure_localizable(label)
        self._label_plural = ensure_localizable(label_plural)
        self._label_countable = label_countable
        self._description = (
            None if description is None else ensure_localizable(description)
        )
        if discovery is None:
            discovery = []
        elif isinstance(discovery, PluginDiscovery):
            discovery = [discovery]  # ty:ignore[invalid-assignment]
        else:
            discovery = list(
                discovery,  # ty:ignore[invalid-argument-type]
            )
        self._defined_discovery: MutableSequence[
            PluginDiscovery[_PluginDefinitionT]
        ] = discovery
        self._active_discovery: Collection[PluginDiscovery[_PluginDefinitionT]] = (
            self._defined_discovery
        )
        self._cls: type[_PluginDefinitionT] | None = None

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @property
    def base_cls(self) -> type[Intersection[_BaseClsCoT, Plugin[_PluginDefinitionT]]]:
        """
        The base class all plugins of this type must subclass.
        """
        return self._base_cls

    @property
    def cls(self) -> type[_PluginDefinitionT]:
        """
        The plugin definition class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """
        if self._cls is None:
            raise ValueError("This definition was not yet used to decorate a class.")
        assert self._cls is not None
        return self._cls

    def __call__(self, cls: type[_PluginDefinitionT]) -> type[_PluginDefinitionT]:
        """
        Decorate a plugin class.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        if self._cls is not None:
            raise ValueError("This definition was already used to decorate a class.")
        assert self._cls is None
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]
        self._cls = cls
        return cls

    @property
    def label(self) -> Localizable:
        """
        The plugin type label.
        """
        return self._label

    @property
    def label_plural(self) -> Localizable:
        """
        The human-readable short plugin type label (plural).
        """
        return self._label_plural

    @property
    def label_countable(self) -> CountableLocalizable:
        """
        The human-readable short plugin type label (countable).
        """
        return self._label_countable

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long plugin type description.
        """
        return self._description

    @property
    def discovery(
        self,
    ) -> Collection[PluginDiscovery[_PluginDefinitionT]]:
        """
        The plugin discoveries for this type.
        """
        return self._active_discovery

    def add_discovery(self, *discoveries: PluginDiscovery[_PluginDefinitionT]) -> None:
        """
        Add a plugin discovery for this type.
        """
        self._defined_discovery.extend(discoveries)

    @contextmanager
    def override_discovery(
        self, *discoveries: PluginDiscovery[_PluginDefinitionT]
    ) -> Iterator[None]:
        """
        Temporarily override the discoveries for this plugin type with the given plugins.
        """
        self._active_discovery = discoveries
        yield
        self._active_discovery = self._defined_discovery

    @property
    def discovery_overridden(self) -> bool:
        """
        Whether the discoveries are currently overridden.
        """
        return self._defined_discovery != self._active_discovery


class Plugin(Generic[_PluginDefinitionCoT]):
    """
    A plugin class.

    ``__init__()`` is considered private to the :py:mod:`factory <betty.factory>` API. That means you MUST use the
    factory API to create new instances.
    """

    @classmethod
    def plugin(cls) -> _PluginDefinitionCoT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )


_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)


@final
class PluginTypeRepository:
    """
    A repository of available plugin types.
    """

    def __init__(self):
        self._plugin_types: Mapping[MachineName, type[PluginDefinition]] | None = None

    def _get_plugin_types(self) -> Mapping[MachineName, type[PluginDefinition]]:
        if self._plugin_types is None:
            self._plugin_types = {
                plugin.type().id: plugin
                for entry_point in metadata.entry_points(group="betty.plugin")
                if (plugin := entry_point.load())
            }
        return self._plugin_types

    def __contains__(self, value: Any) -> bool:
        return value in self._get_plugin_types()

    def __getitem__(self, plugin_type_id: MachineName, /) -> type[PluginDefinition]:
        return self._get_plugin_types()[plugin_type_id]

    def __iter__(self) -> Iterator[type[PluginDefinition]]:
        return iter(self._get_plugin_types().values())


plugin_types: Final[PluginTypeRepository] = PluginTypeRepository()
"""
The available plugin types.
"""
