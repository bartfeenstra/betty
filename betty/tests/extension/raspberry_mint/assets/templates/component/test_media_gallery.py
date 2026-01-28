from pathlib import Path

from PIL import Image

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.extension.raspberry_mint import RaspberryMint
from betty.media_type import MediaType
from betty.model.association import TemporaryToOneResolver
from betty.privacy import Privacy
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "file_references": [],
        },
        extensions={RaspberryMint},
        template="component/media-gallery.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_public_file_references(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"))
    file_reference = FileReference(TemporaryToOneResolver(), file)
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        extensions={RaspberryMint},
        template="component/media-gallery.html.j2",
    ) as (actual, _):
        assert file.public_id in actual


async def test_without_public_file_references(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"), privacy=Privacy.PRIVATE)
    file_reference = FileReference(TemporaryToOneResolver(), file)
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        extensions={RaspberryMint},
        template="component/media-gallery.html.j2",
    ) as (actual, _):
        assert not actual
