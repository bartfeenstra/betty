from betty.ancestry.source import Source
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page-list--source.html.j2"

    async def test_without_entities(self) -> None:
        async with self.assert_template_file(
            data={
                "page_resource": f"/{Source.plugin_id()}/index.html",
                "entity_type": Source,
                "entities": [],
            },
        ) as (actual, _):
            assert "I'm sorry" in actual

    async def test_with_public_entity(self) -> None:
        source = Source()

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Source.plugin_id()}/index.html",
                "entity_type": Source,
                "entities": [source],
            },
        ) as (actual, _):
            assert source.id in actual

    async def test_with_private_entity(self) -> None:
        source = Source(private=True)

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Source.plugin_id()}/index.html",
                "entity_type": Source,
                "entities": [source],
            },
        ) as (actual, _):
            assert source.id not in actual
