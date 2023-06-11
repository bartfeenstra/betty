"""
This is a partial, simplified fork of the abandoned python-resize-image package.

This module exists purely because existing Betty code depended on an abandoned package, and that code has not been
refactored yet.

New code MUST NOT use this module.
"""
import math

from PIL.Image import Image


def resize_crop(image: Image, size: tuple[int, int]) -> Image:
    img_format = image.format
    image = image.copy()
    old_size = image.size
    left = (old_size[0] - size[0]) / 2
    top = (old_size[1] - size[1]) / 2
    right = old_size[0] - left
    bottom = old_size[1] - top
    rect = [int(math.ceil(x)) for x in (left, top, right, bottom)]
    left, top, right, bottom = rect
    crop = image.crop((left, top, right, bottom))
    crop.format = img_format
    return crop


def resize_cover(image: Image, size: tuple[int, int]) -> Image:
    img_format = image.format
    img = image.copy()
    img_size = img.size
    ratio = max(size[0] / img_size[0], size[1] / img_size[1])
    new_size = [
        int(math.ceil(img_size[0] * ratio)),
        int(math.ceil(img_size[1] * ratio))
    ]
    img = img.resize((new_size[0], new_size[1]))
    img = resize_crop(img, size)
    img.format = img_format
    return img


def resize_width(image: Image, width: int) -> Image:
    img_format = image.format
    img = image.copy()
    img_size = img.size
    # If the origial image has already the good width, return it
    # fix issue #16
    if img_size[0] == width:
        return image
    new_height = int(math.ceil((width / img_size[0]) * img_size[1]))
    img.thumbnail((width, new_height))
    img.format = img_format
    return img


def resize_height(image: Image, height: int) -> Image:
    img_format = image.format
    img = image.copy()
    img_size = img.size
    # If the origial image has already the good height, return it
    # fix issue #16
    if img_size[1] == height:
        return image
    new_width = int(math.ceil((height / img_size[1]) * img_size[0]))
    img.thumbnail((new_width, height))
    img.format = img_format
    return img
