"""
Manipulate images.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Final, final, overload

from PIL import Image

from betty.content_type import ContentTypeDefinition, ContentTypeRepository
from betty.content_types import avif, bmp, gif, jpeg, jpeg_xl, png, svg, webp
from betty.file import read, write

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

    def __init__(self, content_types: ContentTypeRepository, /):
        self.publishable: Final[ContentTypeRepository] = ContentTypeRepository(
            avif, bmp, gif, jpeg, jpeg_xl, png, svg, webp
        )
        self._openable: MutableMapping[ContentTypeDefinition, str] = {}
        self._savable: MutableMapping[ContentTypeDefinition, str] = {}
        Image.init()
        for content_type in content_types:
            for format_id, format_mime in Image.MIME.items():
                if content_type.request(format_mime):
                    if format_id in Image.OPEN:
                        self._openable[content_type] = format_id
                    if format_id in Image.SAVE:
                        self._savable[content_type] = format_id
            for format_extension, format_id in Image.EXTENSION.items():
                if content_type.extensions.request(format_extension):
                    if format_id in Image.OPEN:
                        self._openable[content_type] = format_id
                    if format_id in Image.SAVE:
                        self._savable[content_type] = format_id
        self.openable: Final[ContentTypeRepository] = ContentTypeRepository(
            *self._openable
        )
        self.savable: Final[ContentTypeRepository] = ContentTypeRepository(
            *self._savable
        )

    @overload
    async def open(
        self, image: StrPath, /, *, content_type: ContentTypeDefinition | None = None
    ) -> Image.Image:
        pass

    @overload
    async def open(
        self, image: IO[bytes], /, *, content_type: ContentTypeDefinition
    ) -> Image.Image:
        pass

    async def open(self, image, /, *, content_type=None):
        """
        Read an image.
        """
        if content_type is None:
            content_type, _extension = self.openable.extensions.require(image)
        if isinstance(image, Path):
            image = BytesIO(await read(image, mode="rb"))
        return Image.open(image, formats=[self._openable[content_type]])

    async def save(
        self,
        image: Image.Image,
        destination: Path,
        /,
        *,
        content_type: ContentTypeDefinition,
    ) -> None:
        """
        Write an image.
        """
        image_data = BytesIO()
        image.save(image_data, format=self._savable[content_type])
        image_data.seek(0)
        await write(destination, image_data.read(), mode="wb")
