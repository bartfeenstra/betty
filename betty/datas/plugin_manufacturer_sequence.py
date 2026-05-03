"""
Plugin manufacturer sequence data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableResolvedSequence
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.datas.aggregate.collection.sequence import SequenceDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin.factory import PluginManufacturer


@final
class PluginManufacturerSequenceDefinition(SequenceDefinition):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        manufacturer: type[PluginManufacturer],
        *,
        label: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=MutableResolvedSequence,
            factory=lambda: MutableResolvedSequenceAdapter(
                [], value_resolver=manufacturer.resolve
            ),
            value=manufacturer,
            label=manufacturer.plugin_type().type().label_plural
            if label is None
            else label,
        )
