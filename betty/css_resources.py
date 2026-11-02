"""
CSS resource plugins.
"""

from __future__ import annotations

from typing import Final

from betty.html.css import CssResourceDefinition

webpack: Final[CssResourceDefinition] = CssResourceDefinition(
    "webpack", resource="betty-static:///css/webpack/main.css"
)
