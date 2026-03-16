"""
The Webpack entry point loader JavaScript resource.
"""

from typing import final

from betty.html.js import JsResource, JsResourceDefinition


@final
@JsResourceDefinition(
    "webpack-entry-point-loader", resource="betty-static:///js/webpack-entry-loader.js"
)
class WebpackEntryPointLoader(JsResource):
    """
    .. plugin:: js-resource:webpack-entry-point-loader.
    """
