"""
Conditional assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError
from betty.functools import Pipe, Pipeline
from betty.locale.localizable import Localizable, ResolvableLocalizable
from betty.locale.localizable.markup import Paragraphs

if TYPE_CHECKING:
    from collections.abc import MutableSequence


def assert_if_else[ValueT, ReturnT, AssertionReturnU](
    if_assertion: Pipe[ValueT, ReturnT],
    else_assertion: Pipe[ValueT, AssertionReturnU],
    /,
) -> Pipeline[ValueT, ReturnT | AssertionReturnU]:
    """
    Assert that at least one of the given assertions passes.
    """

    def _assert_or(value: Any, /) -> ReturnT | AssertionReturnU:
        assertions = (if_assertion, else_assertion)
        errors: MutableSequence[ResolvableLocalizable] = []
        for assertion in assertions:
            try:
                return assertion(value)
            except Exception as error:
                errors.append(error if isinstance(error, Localizable) else str(error))
        raise _HumanFacingValueError(Paragraphs(*errors))

    return Pipeline(_assert_or)
