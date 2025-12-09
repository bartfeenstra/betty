"""
JSON schemas for static translations.
"""

from __future__ import annotations

from betty.json.schema import Object


class StaticTranslationsSchema(Object):
    """
    A JSON Schema for :py:class:`betty.locale.localizable.static.StaticTranslations`.
    """

    def __init__(
        self, *, title: str = "Static translations", description: str | None = None
    ):
        super().__init__(
            title=title,
            description=(
                (description or "") + "Keys are IETF BCP-47 language tags."
            ).strip(),
        )
        self._schema["additionalProperties"] = {
            "type": "string",
            "description": "A human-readable translation.",
        }
