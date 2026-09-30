"""
Length validators.
"""

from __future__ import annotations

from collections.abc import Sized

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.validation import Invalid, group


def is_len[SizedT: Sized](
    exact: int | None = None,
    /,
    *,
    min: int | None = None,  # noqa: A002
    max: int | None = None,  # noqa: A002
) -> Pipeline[SizedT, SizedT]:
    """
    Validate the length of a value.

    This validator can be used in two ways:
    - with an exact required length
    - with minimum and/or maximum bounds (inclusive)
    """

    @group()
    def _is_len(value: SizedT, /) -> SizedT:
        actual = len(value)
        if exact is not None and actual != exact:
            raise Invalid(
                _("Exactly {expected} items are required, but found {actual}.").format(
                    expected=str(exact), actual=str(actual)
                )
            )
        if min is not None and actual < min:
            raise Invalid(
                _("At least {expected} items are required, but found {actual}.").format(
                    expected=str(min), actual=str(actual)
                )
            )
        if max is not None and actual > max:
            raise Invalid(
                _("At most {expected} items are allowed, but found {actual}.").format(
                    expected=str(max), actual=str(actual)
                )
            )
        return value

    return Pipeline(_is_len)
