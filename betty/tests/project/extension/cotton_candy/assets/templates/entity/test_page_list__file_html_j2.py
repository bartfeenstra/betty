from pathlib import Path

from betty.ancestry.file import File
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page-list--file.html.j2"

    async def test_without_entities(self) -> None:
        async with self.assert_template_file(
            data={
                "page_resource": f"/{File.plugin_id()}/index.html",
                "entity_type": File,
                "entities": [],
            },
        ) as (actual, _):
            assert "I'm sorry" in actual

    async def test_with_public_entity(self) -> None:
        file = File(path=Path())

        async with self.assert_template_file(
            data={
                "page_resource": f"/{File.plugin_id()}/index.html",
                "entity_type": File,
                "entities": [file],
            },
        ) as (actual, _):
            assert file.id in actual

    async def test_with_private_entity(self) -> None:
        file = File(path=Path(), private=True)

        async with self.assert_template_file(
            data={
                "page_resource": f"/{File.plugin_id()}/index.html",
                "entity_type": File,
                "entities": [file],
            },
        ) as (actual, _):
            assert file.id not in actual
