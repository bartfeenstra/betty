"""
Manipulate images.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, final, overload

from PIL import Image

from betty.file import read, write
from betty.media_type import MediaTypeDefinition, MediaTypeRepository
from betty.media_types import avif, bmp, gif, jpeg, jpeg_xl, png, svg, webp

if TYPE_CHECKING:
    from collections.abc import MutableMapping

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

    def __init__(self, media_types: MediaTypeRepository, /):
        self.publishable: Final[MediaTypeRepository] = MediaTypeRepository(
            avif, bmp, gif, jpeg, jpeg_xl, png, svg, webp
        )
        self._openable: MutableMapping[MediaTypeDefinition, str] = {}
        self._savable: MutableMapping[MediaTypeDefinition, str] = {}
        Image.init()
        for media_type in media_types:
            for format_id, format_mime in Image.MIME.items():
                if media_type.request(format_mime):
                    if format_id in Image.OPEN:
                        self._openable[media_type] = format_id
                    if format_id in Image.SAVE:
                        self._savable[media_type] = format_id
            for format_extension, format_id in Image.EXTENSION.items():
                if media_type.extensions.request(format_extension):
                    if format_id in Image.OPEN:
                        self._openable[media_type] = format_id
                    if format_id in Image.SAVE:
                        self._savable[media_type] = format_id
        self.openable: Final[MediaTypeRepository] = MediaTypeRepository(*self._openable)
        self.savable: Final[MediaTypeRepository] = MediaTypeRepository(*self._savable)

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
        return Image.open(image, formats=[self._openable[media_type]])

    async def save(
        self,
        image: Image.Image,
        destination: Path,
        /,
        *,
        media_type: MediaTypeDefinition,
    ) -> None:
        """
        Write an image.
        """
        image_data = BytesIO()
        image.save(image_data, format=self._savable[media_type])
        image_data.seek(0)
        await write(destination, image_data.read(), mode="wb")
