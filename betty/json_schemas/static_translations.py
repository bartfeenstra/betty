"""
JSON schemas for static translations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.portable import PortableMapping


def new_static_translations_schema(
    *, title: str = "Static translations", description: str | None = None
) -> PortableMapping:
    """
    Create a JSON Schema for :py:class:`betty.localizables.static.StaticTranslations`.
    """
    return {
        "additionalProperties": {
            "type": "string",
            "description": "A human-readable translation.",
        },
        "title": title,
        "description": ("" if description is None else description + " ")
        + "Keys are IETF BCP-47 language tags.",
    }
