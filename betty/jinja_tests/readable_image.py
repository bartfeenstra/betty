"""
Image tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.factory import Manufacturable
from betty.jinja.test import JinjaTest, JinjaTestDefinition

if TYPE_CHECKING:
    from betty.media_type import (
        MediaTypeDefinition,
        MediaTypeMatcher,
        ResolvableMediaType,
    )


@final
@JinjaTestDefinition("readable-image", auto=True)
class ReadableImage(JinjaTest, Manufacturable):
    """
    Test that an image type is readable.

    .. plugin:: jinja-test:readable-image
    """

    def __init__(self, readable: MediaTypeMatcher, /):
        self._readable = readable

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls((await app.imager).readable)

    def __call__(  # noqa: D102
        self, media_type: ResolvableMediaType | MediaTypeDefinition, /
    ) -> bool:
        return self._readable.request(media_type) is not None
