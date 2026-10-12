"""
Freezable objects using attributes.
"""

from __future__ import annotations

from typing import Any, final, override

from betty.frosty import Freezable


class AttrFreezable(Freezable):
    """
    An object that can be frozen and stores its status in an attribute.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.__is_frozen = False
        super().__init__(*args, **kwargs)

    @final
    @override
    @property
    def is_frozen(self) -> bool:
        try:
            return self.__is_frozen
        except AttributeError:
            return False

    @override
    def _freeze(self) -> None:
        self.__is_frozen = True
