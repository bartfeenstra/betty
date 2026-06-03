from typing import Final  # noqa: D100

from betty.media_type import MediaType, MediaTypeDefinition

YAML: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "yaml",
    label="YAML",
    media_type=MediaType("application/yaml", extensions=[".yaml", ".yml"]),
)
"""
The media type for YAML content.
"""
