from pathlib import Path

from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model.ancestry import File, HasFileReferences, HasPrivacy, FileReference
from betty.test_utils.assets.templates import TemplateTestBase
from betty.tests.model.test___init__ import DummyEntity


class DummyHasFileReferencesHasPrivacyEntity(
    HasFileReferences, HasPrivacy, DummyEntity
):
    pass


class TestTemplate(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/page--file.html.j2"

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

        async with self._render(
            data={
                "page_resource": file,
                "entity_type": File,
                "entity": file,
            },
        ) as (actual, _):
            assert file.description is not None
            assert file.description in actual
            assert str(public_referee.label.localize(DEFAULT_LOCALIZER)) in actual

            assert str(private_referee.label.localize(DEFAULT_LOCALIZER)) not in actual
