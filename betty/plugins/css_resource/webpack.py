"""
The Webpack CSS resource.
"""

from typing import Final

from betty.html.css import CssResourceDefinition

WEBPACK: Final[CssResourceDefinition] = CssResourceDefinition(
    "webpack", resource="betty-static:///css/webpack/main.css"
)
