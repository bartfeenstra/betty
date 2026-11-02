"""
Enumerated data types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, final

from betty.assertions.enum import assert_enum
from betty.data import DataDefinition
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
class EnumDefinition[EnumT: Enum](DataDefinition[EnumT]):
    """
    An enum data definition.
    """

    def __init__(
        self,
        cls: type[EnumT],
        /,
        *,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter(assert_enum(cls), lambda enum: enum.value),
        )
