"""
Conditional validators.
"""

from __future__ import annotations

from typing import Any

from betty.functools import Pipe
from betty.validation import Validator, collect


def is_if_else[IfInputT, ElseInputT, IfOutputT, ElseOutputT](
    is_if: Validator[IfInputT, IfOutputT],
    is_else: Validator[ElseInputT, ElseOutputT],
    /,
) -> Pipe[IfInputT | ElseInputT, IfOutputT | ElseOutputT]:
    """
    Validate that at least one of the given validators passes.
    """

    def _is_if_else(value: Any, /) -> IfOutputT | ElseOutputT:
        with collect(value) as errors:
            with errors.catch():
                return is_if(value)
            with errors.catch():
                else_value = is_else(value)
                errors.clear()
                return else_value

    return Pipe(_is_if_else)
