"""
An API for linking to web resources.
"""

from abc import ABC, abstractmethod

from betty.locale.localizable import Localizable


class Link(ABC):
    """
    A link to a web resource.
    """

    @property
    @abstractmethod
    def url(self) -> Localizable:
        """
        The absolute URL the link points to.
        """

    @property
    @abstractmethod
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """
