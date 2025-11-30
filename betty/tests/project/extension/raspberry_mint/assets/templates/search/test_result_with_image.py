from pathlib import Path

from PIL import Image

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.model import EntityPlugin
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file
from betty.test_utils.locale.localizable import (
    DUMMY_LOCALIZABLE,
    _DummyCountableLocalizable,
)


@EntityPlugin(
    "dummy-has-file-references",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=_DummyCountableLocalizable(),
)
class DummyEntityWithFileReferences(HasFileReferences):
    pass


async def test_minimal() -> None:
    entity = DummyEntityWithFileReferences()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="search/result-with-image.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual


async def test_with_image(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    image = Image.new("1", (1, 1))
    image.save(image_path)
    entity = DummyEntityWithFileReferences()
    FileReference(entity, File(image_path, media_type=MediaType("image/png")))
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="search/result-with-image.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
        assert "<img" in actual
