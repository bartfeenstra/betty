from pathlib import Path

from PIL import Image

from betty.associations.has_file_references import HasFileReferences
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entity import EntityDefinition
from betty.localizer import default_localizer
from betty.media_type import MediaType
from betty.test_utils.conftest import AssertJinja
from betty.test_utils.locale.localizable import dummy_countable_localizable


@EntityDefinition(
    "dummy-has-file-references",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class DummyEntityWithFileReferences(HasFileReferences):
    pass


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = DummyEntityWithFileReferences()
    async with assert_raspberry_mint_jinja_file(
        "search/result-with-image.html.j2", data={"entity": entity}
    ) as rendered:
        assert default_localizer.localize(entity.label) in rendered
        assert entity.id in rendered


async def test_with_image(
    assert_raspberry_mint_jinja_file: AssertJinja, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    entity = DummyEntityWithFileReferences()
    FileReference(entity, File(image_path, media_type=MediaType("image/png")))
    async with assert_raspberry_mint_jinja_file(
        "search/result-with-image.html.j2", data={"entity": entity}
    ) as rendered:
        assert default_localizer.localize(entity.label) in rendered
        assert entity.id in rendered
        assert "<img" in rendered
