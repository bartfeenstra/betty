"""
Test utilities for :py:mod:`betty.error`.
"""

from __future__ import annotations

from typing import final

from betty.error import StaticError


@final
class DummyError(StaticError):
    """
    A dummy error.
    """

    _message = "Oops!"
