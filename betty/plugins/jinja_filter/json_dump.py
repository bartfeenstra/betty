"""
The ``json_dump`` Jinja filter.
"""

from __future__ import annotations

import json as stdjson
from typing import Any, final

from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition


@final
@JinjaFilterDefinition("json-dump", auto=True)
class JsonDump(JinjaFilter):
    """
    Dump a value to a JSON string.

    .. plugin:: jinja-filter:json-dump
    """

    def __call__(  # noqa: D102
        self, data: Any, *, indent: int | None = None
    ) -> str:
        return stdjson.dumps(data, indent=indent)
