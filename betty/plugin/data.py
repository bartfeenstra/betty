"""
Data plugins.
"""

from __future__ import annotations

from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.portable import Porter
from betty.typing import Intersection


class DataPlugin[
    DefinitionT: Intersection[DataDefinition, PluginClsDefinition],
](Plugin[DefinitionT], Data[DefinitionT]):
    """
    A data plugin.
    """


class DataPluginDefinition[
    ClsT: Intersection[Data, Plugin],
    PorterT: Porter = Porter,
](PluginClsDefinition[ClsT], ObjectDefinition[ClsT, PorterT]):
    """
    A data plugin definition.
    """
