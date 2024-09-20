"""
Provide Jinja2 filters to integrate with Webpack.
"""

from __future__ import annotations

from jinja2 import pass_context

from betty.project.extension.webpack.jinja2 import _context_js_entry_points
from betty.jinja2.filter import filter_public_js
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.jinja2 import Filters
    from jinja2.runtime import Context


@pass_context
def filter_webpack_entry_point_js(context: Context, entry_point_name: str) -> None:
    """
    Add a Webpack entry point's JavaScript files to the current page.
    """
    filter_public_js(context, "/js/webpack-entry-loader.js")
    _context_js_entry_points(context).add(entry_point_name)


FILTERS: Filters = {
    "webpack_entry_point_js": filter_webpack_entry_point_js,
}
