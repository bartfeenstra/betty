"""
Manipulate images.
"""

from typing import TypeAlias

import math

from PIL.Image import Image


OneDimensionalSize: TypeAlias = tuple[int, None] | tuple[None, int]
TwoDimensionalSize: TypeAlias = tuple[int, int]
Size: TypeAlias = OneDimensionalSize | TwoDimensionalSize


def resize_cover(original_image: Image, cover_size: Size) -> Image:
    """
    Resize an image to cover an area.
    """
    cover_width, cover_height = cover_size
    ratio = max(
        cover_width / original_image.width if cover_width is not None else 0,
        cover_height / original_image.height if cover_height is not None else 0,
    )
    resize_width = (
        math.ceil(original_image.width * ratio) if cover_width else original_image.width
    )
    resize_height = (
        math.ceil(original_image.height * ratio)
        if cover_height
        else original_image.height
    )
    cover_image = original_image.resize((resize_width, resize_height))

    if cover_width is not None and cover_height is not None:
        cover_image = resize_crop(cover_image, (cover_width, cover_height))

    cover_image.format = original_image.format

    return cover_image


def resize_crop(original_image: Image, crop_size: TwoDimensionalSize) -> Image:
    """
    Resize an image by cropping it.
    """
    crop_width, crop_height = crop_size
    left = math.ceil((original_image.width - crop_width) / 2)
    top = math.ceil((original_image.height - crop_height) / 2)
    right = left + crop_width
    bottom = top + crop_height
    crop_image = original_image.crop((left - 1, top - 1, right - 1, bottom - 1))
    crop_image.format = original_image.format
    return crop_image
