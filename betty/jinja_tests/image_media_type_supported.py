"""
The image media type supported test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.image import is_supported_media_type
from betty.jinja.test import JinjaTest, JinjaTestDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


@final
@JinjaTestDefinition("image-media-type-supported", auto=True)
class ImageMediaTypeSupported(JinjaTest):
    """
    Test if a media type is supported by the image API.

    .. plugin:: jinja-test:image-media-type-supported
    """

    def __call__(  # noqa: D102
        self,
        media_type: MediaType | None,
        /,
    ) -> bool:
        if media_type is None:
            return False
        return is_supported_media_type(media_type)
