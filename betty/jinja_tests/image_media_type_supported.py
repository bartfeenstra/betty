"""
The image media type supported test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.jinja.test import JinjaTest, JinjaTestDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


# @todo Remove this
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
        raise NotImplementedError
