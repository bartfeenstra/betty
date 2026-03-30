from pathlib import Path

from PIL import Image

from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.plugins.entity.file import File
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = File(Path(__file__))
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={RaspberryMint},
        template="search/result--file.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual


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
        assets={RaspberryMint},
        template="search/result--file.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
        assert "<img" in actual
