from pathlib import Path

from PIL import Image

from betty.associations.to_one import Placeholder
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.media_type import MediaType
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/media-gallery.html.j2", data={"file_references": []}
    ) as rendered:
        assert rendered == ""


async def test_with_public_file_references(
    assert_raspberry_mint_jinja_file: AssertJinja, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"))
    file_reference = FileReference(Placeholder, file)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/media-gallery.html.j2",
        data={"file_references": [file_reference]},
    ) as rendered:
        assert file.id in rendered


async def test_without_public_file_references(
    assert_raspberry_mint_jinja_file: AssertJinja, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    file = File(image_path, media_type=MediaType("image/png"), privacy=Privacy.PRIVATE)
    file_reference = FileReference(Placeholder, file)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/media-gallery.html.j2",
        data={"file_references": [file_reference]},
    ) as rendered:
        assert not rendered
