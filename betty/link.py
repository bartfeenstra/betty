"""
An API for linking to web resources.
"""

from abc import abstractmethod
from typing import Protocol

from betty.locale.localizable import Localizable


class Link(Protocol):
    """
    A link to a web resource.
    """

    @property
    @abstractmethod
    def url(self) -> Localizable:
        """
        The URL the link points to.
        """

    @property
    @abstractmethod
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """
