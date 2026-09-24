from typing import TYPE_CHECKING

from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from ty_extensions import Intersection

type ClassedPluginDefinition[PluginT] = Intersection[
    PluginDefinition, ClsDefinition[PluginT]
]
