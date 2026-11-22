"""
Manipulate images.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, final, overload

from PIL import Image

from betty.file import read, write
from betty.media_type import (
    MediaType,
    MediaTypeDefinition,
    MediaTypeMatcher,
    MediaTypeRepository,
)
from betty.media_types import bmp, gif, jpeg, png, svg, webp

if TYPE_CHECKING:
    from betty.pathlib import StrPath


type Percentage = int
type Pixel = int
type OneDimensionalSize = tuple[Pixel, None] | tuple[None, Pixel]
type TwoDimensionalSize = tuple[Pixel, Pixel]
type Size = OneDimensionalSize | TwoDimensionalSize
type FocusArea = tuple[Percentage, Percentage, Percentage, Percentage]


@final
class Imager:
    """
    The imager.
    """

    def __init__(self, media_types: MediaTypeMatcher, /):
        self._media_types = media_types
        # @todo Finish the list of publishable image types.
        # @todo Take inspiration from https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types
        self.publishable: Final[MediaTypeRepository] = MediaTypeRepository(
            bmp, gif, jpeg, png, svg, webp
        )
        # @todo Compute the readable and writable types based on PIL.Image.EXTENSION, PIL.Image.MINE, PIL.Image.OPEN,
        # @todo and PIL.Image.SAVE.
        self.openable: Final[MediaTypeRepository] = MediaTypeRepository()
        self.writable: Final[MediaTypeRepository] = MediaTypeRepository(gif, jpeg, png)

    @overload
    async def open(
        self, image: StrPath, /, *, media_type: MediaTypeDefinition | None = None
    ) -> Image.Image:
        pass

    @overload
    async def open(
        self, image: IO[bytes], /, *, media_type: MediaTypeDefinition
    ) -> Image.Image:
        pass

    async def open(self, image, /, *, media_type=None):
        """
        Read an image.
        """
        if media_type is None:
            media_type, _extension = self.openable.extensions.require(image)
        if isinstance(image, Path):
            image = await read(image, mode="rb")
        return Image.open(image, formats=[Image.EXTENSION[media_type.extension]])

    async def save(
        self,
        image: Image.Image,
        destination: Path,
        /,
        *,
        media_type: MediaType | MediaTypeDefinition,
    ) -> None:
        """
        Write an image.
        """
        image_data = BytesIO()
        image.save(
            image_data,
            format=Image.EXTENSION[self.writable.require(media_type).extension],
        )
        image_data.seek(0)
        await write(destination, image_data.read(), mode="wb")
