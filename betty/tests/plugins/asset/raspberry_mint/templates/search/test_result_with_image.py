from pathlib import Path

from PIL import Image

from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entity import EntityDefinition
from betty.entity.has_file_references import HasFileReferences
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.test_utils.conftest import AssertTemplateFile
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-file-references",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyEntityWithFileReferences(HasFileReferences):
    pass


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = DummyEntityWithFileReferences()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={RASPBERRY_MINT},
        template="search/result-with-image.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual


async def test_with_image(
    assert_template_file: AssertTemplateFile, tmp_path: Path
) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    entity = DummyEntityWithFileReferences()
    FileReference(entity, File(image_path, media_type=MediaType("image/png")))
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={RASPBERRY_MINT},
        template="search/result-with-image.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
        assert "<img" in actual
