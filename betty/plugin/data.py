"""
Data plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition

if TYPE_CHECKING:
    from ty_extensions import Intersection


class DataPlugin[
    DefinitionT: Intersection[DataDefinition, PluginClsDefinition],
](Plugin[DefinitionT], Data[DefinitionT]):
    """
    A data plugin.
    """


class DataPluginDefinition[ClsT: Intersection[Data, Plugin]](
    PluginClsDefinition[ClsT], ObjectDefinition[ClsT]
):
    """
    A data plugin definition.
    """
