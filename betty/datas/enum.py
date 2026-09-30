"""
Enumerated data types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.porters.callback import CallbackPorter
from betty.validators.enum import is_enum

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


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
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter(is_enum(cls), lambda enum: enum.value),
        )
