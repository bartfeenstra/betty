"""
Always-frozen types.
"""

from __future__ import annotations

from typing import final, override

from betty.frozen import Freezable


class Frozen(Freezable):
    """
    An object that is always frozen.
    """

    __slots__ = ()

    @final
    @override
    @property
    def is_frozen(self) -> bool:
        return True
