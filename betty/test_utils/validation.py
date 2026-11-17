"""
Test utilities for :py:mod:`betty.validation`.
"""

from __future__ import annotations

from typing import final

from betty.validation import StaticInvalid


@final
class DummyInvalid(StaticInvalid):
    """
    A dummy validation error.
    """

    _message = "Oops!"
