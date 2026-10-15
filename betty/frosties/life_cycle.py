"""
Frozen life cycles.
"""

from __future__ import annotations

from typing import final, override

from betty.frosty import Frosty
from betty.life_cycle import Bootstrappable


class FrozenOnBootstrap(Bootstrappable, Frosty):
    """
    An object that becomes frozen when it is bootstrapped.
    """

    @final
    @override
    @property
    def is_frozen(self) -> bool:
        return self.is_bootstrapped

    @final
    @override
    def _on_is_bootstrapped(self) -> None:
        self._freeze()
