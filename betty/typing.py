"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import final

type Number = int | float


@final
class Unreachable(NotImplementedError):
    """
    Raised when a line of code is supposed to be unreachable, but was executed anyway.

    Use ``raise Unreachable`` to satisfy type checkers as well as tell Betty's code coverage collection to ignore that
    line.
    """

    def __init__(self, reason: str | None = None):
        super().__init__(
            f"This code was marked unreachable, and this line should never have been executed{'.' if reason is None else f', because {reason}.'}."
        )
