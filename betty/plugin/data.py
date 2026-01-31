"""
Data types for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.data import DataDefinition, Sample, Size
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record import (
    FieldDefinition,
)
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.functools import passthrough
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.config import PluginConfiguration, _PluginDefinitionT
from betty.portable import CallbackPorter

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin import PluginDefinition
    from betty.service.level import ServiceLevel


@final
class PluginIdDefinition(DataDefinition[MachineName]):
    """
    Define data that represents a plugin ID.
    """

    def __init__(self, plugin_type: type[PluginDefinition] | None = None):
        super().__init__(
            cls=MachineName,
            label=_("Plugin ID") if plugin_type is None else plugin_type.type().label,
            description=None if plugin_type is None else _("Plugin ID"),
            porter=CallbackPorter[str](assert_machine_name(), passthrough),
        )
        self._plugin_type = plugin_type

    @override
    async def hydrate(self, services: ServiceLevel, data: MachineName, /) -> None:
        if self._plugin_type is not None:
            (await services.plugins(self._plugin_type)).get(data)


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
                FieldDefinition(Attr("id"), PluginIdDefinition(plugin_type)),
                FieldDefinition(
                    Attr("configuration"),
                    DataDefinition(cls=object, label=_("Plugin configuration")),
                ),
            ],
            samples=[
                lambda: Sample(
                    PluginConfiguration("my-first-plugin-id"),
                    label="Minimal",
                    size=Size.MINIMAL,
                ),
                lambda: Sample(
                    PluginConfiguration(
                        "my-first-plugin-id",
                        {
                            "configuration-key": "configuration-value",
                        },
                    ),
                    label="Full",
                    size=Size.FULL,
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
            cls=list,
            value=PluginConfigurationDefinition(plugin_type),
            label=plugin_type.type().label_plural if label is None else label,
        )
