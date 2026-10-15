from pathlib import Path

from PIL import Image

from betty.entities.file import File
from betty.localizer import default_localizer
from betty.media_type import MediaType
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = File(__file__)
    async with assert_raspberry_mint_jinja_file(
        "search/result--file.html.j2", data={"entity": entity}
    ) as rendered:
        assert entity.label.localize(default_localizer) in rendered
        assert entity.id in rendered


async def test_with_image(
    assert_raspberry_mint_jinja_file: AssertJinja, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    entity = File(image_path, media_type=MediaType("image/png"))
    async with assert_raspberry_mint_jinja_file(
        "search/result--file.html.j2", data={"entity": entity}
    ) as rendered:
        assert entity.label.localize(default_localizer) in rendered
        assert entity.id in rendered
        assert "<img" in rendered
