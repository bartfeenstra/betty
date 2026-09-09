"""
Dictionary data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.datas.aggregate.collection.mapping import MutableMappingDefinition

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import Porter


@final
class DictDefinition[KeyT, ValueT](
    MutableMappingDefinition[dict[KeyT, ValueT], KeyT, ValueT]
):
    """
    A dictionary definition.
    """

    def __init__(
        self,
        *,
        key: ResolvableDataDefinition[DataDefinition[KeyT]],
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[dict[KeyT, ValueT]] | None = None,
    ):
        super().__init__(
            key=key,
            value=value,
            label=label,
            description=description,
            factory=lambda values: dict(values) if values else {},
            porter=porter,
        )
