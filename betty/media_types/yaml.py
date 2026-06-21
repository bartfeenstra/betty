from __future__ import annotations  # noqa: D100

from typing import Final

from betty.media_type import MediaType, MediaTypeDefinition

YAML: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "yaml",
    label="YAML",
    media_type=MediaType("application/yaml", extensions=[".yaml", ".yml"]),
)
"""
The media type for YAML content.
"""
