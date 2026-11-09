"""
Boolean data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.assertions.bool import assert_bool
from betty.data import PortableDataDefinitionBase
from betty.pipeline import pipe
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
class BoolDefinition(PortableDataDefinitionBase[bool]):
    """
    A boolean data definition.
    """

    def __init__(
        self, *, label: AnyLocalizable, description: AnyLocalizable | None = None
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter(assert_bool, pipe),
        )
