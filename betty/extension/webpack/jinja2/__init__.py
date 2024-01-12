"""
Integrate Webpack with Jinja2.
"""
from jinja2.runtime import Context


def _context_js_entrypoints(context: Context) -> set[str]:
    entrypoints = context.resolve_or_missing('webpack_js_entrypoints')
    if isinstance(entrypoints, set):
        return entrypoints
    raise RuntimeError('No `webpack_js_entrypoints` context variable exists in this Jinja2 template.')
