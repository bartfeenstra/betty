"""
Data types for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import TypeVar, override

from betty.data import DataDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.functools import passthrough
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.portable import CallbackPorter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.plugin import Plugin, PluginDefinition, _BaseClsCoT
    from betty.service.level import ServiceLevel

_DataT = TypeVar("_DataT")


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
            porter=CallbackPorter[str](assert_machine_name(), passthrough),
        )
        self._plugin_type = plugin_type

    @override
    async def hydrate(self, services: ServiceLevel, data: MachineName, /) -> None:
        (await services.plugins(self._plugin_type)).get(data)


class DataPluginDefinition(HumanFacingPluginDefinition[_DataT]):
    """
    A definition of plugin that can declare its order with respect to other plugins.
    """

    @override
    def _set_cls(self, cls: type[Intersection[_BaseClsCoT, Plugin[Self]]]) -> None:
        super()._set_cls(cls)
        ObjectDefinition(label=self.label, description=self.description)(cls)
