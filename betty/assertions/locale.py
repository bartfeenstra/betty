"""
Locale assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertions.str import assert_str
from betty.locale import from_language_tag

if TYPE_CHECKING:
    from babel import Locale

    from betty.functools import Pipeline


def assert_locale() -> Pipeline[Any, Locale]:
    """
    Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
    """
    return assert_str() | from_language_tag
