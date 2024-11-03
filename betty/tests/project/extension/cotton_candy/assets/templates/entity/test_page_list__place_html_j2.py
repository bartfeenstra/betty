from betty.ancestry.place import Place
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page-list--place.html.j2"

    async def test_without_entities(self) -> None:
        async with self.assert_template_file(
            data={
                "page_resource": f"/{Place.plugin_id()}/index.html",
                "entity_type": Place,
                "entities": [],
            },
        ) as (actual, _):
            assert "I'm sorry" in actual

    async def test_with_public_entity(self) -> None:
        place = Place()

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Place.plugin_id()}/index.html",
                "entity_type": Place,
                "entities": [place],
            },
        ) as (actual, _):
            assert place.id in actual

    async def test_with_private_entity(self) -> None:
        place = Place(private=True)

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Place.plugin_id()}/index.html",
                "entity_type": Place,
                "entities": [place],
            },
        ) as (actual, _):
            assert place.id not in actual
