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

    def __init__(self, proxied: DataDefinition[DataClsT], /):
        super().__init__(
            cls=proxied.cls,
            label=proxied.label,
            description=proxied.description,
            porter=OptionalPorter(proxied.porter),  # ty:ignore[invalid-argument-type]
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                proxied.samples,
            ],
        )
