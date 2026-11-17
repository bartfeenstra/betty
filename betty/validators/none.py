"""
``None`` validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, overload

from betty.localizables.gettext import _
from betty.pipeline import Inlet, Pipeline
from betty.validators import InvalidValue
from betty.validators.group import is_any

if TYPE_CHECKING:
    from betty.validation import Validator


@final
class NotNone(InvalidValue):
    """
    Raised when a value is not ``None``.
    """

    _message = _("This must be none/null.")


@Inlet
def is_none(value: Any, /) -> None:
    """
    Validate that a value is ``None``.
    """
    if value is not None:
        raise NotNone(value)
    return


@overload
def is_optional[T](value: Any, validator: Validator[Any, T], /) -> T | None:
    pass


@overload
def is_optional[T](validator: Validator[Any, T], /) -> Pipeline[Any, T | None]:
    pass


def is_optional(*args):
    """
    Validate that a value can be validated by another validator, or is ``None``.
    """
    if len(args) == 2:
        return is_any(is_none, args[1])(args[0])
    return is_any(is_none, args[0])
