"""
Provide Jinja2 filters to integrate with Webpack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import pass_context

from betty.project.extension.webpack.jinja2 import _context_js_entry_points

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.jinja2 import Filters


@pass_context
async def filter_webpack_entry_point_js(
    context: Context, entry_point_name: str
) -> None:
    """
    Add a Webpack entry point's JavaScript files to the current page.
    """
    _context_js_entry_points(context).add(entry_point_name)


FILTERS: Filters = {
    "webpack_entry_point_js": filter_webpack_entry_point_js,
}
