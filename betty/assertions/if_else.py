"""
Conditional assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions import _HumanFacingValueError
from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.markup import Paragraphs
from betty.pipeline import Inlet, Pipeline

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSequence


def assert_if_else[ValueT, ReturnT, AssertionReturnU](
    if_assertion: Callable[[ValueT], ReturnT],
    else_assertion: Callable[[ValueT], AssertionReturnU],
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

    return Inlet(_assert_or)
