"""
Integrate Webpack with Jinja2.
"""

from collections.abc import MutableSet

from jinja2.runtime import Context

from betty.jinja import context_document


def _context_js_entry_points(context: Context) -> MutableSet[str]:
    document = context_document(context)
    try:
        js_entry_points = document["webpack_js_entry_points"]
        assert isinstance(js_entry_points, MutableSet)
        return js_entry_points  # ty:ignore[invalid-return-type]
    except KeyError:
        raise RuntimeError(
            "No `resource.webpack_js_entry_points` context variable exists in this Jinja2 template."
        ) from None
