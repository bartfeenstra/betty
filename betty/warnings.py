"""
Provide utilities for raising warnings.
"""

from __future__ import annotations

import warnings
from typing import LiteralString


class BettyDeprecationWarning(DeprecationWarning):
    """
    Raised for deprecated Betty functionality.
    """


def deprecate(message: str, stacklevel: int = 1) -> None:
    """
    Raise a Betty deprecation warning.
    """
    warnings.warn(message, category=BettyDeprecationWarning, stacklevel=stacklevel + 1)


class deprecated(warnings.deprecated):
    """
    Decorate a class, function, or overload to indicate that it is deprecated.

    This is identical to :py:class:`warnings.deprecated`, but raises a Betty
    deprecation warning.
    """

    def __init__(self, message: LiteralString, stacklevel: int = 1):
        super().__init__(
            message, category=BettyDeprecationWarning, stacklevel=stacklevel
        )
