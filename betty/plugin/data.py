"""
Data plugins.
"""

from __future__ import annotations

from betty.capability import Stage
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.cls import ClsDefinitionCapabilityStage
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.portable import Porter
from betty.search import RecordIndexer
from betty.typing import Intersection


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
    IndexerT: RecordIndexer = RecordIndexer,
](PluginClsDefinition[ClsT, StageT], ObjectDefinition[ClsT, StageT, PorterT, IndexerT]):
    """
    A data plugin definition.
    """
