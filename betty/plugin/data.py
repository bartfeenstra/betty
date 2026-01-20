"""
Data types for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.data import DataDefinition
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.functools import passthrough
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.config import PluginInstanceConfiguration
from betty.portable import CallbackPorter

if TYPE_CHECKING:
    from betty.plugin import PluginDefinition
    from betty.service.level import ServiceLevel


@final
class PluginIdDefinition(DataDefinition[MachineName]):
    """
    Define data that represents a plugin ID.
    """

    def __init__(self, plugin_type: type[PluginDefinition]):
        super().__init__(
            cls=MachineName,
            label=plugin_type.type().label,
            description=_("A plugin ID"),
            porter=CallbackPorter(assert_machine_name(), passthrough),
        )
        self._plugin_type = plugin_type

    @override
    async def hydrate(self, data: MachineName, services: ServiceLevel, /) -> None:
        (await services.plugins(self._plugin_type)).get(data)


@final
class PluginInstanceConfigurationDefinition(ObjectDefinition):
    """
    Define :py:class:`betty.plugin.config.PluginInstanceConfiguration`.
    """

    def __init__(self, plugin_type: type[PluginDefinition], /):
        super().__init__(
            cls=PluginInstanceConfiguration,
            label=_("{plugin_type} configuration").format(
                plugin_type=plugin_type.type().label
            ),
            fields=[
                FieldDefinition(Attr("id"), PluginIdDefinition(plugin_type)),
                FieldDefinition(Attr("configuration"), DataDefinition(cls=object, label=_("Plugin configuration"))),
            ],
        )
