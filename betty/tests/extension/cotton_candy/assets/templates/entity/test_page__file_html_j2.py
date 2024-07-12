from pathlib import Path

from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.localizable import _, Localizable
from betty.model.ancestry import File, HasFiles, HasPrivacy
from betty.tests import TemplateTestCase
from betty.tests.model.test___init__ import DummyEntity


class TemplateTestEntity(HasFiles, HasPrivacy, DummyEntity):
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Test")

    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Tests")


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = "entity/page--file.html.j2"

    async def test_privacy(self) -> None:
        file = File(
            path=Path(),
            description="file description",
        )

        public_entity = TemplateTestEntity(None)
        file.entities.add(public_entity)

        private_entity = TemplateTestEntity(None)
        private_entity.private = True
        file.entities.add(private_entity)

        async with self._render(
            data={
                "page_resource": file,
                "entity_type": File,
                "entity": file,
            },
        ) as (actual, _):
            assert file.description is not None
            assert file.description in actual
            assert str(public_entity.label.localize(DEFAULT_LOCALIZER)) in actual

            assert str(private_entity.label.localize(DEFAULT_LOCALIZER)) not in actual
