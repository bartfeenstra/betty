import pytest
from PIL import Image, ImageDraw

from betty.image import resize_cover, FocusArea, Size, Pixel


class TestResizeCover:
    @pytest.mark.parametrize(
        ("expected_focus", "cover_size", "original_focus"),
        [
            # The cover area is smaller than the image.
            (None, (500, 500), None),
            # The cover area is bigger than the image.
            (None, (2000, 2000), None),
            # The focus area is a portrait and the cover area a landscape.
            ((200, 0, 299, 199), (500, 200), (40, 0, 60, 100)),
            # The focus area is a landscape and the cover area a portrait.
            ((0, 200, 199, 299), (200, 500), (0, 40, 100, 60)),
            # A square focus area outside a square cover area.
            ((0, 0, 99, 99), (100, 100), (40, 40, 50, 50)),
            # A square focus area overlapping a square cover area.
            ((0, 0, 99, 99), (100, 100), (45, 45, 55, 55)),
            # A square focus area inside a square cover area.
            ((10, 10, 90, 90), (100, 100), (46, 46, 54, 54)),
            # The focus area is in the far top left corner.
            ((0, 0, 80, 80), (100, 100), (0, 0, 8, 8)),
            ((0, 0, 80, 80), (100, None), (0, 0, 8, 8)),
            # The focus area is in the far top right corner.
            ((20, 0, 99, 80), (100, 100), (92, 0, 100, 8)),
            ((20, 0, 99, 80), (100, None), (92, 0, 100, 8)),
            # The focus area is in the far bottom right corner.
            ((20, 20, 99, 99), (100, 100), (92, 92, 100, 100)),
            # The focus area is in the far bottom left corner.
            ((0, 20, 80, 99), (100, 100), (0, 92, 8, 100)),
        ],
    )
    async def test(
        self,
        expected_focus: tuple[Pixel, Pixel, Pixel, Pixel] | None,
        cover_size: Size,
        original_focus: FocusArea | None,
    ) -> None:
        original = Image.new("1", (1000, 1000))
        draw = ImageDraw.Draw(original)
        if original_focus:
            draw.rectangle(
                (
                    original_focus[0] * 10,
                    original_focus[1] * 10,
                    original_focus[2] * 10,
                    original_focus[3] * 10,
                ),
                fill=1,
                width=0,
            )
        actual = resize_cover(original, cover_size, focus=original_focus)
        cover_width, cover_height = cover_size

        if cover_width is not None:
            assert actual.width == cover_width
        if cover_height is not None:
            assert actual.height == cover_height

        if expected_focus is not None:
            # Assert the top-left pixel.
            assert actual.getpixel((expected_focus[0], expected_focus[1])) == 1
            # Assert the pixel left of the top-left pixel.
            if expected_focus[0] > 0:
                assert actual.getpixel((expected_focus[0] - 1, expected_focus[1])) == 0
            # Assert the pixel above the top-left pixel.
            if expected_focus[1] > 0:
                assert actual.getpixel((expected_focus[0], expected_focus[1] - 1)) == 0

            # Assert the top-right pixel.
            assert actual.getpixel((expected_focus[2], expected_focus[1])) == 1
            # Assert the pixel above the top-right pixel.
            if expected_focus[1] > 0:
                assert actual.getpixel((expected_focus[2], expected_focus[1] - 1)) == 0
            # Assert the pixel right of the top-right pixel.
            if expected_focus[2] < actual.width - 1:
                assert actual.getpixel((expected_focus[2] + 1, expected_focus[1])) == 0

            # Assert the bottom-right pixel.
            assert actual.getpixel((expected_focus[2], expected_focus[3])) == 1
            # Assert the pixel right of the bottom-right pixel.
            if expected_focus[2] < actual.width - 1:
                assert actual.getpixel((expected_focus[2] + 1, expected_focus[3])) == 0
            # Assert the pixel below the bottom-right pixel.
            if expected_focus[3] < actual.height - 1:
                assert actual.getpixel((expected_focus[2], expected_focus[3] + 1)) == 0

            # Assert the bottom-left pixel.
            assert actual.getpixel((expected_focus[0], expected_focus[3])) == 1
            # Assert the pixel below the bottom-left pixel.
            if expected_focus[3] < actual.height - 1:
                assert actual.getpixel((expected_focus[0], expected_focus[3] + 1)) == 0
            # Assert the pixel left of the bottom-left pixel.
            if expected_focus[0] > 0:
                assert actual.getpixel((expected_focus[0] - 1, expected_focus[3])) == 0
