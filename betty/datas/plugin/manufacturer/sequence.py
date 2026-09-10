"""
Plugin manufacturer sequence data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableResolvedSequence
from betty.collections.sequence.list import ResolvedList
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.plugin.cls import (
    ClassedPluginDefinition,
    PluginManufacturer,
    ResolvablePluginManufacturer,
)

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class PluginManufacturerSequenceDefinition[
    PluginDefinitionT: ClassedPluginDefinition,
    PluginManufacturerT: PluginManufacturer,
](
    SequenceDefinition[
        MutableResolvedSequence[
            PluginManufacturerT,
            ResolvablePluginManufacturer[PluginDefinitionT, PluginManufacturerT],
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
            cls=MutableResolvedSequence,
            manufacturer=lambda values: ResolvedList(
                values, value_resolver=manufacturer.resolve
            ),  # ty: ignore[invalid-argument-type]
            value=manufacturer,  # ty: ignore[invalid-argument-type]
            label=manufacturer.data().plugin_type.type().label_plural
            if label is None
            else label,
            description=description,
        )
