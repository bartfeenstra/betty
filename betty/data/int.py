"""
Integer data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.assertion import assert_int
from betty.data import DataDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class IntDefinition(DataDefinition[int]):
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
            porter=CallbackPorter(assert_int(), passthrough),  # ty:ignore[invalid-argument-type]
        )
