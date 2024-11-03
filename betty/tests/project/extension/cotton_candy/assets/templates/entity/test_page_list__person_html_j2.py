from betty.ancestry.person import Person
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page-list--person.html.j2"

    async def test_without_entities(self) -> None:
        async with self.assert_template_file(
            data={
                "page_resource": f"/{Person.plugin_id()}/index.html",
                "entity_type": Person,
                "entities": [],
            },
        ) as (actual, _):
            assert "I'm sorry" in actual

    async def test_with_public_entity(self) -> None:
        person = Person(id="P1")

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Person.plugin_id()}/index.html",
                "entity_type": Person,
                "entities": [person],
            },
        ) as (actual, _):
            assert person.id in actual

    async def test_with_private_entity(self) -> None:
        person = Person(id="P1", private=True)

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Person.plugin_id()}/index.html",
                "entity_type": Person,
                "entities": [person],
            },
        ) as (actual, _):
            assert person.id not in actual
