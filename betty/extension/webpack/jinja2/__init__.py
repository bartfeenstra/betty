"""
Integrate Webpack with Jinja2.
"""

from jinja2.runtime import Context


def _context_js_entry_points(context: Context) -> set[str]:
    entry_points = context.resolve_or_missing("webpack_js_entry_points")
    if isinstance(entry_points, set):
        return entry_points
    raise RuntimeError(
        "No `webpack_js_entry_points` context variable exists in this Jinja2 template."
    )
