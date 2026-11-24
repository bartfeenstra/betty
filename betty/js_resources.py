"""
JavaScript resource plugins.
"""

from __future__ import annotations

from typing import Final

from betty.discoveries.module import ModuleDefinitionDiscovery
from betty.html.js import JsResourceDefinition

discover = ModuleDefinitionDiscovery(JsResourceDefinition)

webpack_entry_point_loader: Final[JsResourceDefinition] = JsResourceDefinition(
    "webpack-entry-point-loader", resource="betty-static:///js/webpack-entry-loader.js"
)
