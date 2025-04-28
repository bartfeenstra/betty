"""
Provide utilities for raising warnings.
"""

import warnings

import typing_extensions


class BettyDeprecationWarning(DeprecationWarning):
    """
    Raised for deprecated Betty functionality.
    """


def deprecate(message: str, stacklevel: int = 1):
    """
    Raise a Betty deprecation warning.
    """
    warnings.warn(message, category=BettyDeprecationWarning, stacklevel=stacklevel + 1)


class deprecated(typing_extensions.deprecated):
    """
    Decorate a class, function, or overload to indicate that it is deprecated.

    This is identical to :py:class:`typing_extensions.deprecated`, but raises a Betty
    deprecation warning.
    """

    def __init__(self, message: str, stacklevel: int = 1):
        super().__init__(
            message, category=BettyDeprecationWarning, stacklevel=stacklevel
        )
