"""
Validators that always do the same thing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, overload

from betty.functools import Pipe, raise_
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import ResolvableLocalizable
    from betty.user.location import Locator


@final
class AlwaysInvalid(Invalid):
    """
    Raised when a value is always invalid.
    """

    def __init__(
        self,
        value: Any,
        /,
        *,
        message: ResolvableLocalizable = "This is always invalid.",
        location: Iterable[Locator] = (),
    ):
        super().__init__(value, location=location, message=message)


@overload
def is_always_invalid[ValueT](
    *,
    message: ResolvableLocalizable | None = None,
    location: Iterable[Locator] = (),
) -> Pipe[Any, ValueT]:
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
    return Pipe(lambda value: raise_(AlwaysInvalid(value, **kwargs)))


def is_always_valid[ValueT](value: ValueT) -> ValueT:
    """
    Validate a value, but always consider it valid.
    """
    return value
