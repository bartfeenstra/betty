"""
Provide Jinja2 filters to integrate with Webpack.
"""

from __future__ import annotations

from jinja2 import pass_context

from betty.extension.webpack.jinja2 import _context_js_entrypoints
from betty.jinja2.filter import filter_public_js
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jinja2.runtime import Context


@pass_context
def filter_webpack_entrypoint_js(context: Context, entrypoint_name: str) -> None:
    """
    Add a Webpack entrypoint's JavaScript files to the current page.
    """
    filter_public_js(context, "/js/webpack-entry-loader.js")
    _context_js_entrypoints(context).add(entrypoint_name)


FILTERS = {
    "webpack_entrypoint_js": filter_webpack_entrypoint_js,
}
