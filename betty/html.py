"""
Provide the HTML API, for generating HTML pages.
"""

from abc import ABC, abstractmethod


class CssProvider(ABC):
    """
    Provide CSS for HTML pages.
    """

    @property
    @abstractmethod
    def public_css_paths(self) -> list[str]:
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
    def public_js_paths(self) -> list[str]:
        """
        The public URL paths to the JavaScript files to include in each HTML page.
        """
        pass
