"""
The ``webpack_entry_point_js`` Jinja filter.
"""

from __future__ import annotations

from collections.abc import MutableSet
from typing import TYPE_CHECKING, cast, final

from jinja2 import pass_context

from betty.document_providers.webpack import Webpack
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.project import Project

if TYPE_CHECKING:
    from jinja2.runtime import Context


@final
@JinjaFilterDefinition(
    "webpack-entry-point-js",
    requires={Project.document_providers.require(Webpack)},
)
class WebpackEntryPointJs(JinjaFilter):
    """
    Add a Webpack entry point's JavaScript files to the current page.

    .. plugin:: jinja-filter:webpack-entry-point-js
    """

    @pass_context
    def __call__(  # noqa: D102
        self, context: Context, entry_point_name: str, /
    ) -> None:
        document = context_document(context)
        try:
            js_entry_points = document["webpack_js_entry_points"]
            assert isinstance(js_entry_points, MutableSet)
            cast(MutableSet[str], js_entry_points).add(entry_point_name)
        except KeyError:
            raise RuntimeError(
                "No `resource.webpack_js_entry_points` context variable exists in this Jinja2 template."
            ) from None
