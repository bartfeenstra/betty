"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import Any

try:
    from ty_extensions import Intersection, Not
except ImportError:

    class Intersection:
        """
        A fake intersection type that works runtime, until https://github.com/astral-sh/ty/issues/2084 is fixed.
        """

        def __class_getitem__(cls, item: Any):
            pass  # pragma: nocover

    class Not:
        """
        A fake negation type that works runtime, until https://github.com/astral-sh/ty/issues/2084 is fixed.
        """

        def __class_getitem__(cls, item: Any):
            pass  # pragma: nocover


type Number = int | float
