"""
An API to load serializable data dumps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class Loadable(ABC):
    """
    Instances can load serializable data dumps into ``self``.
    """

    @abstractmethod
    def load(self, dump: Dump) -> None:
        """
        Load a serialized data dump into ``self``.

        :raises betty.exception.UserFacingException: Raised if the dump is invalid.
        """
