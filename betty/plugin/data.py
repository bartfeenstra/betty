"""
Data types for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar

from betty.collections import MutableResolvedSequence, MutableResolvedSequenceProxy
from betty.data import DataDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.config import PluginConfiguration, resolve_plugin_configuration

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class PluginConfigurationDefinition(ObjectDefinition):
    """
    Define data for :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    def __init__(self, plugin_type: type[PluginDefinition], /):
        super().__init__(
            cls=PluginConfiguration,
            label=_("{plugin_type} configuration").format(
                plugin_type=plugin_type.type().label
            ),
            fields=[
                FieldDefinition(Attr("id"), MachineName),
                FieldDefinition(
                    Attr("configuration"),
                    DataDefinition(cls=object, label=_("Plugin configuration")),
                ),
            ],
        )


@final
class PluginConfigurationSequenceDefinition(SequenceDefinition):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
        *,
        label: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=MutableResolvedSequence,
            factory=lambda values: MutableResolvedSequenceProxy(
                list(values), value_resolver=resolve_plugin_configuration
            ),
            value=PluginConfigurationDefinition(plugin_type),
            label=plugin_type.type().label_plural if label is None else label,
        )
