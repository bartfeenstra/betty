"""
The image media type supported test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.image import is_image_type
from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.validation import Invalid

if TYPE_CHECKING:
    from betty.validators.media_type import MediaTypeIndicator


@final
@JinjaTestDefinition("image-media-type-supported", auto=True)
class ImageMediaTypeSupported(JinjaTest):
    """
    Test if a media type is supported by the image API.

    .. plugin:: jinja-test:image-media-type-supported
    """

    def __call__(  # noqa: D102
        self, media_type: MediaTypeIndicator | None, /
    ) -> bool:
        if media_type is None:
            return False
        try:
            is_image_type(media_type)
        except Invalid:
            return False
        return True
