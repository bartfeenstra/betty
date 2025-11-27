"""
Integrate Webpack with Jinja2.
"""

from jinja2.runtime import Context

from betty.jinja2 import context_resource_context


def _context_js_entry_points(context: Context) -> set[str]:
    resource = context_resource_context(context)
    try:
        return resource["webpack_js_entry_points"]  # type: ignore[no-any-return,typeddict-item]
    except KeyError:
        raise RuntimeError(
            "No `resource.webpack_js_entry_points` context variable exists in this Jinja2 template."
        ) from None
