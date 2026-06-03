from pathlib import Path

from PIL import Image

from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entity.association import TemporaryToOneResolver
from betty.media_type import MediaType
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "file_references": [],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/media-gallery.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_public_file_references(
    assert_template_file: AssertTemplateFile, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"))
    file_reference = FileReference(TemporaryToOneResolver(), file)
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/media-gallery.html.j2",
    ) as (actual, _):
        assert file.public_id in actual


async def test_without_public_file_references(
    assert_template_file: AssertTemplateFile, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"), privacy=Privacy.PRIVATE)
    file_reference = FileReference(TemporaryToOneResolver(), file)
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/media-gallery.html.j2",
    ) as (actual, _):
        assert not actual
