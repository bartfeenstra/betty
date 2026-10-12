"""
Validators that always do the same thing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, overload

from betty.functools import raise_
from betty.pipeline import Inlet, Pipeline
from betty.validators import InvalidValue

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.location import ResolvableLocation


@final
class AlwaysInvalid(InvalidValue):
    """
    Raised when a value is always invalid.
    """

    _message = "This is always invalid."


@overload
def is_always_invalid[ValueT](
    *, message: ResolvableLocalizable | None = None, at: ResolvableLocation = ()
) -> Pipeline[Any, ValueT]:
    pass


@overload
def is_always_invalid[ValueT](value: Any, /) -> ValueT:
    pass


def is_always_invalid(*value_, **kwargs):
    """
    Validate a value, but always consider it invalid.
    """
    if value_:
        raise AlwaysInvalid(*value_, **kwargs)
    return Inlet(lambda value: raise_(AlwaysInvalid(value, **kwargs)))


def is_always_valid[ValueT](value: ValueT) -> ValueT:
    """
    Validate a value, but always consider it valid.
    """
    return value
