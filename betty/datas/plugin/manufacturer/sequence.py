"""
Plugin manufacturer sequence data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableBettySequence
from betty.collections.sequence.list import List
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition
from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.localizable import ResolvableLocalizable


@final
class PluginManufacturerSequenceDefinition[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    PluginManufacturerT: PluginManufacturer,
](
    SequenceDefinition[
        MutableBettySequence[
            PluginManufacturerT,
            ResolvablePluginManufacturer[DefinitionT, PluginManufacturerT],
        ],
        PluginManufacturerT,
    ]
):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        manufacturer: type[PluginManufacturerT],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            manufacturer=lambda values: List[
                PluginManufacturerT,
                ResolvablePluginManufacturer[DefinitionT, PluginManufacturerT],
            ](values, value=manufacturer.resolve),
            value=manufacturer,
            label=manufacturer.definition.plugin_type.definition.label_plural
            if label is None
            else label,
            description=description,
        )
