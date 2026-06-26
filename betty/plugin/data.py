"""
Data plugins.
"""

from __future__ import annotations

from betty.data import Data, DataDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.typing import Intersection


class DataPlugin[
    DefinitionT: Intersection[DataDefinition, PluginClsDefinition],
](Plugin[DefinitionT], Data[DefinitionT]):
    """
    A data plugin.
    """


class DataPluginDefinition[ClsT: Intersection[Data, Plugin]](
    PluginClsDefinition[ClsT], DataDefinition[ClsT]
):
    """
    A data plugin definition.
    """
