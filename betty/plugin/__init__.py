"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Self, final, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, ResolvableMachineName

if TYPE_CHECKING:
    import builtins
    from collections.abc import Collection, Iterable

    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.plugin.discovery import ResolvableDiscovery


class PluginDefinition[BaseClsT](ClsDefinition[BaseClsT]):
    """
    A plugin definition.
    """

    def __init__(self, plugin_id: ResolvableMachineName, /):
        super().__init__()
        self._id = MachineName.resolve(plugin_id)

    @classmethod
    def type(cls) -> PluginTypeDefinition[BaseClsT, Self]:
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

    @override
    def _set_cls(self, cls: builtins.type[BaseClsT]) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]

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


@final
class PluginTypeDefinition[BaseClsT, PluginDefinitionT: PluginDefinition](
    CountableHumanFacingDefinition, ClsDefinition[PluginDefinitionT]
):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        plugin_type_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        discovery: Iterable[ResolvableDiscovery[PluginDefinitionT]] | None = None,
    ):
        super().__init__(
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )

        self._id = MachineName.resolve(plugin_type_id)
        self._discovery = () if discovery is None else tuple(discovery)

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @override
    def _set_cls(self, cls: type[PluginDefinitionT]) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]

    @property
    def discovery(self) -> Collection[ResolvableDiscovery[PluginDefinitionT]]:
        """
        The plugin discoveries for this type.
        """
        return self._discovery


class Plugin[PluginDefinitionT: PluginDefinition]:
    """
    A plugin class.
    """

    @classmethod
    def plugin(cls) -> PluginDefinitionT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )


type ResolvableDefinition[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    PluginDefinitionT | type[Plugin[PluginDefinitionT]]
)
"""
Use :py:func:`betty.plugin.resolve.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""


type ResolvableId[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    ResolvableMachineName | ResolvableDefinition[PluginDefinitionT]
)
"""
Use :py:func:`betty.plugin.resolve.resolve_id` to resolve this to a plugin ID.
"""


def resolve_definition[PluginDefinitionT: PluginDefinition](
    definition: ResolvableDefinition[PluginDefinitionT], /
) -> PluginDefinitionT:
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition  # ty:ignore[invalid-return-type]
    return definition.plugin()


def resolve_id(plugin_id: ResolvableId, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, MachineName):
        return plugin_id
    if isinstance(plugin_id, str):
        return MachineName.resolve(plugin_id)
    return resolve_definition(plugin_id).id
