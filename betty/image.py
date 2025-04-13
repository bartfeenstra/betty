"""
Manipulate images.
"""

import math
from pathlib import Path
from typing import TypeAlias

from PIL import UnidentifiedImageError
from PIL.Image import EXTENSION, Image, init, preinit

from betty.media_type import MediaType
from betty.media_type.media_types import PDF

Percentage: TypeAlias = int
Pixel: TypeAlias = int
OneDimensionalSize: TypeAlias = tuple[Pixel, None] | tuple[None, Pixel]
TwoDimensionalSize: TypeAlias = tuple[Pixel, Pixel]
Size: TypeAlias = OneDimensionalSize | TwoDimensionalSize
FocusArea: TypeAlias = tuple[Percentage, Percentage, Percentage, Percentage]


def is_supported_media_type(media_type: MediaType) -> bool:
    """
    Test if a media type is supported by the image API.
    """
    if media_type.type == "image":
        return True
    if media_type == PDF:
        return True
    return False


def image_file_path_format(image_file_path: Path) -> str:
    """
    Get the PIL image format for an image's file path.
    """
    if image_file_path.suffix not in EXTENSION:
        preinit()
        if image_file_path.suffix not in EXTENSION:
            init()
            if image_file_path.suffix not in EXTENSION:
                raise UnidentifiedImageError(
                    f"cannot identify image file {image_file_path}"
                )
    return EXTENSION[image_file_path.suffix]


def _assert_size(size: Size) -> None:
    if size[0] is not None and size[0] <= 0 or size[1] is not None and size[1] <= 0:
        raise ValueError("Invalid size: sizes must be greater than 0")


def _assert_area(area: FocusArea) -> None:
    if area[0] >= area[2] or area[1] >= area[3]:
        raise ValueError("Invalid area")


def _assert_boundaries(image: Image, area: FocusArea) -> None:
    if (
        0 > area[0] > image.width
        or 0 > area[2] > image.width
        or 0 > area[1] > image.height
        or 0 > area[3] > image.height
    ):
        raise ValueError("Given area does not fit within the image.")


def resize_cover(
    original_image: Image, resize_size: Size, *, focus: FocusArea | None = None
) -> Image:
    """
    Resize an image to cover an area.

    :arg focus: An area within the image of which as much as possible should be part of the resized image.
    """
    _assert_size(resize_size)
    if focus is not None:
        _assert_area(focus)
        _assert_boundaries(original_image, focus)

    resize_width, resize_height = resize_size
    focus_left = 0 if focus is None else focus[0] * original_image.width / 100
    focus_top = 0 if focus is None else focus[1] * original_image.height / 100
    focus_right = (
        original_image.width if focus is None else focus[2] * original_image.width / 100
    )
    focus_bottom = (
        original_image.height
        if focus is None
        else focus[3] * original_image.height / 100
    )
    focus_width = focus_right - focus_left
    focus_height = focus_bottom - focus_top
    focus_ratio = focus_width / focus_height

    # Bind the maximum size by the original image.
    # This ensures the resized image won't have empty bars.
    max_width: float = original_image.width
    max_height: float = original_image.height
    # Bind the minimum size by the requested resize area, as long as the maximum allows.
    # This ensures we use at least as many pixels as needed for the resize area, reducing
    # the likelihood of the resulting image being *enlarged*.
    min_width: float = 0 if resize_width is None else min(max_width, resize_width)
    min_height: float = 0 if resize_height is None else min(max_height, resize_height)

    max_ratio = max_width / max_height
    # Adjust the minimum and maximum dimensions if the
    # resize area has a ratio (a width *and* a height).
    if resize_width is not None and resize_height is not None:
        resize_ratio = resize_width / resize_height

        # Adjust the maximum dimensions.
        if resize_ratio > max_ratio:
            # The resize area is more landscape than the original image.
            # The height is the constrained dimension.
            max_height = min(max_height, max_width / resize_ratio)
        else:
            # The resize's area is more portrait than the original image.
            # The width is the constrained dimension.
            max_width = min(max_width, max_height * resize_ratio)

        # Adjust the minimum dimensions.
        if resize_ratio > focus_ratio:
            # The resize area is more landscape than the focus area.
            # The height is the constrained dimension.
            min_height = max(min_height, focus_width / resize_ratio)
            crop_height = min(max_height, max(min_height, focus_height))
            crop_width = crop_height * resize_ratio
        else:
            # The resize's area is more portrait than the focus area.
            # The width is the constrained dimension.
            min_width = max(min_width, focus_height * resize_ratio)
            crop_width = min(max_width, max(min_width, focus_width))
            crop_height = crop_width / resize_ratio
    elif resize_width is not None:
        crop_width = max(min_width, focus_width)
        crop_height = max_height
    else:
        crop_width = max_width
        crop_height = max(min_height, focus_height)

    crop_focus_width_diff = crop_width - focus_width
    crop_focus_height_diff = crop_height - focus_height
    ideal_margin_left = math.ceil(crop_focus_width_diff / 2)
    ideal_margin_top = math.ceil(crop_focus_height_diff / 2)
    ideal_margin_right = crop_focus_width_diff - ideal_margin_left
    ideal_margin_bottom = crop_focus_height_diff - ideal_margin_top

    # Place the crop area centrally on top of the focus area.
    # At this point the crop area may still be out of bounds.
    crop_left = math.ceil(focus_left - ideal_margin_left)
    crop_top = math.ceil(focus_top - ideal_margin_top)
    crop_right = math.ceil(focus_right + ideal_margin_right)
    crop_bottom = math.ceil(focus_bottom + ideal_margin_bottom)

    # Ensure the crop area lies within the original image bounds.
    if crop_left < 0:
        crop_right -= crop_left
        crop_left = 0
    if crop_top < 0:
        crop_bottom -= crop_top
        crop_top = 0
    if crop_right > original_image.width:
        crop_left -= crop_right - original_image.width
        crop_right = original_image.width
    if crop_bottom > original_image.height:
        crop_top -= crop_bottom - original_image.height
        crop_bottom = original_image.height

    return original_image.crop((crop_left, crop_top, crop_right, crop_bottom)).resize(
        (resize_width or original_image.width, resize_height or original_image.height)
    )
