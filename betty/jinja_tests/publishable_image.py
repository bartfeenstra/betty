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
@JinjaTestDefinition("publishable-image", auto=True)
class PublishableImage(JinjaTest, Manufacturable):
    """
    Test that an image type is publishable.

    .. plugin:: jinja-test:publishable-image
    """

    def __init__(self, publishable: ContentTypeNegotiator, /):
        self._publishable = publishable

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls((await app.imager).publishable)

    def __call__(  # noqa: D102
        self, media_type: ResolvableMediaType | ContentTypeDefinition | None, /
    ) -> bool:
        return self._publishable.request(media_type) is not None
