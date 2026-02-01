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

from typing_extensions import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name
from betty.plugin.cls import PluginClsDefinition

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Mapping, MutableSequence

    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.plugin.discovery import PluginDiscovery


class PluginDefinition:
    """
    A plugin definition.
    """

    def __init__(self, plugin_id: MachineName, /):
        super().__init__()
        if not validate_machine_name(plugin_id):
            raise InvalidMachineName(plugin_id)
        self._id = plugin_id

    @classmethod
    def type(cls) -> PluginTypeDefinition[Self]:
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
_PluginClsDefinitionT = TypeVar(
    "_PluginClsDefinitionT", bound=PluginClsDefinition, default=PluginClsDefinition
)


@final
class PluginTypeDefinition(
    CountableHumanFacingDefinition, ClsDefinition[_PluginDefinitionT]
):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        id: MachineName,  # noqa: A002
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        discovery: Collection[PluginDiscovery[_PluginDefinitionT]]
        | PluginDiscovery[_PluginDefinitionT]
        | None = None,
    ):
        from betty.plugin.discovery import PluginDiscovery

        super().__init__(
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )

        if not validate_machine_name(id):
            raise InvalidMachineName(id)
        self._id = id
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

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @override
    def _set_cls(self, cls: type[_PluginDefinitionT]) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]

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
        try:
            yield
        finally:
            self._active_discovery = self._defined_discovery

    @property
    def discovery_overridden(self) -> bool:
        """
        Whether the discoveries are currently overridden.
        """
        return self._defined_discovery != self._active_discovery


class Plugin(Generic[_PluginClsDefinitionT]):
    """
    A plugin class.

    ``__init__()`` is considered private to the :py:mod:`factory <betty.factory>` API. That means you MUST use the
    factory API to create new instances.
    """

    @classmethod
    def plugin(cls) -> _PluginClsDefinitionT:
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
