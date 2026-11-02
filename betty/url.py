"""
URL handling.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


class HasUrl(metaclass=ABCMeta):
    """
    An object that has a URL.
    """

    @property
    @abstractmethod
    def url(self) -> AnyLocalizable:
        """
        The object's URL.
        """
