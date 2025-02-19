"""
Provide Betty's default Jinja2 globals.
"""

from jinja2 import pass_context
from jinja2.runtime import Context


class HtmlId:
    """
    Generate unique HTML IDs.
    """

    def __init__(self):
        self._count = 0

    def increment(self) -> None:
        """
        Increment the ID counter.
        """
        self._count += 1

    def __str__(self) -> str:
        return str(self._count)


@pass_context
def generate_html_id(context: Context) -> str:
    """
    Generate an HTML ID unique within the current render call.
    """
    html_id = context.resolve_or_missing("_html_id_generator")
    if not isinstance(html_id, HtmlId):
        raise RuntimeError(
            "No `html_id` context variable exists in this Jinja2 template."
        )
    html_id.increment()
    return f"betty-generated--{html_id}"
