"""
Enumerated data types.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, TypeVar, final

from betty.data import DataDefinition
from betty.portable import CallbackPorter

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable

_EnumT = TypeVar("_EnumT", bound=Enum)


@final
class EnumDefinition(DataDefinition[_EnumT]):
    """
    An enum data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_EnumT],
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        from betty.assertion import assert_enum

        super().__init__(
            cls=cls,
            label=label,
            description=description,
            porter=CallbackPorter(assert_enum(cls), lambda enum: enum.value),
        )
