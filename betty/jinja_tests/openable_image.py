"""
Image tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.factory import Manufacturable
from betty.jinja.test import JinjaTest, JinjaTestDefinition

if TYPE_CHECKING:
    from betty.content_type import ContentTypeDefinition, ContentTypeNegotiator
    from betty.media_type import (
        ResolvableMediaType,
    )


@final
@JinjaTestDefinition("openable-image", auto=True)
class OpenableImage(JinjaTest, Manufacturable):
    """
    Test that an image type is openable.

    .. plugin:: jinja-test:openable-image
    """

    def __init__(self, openable: ContentTypeNegotiator, /):
        self._openable = openable

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls((await app.imager).openable)

    def __call__(  # noqa: D102
        self, media_type: ResolvableMediaType | ContentTypeDefinition | None, /
    ) -> bool:
        return self._openable.request(media_type) is not None
