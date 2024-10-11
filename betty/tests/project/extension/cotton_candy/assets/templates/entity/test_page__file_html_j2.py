from pathlib import Path

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.privacy import HasPrivacy
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.test_utils.model import DummyEntity


class DummyHasFileReferencesHasPrivacyEntity(
    HasFileReferences, HasPrivacy, DummyEntity
):
    pass


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page--file.html.j2"

    async def test_privacy(self) -> None:
        file = File(
            path=Path(),
            description="file description",
        )

        public_referee = DummyHasFileReferencesHasPrivacyEntity()
        FileReference(public_referee, file)

        private_referee = DummyHasFileReferencesHasPrivacyEntity()
        private_referee.private = True
        FileReference(private_referee, file)

        async with self.assert_template_file(
            data={
                "page_resource": file,
                "entity_type": File,
                "entity": file,
            },
        ) as (actual, _):
            assert file.description
            assert file.description.localize(DEFAULT_LOCALIZER) in actual
            assert str(public_referee.label.localize(DEFAULT_LOCALIZER)) in actual

            assert str(private_referee.label.localize(DEFAULT_LOCALIZER)) not in actual
