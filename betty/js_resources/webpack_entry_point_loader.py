"""
The Webpack entry point loader JavaScript resource.
"""

from __future__ import annotations

from typing import Final

from betty.html.js import JsResourceDefinition

WEBPACK_ENTRY_POINT_LOADER: Final[JsResourceDefinition] = JsResourceDefinition(
    "webpack-entry-point-loader", resource="betty-static:///js/webpack-entry-loader.js"
)
