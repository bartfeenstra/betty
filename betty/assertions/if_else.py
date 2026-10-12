"""
Conditional assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError
from betty.functools import Pipe
from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.markup import Paragraphs

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSequence


def assert_if_else[ValueT, ReturnT, AssertionReturnU](
    if_assertion: Callable[[ValueT], ReturnT],
    else_assertion: Callable[[ValueT], AssertionReturnU],
    /,
) -> Pipe[ValueT, ReturnT | AssertionReturnU]:
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

    return Pipe(_assert_or)
