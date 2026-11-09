"""
Integer data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.assertions.int import assert_int
from betty.data import PortableDataDefinitionBase
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
class IntDefinition(PortableDataDefinitionBase[int]):
    """
    An integer data definition.
    """

    def __init__(
        self, *, label: AnyLocalizable, description: AnyLocalizable | None = None
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter[int](assert_int(), int),
        )
