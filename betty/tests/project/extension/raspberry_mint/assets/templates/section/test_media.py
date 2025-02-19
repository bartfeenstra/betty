from pathlib import Path

from PIL import Image

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.media_type import MediaType
from betty.model.association import TemporaryToOneResolver
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "section/media.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "file_references": [],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_public_file_references(self, tmp_path: Path) -> None:
        image_path = tmp_path / "image.png"
        image = Image.new("1", (1, 1))
        image.save(image_path)
        file = File(image_path, media_type=MediaType("image/png"))
        file_reference = FileReference(TemporaryToOneResolver(), file)
        async with self.assert_template_file(
            data={
                "file_references": [file_reference],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert file.id in actual

    async def test_without_public_file_references(self, tmp_path: Path) -> None:
        image_path = tmp_path / "image.png"
        image = Image.new("1", (1, 1))
        image.save(image_path)
        file = File(image_path, media_type=MediaType("image/png"), private=True)
        file_reference = FileReference(TemporaryToOneResolver(), file)
        async with self.assert_template_file(
            data={
                "file_references": [file_reference],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual
