"""
Data plugins.
"""

from __future__ import annotations

from betty.capability import Stage
from betty.data import Data, DataDefinition, DataDefinitionCapabilityStage
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.cls import ClsDefinitionCapabilityStage
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
    StageT: Stage = DataDefinitionCapabilityStage,
](
    PluginClsDefinition[
        ClsT, StageT | DataDefinitionCapabilityStage | ClsDefinitionCapabilityStage
    ],
    ObjectDefinition[
        ClsT,
        PorterT,
        StageT | DataDefinitionCapabilityStage | ClsDefinitionCapabilityStage,
    ],
):
    """
    A data plugin definition.
    """
