"""
Optional data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.portable import OptionalPorter, PortableData
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.typing import Intersection


@final
class OptionalDefinition[
    DataDefinitionT: DataDefinition,
    DataClsT,
    PortableDataT: PortableData,
](DataDefinition[DataClsT | None, PortableDataT | None]):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(
        self,
        wrapped: Intersection[DataDefinition[DataClsT, PortableDataT], DataDefinitionT],
        /,
    ):
        super().__init__(
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            porter=OptionalPorter(wrapped.porter),
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                wrapped.samples,
            ],
        )
