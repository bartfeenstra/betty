"""
The ``json_load`` Jinja filter.
"""

from __future__ import annotations

import json as stdjson
from typing import Any, final

from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition


@final
@JinjaFilterDefinition("json-load", auto=True)
class JsonLoad(JinjaFilter):
    """
    Load a value from a JSON string.

    .. plugin:: jinja-filter:json-load
    """

    def __call__(  # noqa: D102
        self, data: str, /
    ) -> Any:
        return stdjson.loads(data)
