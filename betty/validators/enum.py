"""
Enum data validators.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from betty.localizables.markup import do_you_mean
from betty.pipeline import Inlet, Pipeline
from betty.validators.option import UnknownOption


def is_enum[EnumT: Enum](options: type[EnumT], /) -> Pipeline[Any, EnumT]:
    """
    Validate that a value is allowed by an enum, and return the enum value.
    """

    def _is_enum(value: Any) -> Any:
        try:
            return options(value)
        except ValueError:
            raise UnknownOption(
                value, hint=do_you_mean(*(str(option.value) for option in options))
            ) from None

    return Inlet(_is_enum)
