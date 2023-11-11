from pathlib import Path

from betty.extension import CottonCandy
from betty.locale import Localizer
from betty.model import Entity
from betty.model.ancestry import File, HasFiles, HasMutablePrivacy
from betty.tests import TemplateTestCase


class TemplateTestEntity(HasFiles, HasMutablePrivacy, Entity):
    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return 'Test'

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return 'Tests'


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--file.html.j2'

    async def test_privacy(self) -> None:
        file = File(None, Path())
        file.description = 'file description'

        public_entity = TemplateTestEntity(None)
        file.entities.add(public_entity)

        private_entity = TemplateTestEntity(None)
        private_entity.private = True
        file.entities.add(private_entity)

        async with self._render(
            data={
                'page_resource': file,
                'entity_type': File,
                'entity': file,
            },
        ) as (actual, _):
            assert file.description in actual
            assert public_entity.label in actual

            assert private_entity.label not in actual
