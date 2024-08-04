"""
Provide the HTML API, for generating HTML pages.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class CssProvider(ABC):
    """
    Provide CSS for HTML pages.
    """

    @property
    @abstractmethod
    def public_css_paths(self) -> Sequence[str]:
        """
        The public URL paths to the CSS files to include in each HTML page.
        """
        pass


class JsProvider(ABC):
    """
    Provide JavaScript for HTML pages.
    """

    @property
    @abstractmethod
    def public_js_paths(self) -> Sequence[str]:
        """
        The public URL paths to the JavaScript files to include in each HTML page.
        """
        pass
