"""
Plugin definition data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from betty.attrs.machine_name import new_machine_name_attr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.locale.localizable.gettext import _
from betty.plugin import PluginDefinition
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName


class PluginDefinitionData[PluginDefinitionT: PluginDefinition = PluginDefinition](
    Data[ObjectDefinition["PluginDefinitionData"]], HasProps, ABC
):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.

    .. data:: betty.datas.plugin_definition:PluginDefinitionData
    """

    id = new_machine_name_attr(label=_("Plugin ID"))
    """
    The plugin ID.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName,  # noqa: A002
    ):
        super().__init__()
        self.id = id

    @abstractmethod
    def new_plugin(self) -> PluginDefinitionT:
        """
        Create a new plugin from this configuration.
        """
