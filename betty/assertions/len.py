"""
Length assertions.
"""

from __future__ import annotations

from collections.abc import Sized

from betty.assertions import _HumanFacingValueError
from betty.functools import Pipeline
from betty.locale.localizable.gettext import _


def assert_len[SizedT: Sized](
    exact: int | None = None, *, minimum: int | None = None, maximum: int | None = None
) -> Pipeline[SizedT, SizedT]:
    """
    Assert the length of a value.

    This assertion can be used in two ways:
    - with an exact required length
    - with minimum and/or maximum bounds (inclusive)
    """

    def _assert_len(value: SizedT, /) -> SizedT:
        actual = len(value)
        if exact is not None and actual != exact:
            raise _HumanFacingValueError(
                _("Exactly {expected} items are required, but found {actual}.").format(
                    expected=str(exact), actual=str(actual)
                )
            )
        if minimum is not None and actual < minimum:
            raise _HumanFacingValueError(
                _("At least {expected} items are required, but found {actual}.").format(
                    expected=str(minimum), actual=str(actual)
                )
            )
        if maximum is not None and actual > maximum:
            raise _HumanFacingValueError(
                _("At most {expected} items are allowed, but found {actual}.").format(
                    expected=str(maximum), actual=str(actual)
                )
            )
        return value

    return Pipeline(_assert_len)
