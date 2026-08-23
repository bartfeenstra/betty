"""
Data plugins.
"""

from __future__ import annotations

from ty_extensions import Intersection

from betty.capability import Stage
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.cls import ClsDefinitionCapabilityStage
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.portable import Porter


class DataPlugin[
    DefinitionT: Intersection[DataDefinition, PluginClsDefinition],
](Plugin[DefinitionT], Data[DefinitionT]):
    """
    A data plugin.
    """


class DataPluginDefinition[
    ClsT: Intersection[Data, Plugin],
    StageT: Stage = ClsDefinitionCapabilityStage,
    PorterT: Porter = Porter,
](PluginClsDefinition[ClsT, StageT], ObjectDefinition[ClsT, StageT, PorterT]):
    """
    A data plugin definition.
    """
