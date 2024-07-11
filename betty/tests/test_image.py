from PIL import Image

from betty.image import resize_cover, resize_crop


class TestResizeCover:
    async def test_smaller_area(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (9, 9))
        assert actual.width == 9
        assert actual.height == 9

    async def test_narrower(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (9, None))
        assert actual.width == 9
        assert actual.height == 299

    async def test_lower(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (None, 9))
        assert actual.width == 199
        assert actual.height == 9

    async def test_bigger_area(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (999, 999))
        assert actual.width == 999
        assert actual.height == 999

    async def test_wider_area(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (999, 9))
        assert actual.width == 999
        assert actual.height == 9

    async def test_higher_area(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_cover(original, (9, 999))
        assert actual.width == 9
        assert actual.height == 999


class TestResizeCrop:
    async def test_smaller(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_crop(original, (9, 9))
        assert actual.width == 9
        assert actual.height == 9

    async def test_bigger(self) -> None:
        original = Image.new("1", (199, 299))
        actual = resize_crop(original, (999, 999))
        assert actual.width == 999
        assert actual.height == 999
