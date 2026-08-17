"""
Enumerated data types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Never, final

from betty.assertions.enum import assert_enum
from betty.data import DataDefinition
from betty.portable import Porter
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class EnumDefinition[EnumT: Enum[bool | int | float | str]](
    DataDefinition[EnumT, Never, Porter[EnumT]]
):
    """
    An enum data definition.
    """

    def __init__(
        self,
        *,
        cls: type[EnumT],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            porter=CallbackPorter(assert_enum(cls), lambda enum: enum.value),
        )
