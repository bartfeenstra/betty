"""
Image readers using :py:mod:`pdf2image`.
"""

from __future__ import annotations

import warnings
from asyncio import to_thread
from pathlib import Path
from typing import final, override

from pdf2image.pdf2image import convert_from_bytes, convert_from_path
from PIL.Image import DecompressionBombWarning, Image

from betty.image import ImageReader, ImageReaderDefinition
from betty.media_types import pdf


@final
@ImageReaderDefinition(
    "pdf2image",
    pdf,
    requires=[
        # @todo Add a Poppler requirement.
    ],
)
class Pdf2Image(ImageReader):
    """
    Read images using :py:mod:`pdf2image`.
    """

    @override
    async def read(self, image: bytes | Path, /) -> Image:
        return await to_thread(self._read, image)

    def _read(self, image: bytes | Path, /) -> Image:
        # Ignore warnings about decompression bombs, because we know where the files come from.
        with warnings.catch_warnings(
            action="ignore", category=DecompressionBombWarning
        ):
            if isinstance(image, Path):
                return convert_from_path(image, last_page=1)[0]
            return convert_from_bytes(image, last_page=1)[0]
