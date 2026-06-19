"""
Media type JSON Schemas.
"""

from __future__ import annotations

from typing import final

from betty.json_schema import String


@final
class MediaTypeSchema(String):
    """
    A JSON Schema for :py:class:`betty.media_type.MediaType`.
    """

    def __init__(self):
        super().__init__(
            def_name="mediaType",
            title="Media type",
            description="An IANA media type (https://www.iana.org/assignments/media-types/media-types.xhtml).",
        )
