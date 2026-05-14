"""
Optional data.
"""

from __future__ import annotations

from typing import final

from betty.data import DataDefinition
from betty.portable import OptionalPorter
from betty.sample import Sample, Size


@final
class OptionalDefinition[DataClsT](DataDefinition[DataClsT | None]):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(self, wrapped: DataDefinition[DataClsT], /):
        super().__init__(
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            porter=OptionalPorter(wrapped.porter),  # ty:ignore[invalid-argument-type]
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                wrapped.samples,
            ],
        )
        self._wrapped = wrapped

    @property
    def wrapped(self) -> DataDefinition[DataClsT]:
        """
        The wrapped, required (non-optional) data definition.
        """
        return self._wrapped
