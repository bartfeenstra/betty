"""
JSON schemas for static translations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.json_schema import Object
from betty.locale.localizable.markup import Paragraph

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


class StaticTranslationsSchema(Object):
    """
    A JSON Schema for :py:class:`betty.locale.localizable.static.StaticTranslations`.
    """

    def __init__(
        self,
        *,
        title: ResolvableLocalizable = "Static translations",
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            title=title,
            description=Paragraph(
                *([] if description is None else [description]),
                "Keys are IETF BCP-47 language tags.",
            ),
        )
        self.schema["additionalProperties"] = {
            "type": "string",
            "description": "A human-readable translation.",
        }
