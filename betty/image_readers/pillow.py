"""
Image readers using :py:mod:`PIL` itself.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import final, override

from PIL import Image

from betty.file import read
from betty.image import ImageReader, ImageReaderDefinition
from betty.media_types import bmp, gif, icns, ico, jpeg, jpeg_2000, jpeg_mpo, png


@final
@ImageReaderDefinition(
    "pillow", media_types=(bmp, gif, icns, ico, jpeg, jpeg_2000, jpeg_mpo, png)
)
class Pillow(ImageReader):
    """
    Read images using :py:mod:`PIL` itself.

    .. plugin:: image-reader:pillow
    """

    @override
    async def read(self, image: bytes | Path, /) -> Image.Image:
        if isinstance(image, Path):
            image = await read(image, mode="rb")
        # Ignore warnings about decompression bombs, because we know where the files come from.
        with warnings.catch_warnings(
            action="ignore", category=Image.DecompressionBombWarning
        ):
            return Image.open(
                image,
                formats=[Image.EXTENSION[self.definition.media_type.extension]],
            )
