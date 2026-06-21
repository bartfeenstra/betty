from pathlib import Path

from PIL import Image

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.file import File
from betty.localizer import default_localizer
from betty.media_type import MediaType
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = File(__file__)
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={raspberry_mint},
        template="search/result--file.html.j2",
    ) as (actual, _):
        assert entity.label.localize(default_localizer) in actual
        assert entity.id in actual


async def test_with_image(
    assert_template_file: AssertTemplateFile, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    entity = File(image_path, media_type=MediaType("image/png"))
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={raspberry_mint},
        template="search/result--file.html.j2",
    ) as (actual, _):
        assert entity.label.localize(default_localizer) in actual
        assert entity.id in actual
        assert "<img" in actual
