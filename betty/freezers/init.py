"""
Integrate :py:mod:`betty.frozen` and :py:mod:`betty.classtools.init`.
"""

from __future__ import annotations

from typing import final, override

from betty.classtools.init import Init
from betty.frozen import Freezable


class FrozenOnInit(Freezable, Init):
    """
    An object that is frozen (immutable) after initialization.
    """

    @override
    def post_init(self) -> None:
        self.freeze()

    @final
    @override
    @property
    def is_frozen(self) -> bool:
        return self.is_initialized is True
