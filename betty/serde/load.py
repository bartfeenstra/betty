"""
An API to load serializable data dumps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class Loadable(ABC):
    """
    Instances can load serializable data dumps into ``self``.
    """

    @classmethod
    @abstractmethod
    def load(cls, dump: Dump, /) -> Self:
        """
        Create a new instance from ``dump``.

        :raises betty.exception.HumanFacingException: Raised if the dump is invalid.
        """
