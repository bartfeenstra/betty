"""
Plugin manufacturer sequence data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableResolvedSequence
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.plugin.cls import PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class PluginManufacturerSequenceDefinition[
    PluginDefinitionT: PluginClsDefinition,
    PluginT,
](
    SequenceDefinition[
        MutableResolvedSequence[
            PluginManufacturer[PluginDefinitionT, PluginT],
            ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
        ],
        PluginManufacturer[PluginDefinitionT, PluginT],
    ]
):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        manufacturer: type[
            PluginManufacturer[
                PluginDefinitionT,
                PluginT,
            ]
        ],
        *,
        label: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=MutableResolvedSequence,
            factory=lambda: MutableResolvedSequenceAdapter(
                [], value_resolver=manufacturer.resolve
            ),
            value=manufacturer,
            label=manufacturer.data().plugin_type.type().label_plural
            if label is None
            else label,
        )
