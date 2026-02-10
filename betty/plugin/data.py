"""
Data types for plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections import MutableResolvedSequence, MutableResolvedSequenceProxy
from betty.data.aggregate.collection.sequence import SequenceDefinition

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
            factory=lambda values: MutableResolvedSequenceProxy(
                list(values), value_resolver=manufacturer.resolve
            ),
            value=manufacturer,
            label=manufacturer.type().type().label_plural if label is None else label,
        )
