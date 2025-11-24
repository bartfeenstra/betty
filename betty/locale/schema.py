"""
JSON schemas for the locale API.
"""

from __future__ import annotations

from typing import final

from betty.classtools import Singleton
from betty.json.schema import String


@final
class LocaleSchema(Singleton, String):
    """
    The JSON Schema for locales.
    """

    def __init__(self):
        super().__init__(
            def_name="locale",
            title="Locale",
            description="A BCP 47 locale identifier (https://www.ietf.org/rfc/bcp/bcp47.txt).",
        )
