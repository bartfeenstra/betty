"""
Integrate Webpack with Jinja2.
"""

from jinja2.runtime import Context

from betty.jinja2 import context_document


def _context_js_entry_points(context: Context) -> set[str]:
    document = context_document(context)
    try:
        return document["webpack_js_entry_points"]  # type: ignore[return-value]
    except KeyError:
        raise RuntimeError(
            "No `resource.webpack_js_entry_points` context variable exists in this Jinja2 template."
        ) from None
