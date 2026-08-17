"""
Integer data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, final

from betty.assertions.int import assert_int
from betty.data import DataDefinition
from betty.portable import Porter
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class IntDefinition(DataDefinition[int, Never, Porter[int]]):
    """
    An integer data definition.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=int,
            label=label,
            description=description,
            porter=CallbackPorter[int](assert_int(), int),
        )
