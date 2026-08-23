"""
List data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.datas.aggregate.collection.sequence import MutableSequenceDefinition

if TYPE_CHECKING:
    from betty.data import DataDefinition, ResolvableDataDefinition
    from betty.localizable import ResolvableLocalizable


@final
class ListDefinition[ValueT](MutableSequenceDefinition[list[ValueT], ValueT]):
    """
    A list definition.
    """

    def __init__(
        self,
        *,
        value: ResolvableDataDefinition[DataDefinition[ValueT]],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            value=value,
            label=label,
            description=description,
            manufacturer=lambda values: [] if values is None else list(values),
        )
