"""
Plugin manufacturer sequence data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collection.sequence import MutableResolvedSequence
from betty.collections.sequence.list import ResolvedList
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.definition.cls import ClsDefinition
from betty.plugin.cls.factory import NewPlugin

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class NewPluginSequenceDefinition[
    DefinitionT: ClsDefinition,
    NewPluginT: NewPlugin,
](
    SequenceDefinition[
        MutableResolvedSequence[
            NewPluginT,
            ResolvablePluginManufacturer[DefinitionT, NewPluginT],
        ],
        NewPluginT,
    ]
):
    """
    Define a sequence of plugin instance configurations.
    """

    def __init__(
        self,
        manufacturer: type[NewPluginT],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            manufacturer=lambda values: ResolvedList[
                NewPluginT,
                ResolvablePluginManufacturer[DefinitionT, NewPluginT],
            ](values, value_resolver=manufacturer.resolve),
            value=manufacturer,
            label=manufacturer.definition.plugin_type.definition.label_plural
            if label is None
            else label,
            description=description,
        )
