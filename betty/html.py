"""
Provide the HTML API, for generating HTML pages.
"""


class CssProvider:
    """
    Provide CSS for HTML pages.
    """

    @property
    def public_css_paths(self) -> list[str]:
        """
        The public URL paths to the CSS files to include in each HTML page.
        """
        raise NotImplementedError(repr(self))


class JsProvider:
    """
    Provide JavaScript for HTML pages.
    """

    @property
    def public_js_paths(self) -> list[str]:
        """
        The public URL paths to the JavaScript files to include in each HTML page.
        """
        raise NotImplementedError(repr(self))
