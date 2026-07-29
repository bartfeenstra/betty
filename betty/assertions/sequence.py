"""
Sequence data assertions.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import Any, overload

from betty.assertions.type import assert_type
from betty.exception import reraise_with_indicator
from betty.functools import Pipe, Pipeline
from betty.indicator.operator import Index


@overload
def assert_sequence(
    value_assertion: None = None, /
) -> Pipeline[Any, MutableSequence[Any]]:
    pass


@overload
def assert_sequence[ReturnT](
    value_assertion: Pipe[Any, ReturnT], /
) -> Pipeline[Any, MutableSequence[ReturnT]]:
    pass


def assert_sequence[ReturnT](value_assertion: Pipe[Any, ReturnT] | None = None, /):
    """
    Assert that a value is a sequence.

    Optionally assert that values are of a given type.
    """

    def _assert_sequence(value: Any, /) -> MutableSequence[ReturnT]:
        sequence = assert_type(Sequence)(value)
        if value_assertion is None:
            return list(sequence)
        asserted_sequence = []
        for value_index, value_value in enumerate(sequence):
            with reraise_with_indicator(Index(value_index)):
                asserted_sequence.append(value_assertion(value_value))
        return asserted_sequence

    return Pipeline(_assert_sequence)
