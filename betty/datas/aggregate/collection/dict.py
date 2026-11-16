"""
Dictionary data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.collections.mapping.dict import Dict, empty_frozen_dict
from betty.datas.aggregate.collection.mapping import MutableMappingDefinition

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizer import AnyLocalizable
    from betty.portable import Porter


@final
class DictDefinition[KeyT, ValueT](
    MutableMappingDefinition[Dict[KeyT, KeyT, ValueT, ValueT], KeyT, ValueT]
):
    """
    A :py:class`betty.collections.mapping.dict.Dict` definition.
    """

    def __init__(
        self,
        *,
        key: ResolvableDataDefinition[DataDefinition[KeyT]],
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        porter: Porter[Dict[KeyT, KeyT, ValueT, ValueT]] | None = None,
    ):
        super().__init__(
            key=key,
            value=value,
            label=label,
            description=description,
            manufacturer=lambda values: Dict(values or empty_frozen_dict),
            porter=porter,
        )
