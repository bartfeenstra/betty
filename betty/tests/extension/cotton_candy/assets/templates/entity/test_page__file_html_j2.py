from pathlib import Path

import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.locale import Str, DEFAULT_LOCALIZER
from betty.model import Entity
from betty.model.ancestry import File, HasFiles, HasPrivacy
from betty.tests import TemplateTester


class TemplateTestEntity(HasFiles, HasPrivacy, Entity):
    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Test")

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Tests")


class TestTemplate:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(
            new_temporary_app, template_file="entity/page--file.html.j2"
        )

    async def test_privacy(self, template_tester: TemplateTester) -> None:
        file = File(
            path=Path(),
            description="file description",
        )

        public_entity = TemplateTestEntity(None)
        file.entities.add(public_entity)

        private_entity = TemplateTestEntity(None)
        private_entity.private = True
        file.entities.add(private_entity)

        async with template_tester.render(
            data={
                "page_resource": file,
                "entity_type": File,
                "entity": file,
            },
        ) as actual:
            assert file.description is not None
            assert file.description in actual
            assert str(public_entity.label.localize(DEFAULT_LOCALIZER)) in actual

            assert str(private_entity.label.localize(DEFAULT_LOCALIZER)) not in actual
