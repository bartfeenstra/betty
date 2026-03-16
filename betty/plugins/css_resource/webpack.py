"""
The Webpack CSS resource.
"""

from typing import final

from betty.html.css import CssResource, CssResourceDefinition


@final
@CssResourceDefinition("webpack", resource="betty-static:///css/webpack/webpack.css")
class Webpack(CssResource):
    """
    .. plugin:: css-resource:webpack.
    """
