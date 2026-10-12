"""
Integrate :py:mod:`betty.frosty` and :py:mod:`betty.classtools`.
"""

from __future__ import annotations

from typing import final, override

from betty.classtools import Object, TypeABCMeta
from betty.frosty import Frosty


class Frozen(Object, Frosty, metaclass=TypeABCMeta):
    """
    An object that is frozen (immutable) after initialization.
    """

    @final
    @override
    def _on_is_initialized(self) -> None:
        self._freeze()

    @final
    @override
    @property
    def is_frozen(self) -> bool:
        return self.is_initialized
