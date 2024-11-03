from betty.ancestry.event import Event
from betty.date import Date
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class TestTemplate(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/page-list--event.html.j2"

    async def test_without_entities(self) -> None:
        async with self.assert_template_file(
            data={
                "page_resource": f"/{Event.plugin_id()}/index.html",
                "entity_type": Event,
                "entities": [],
            },
        ) as (actual, _):
            assert "I'm sorry" in actual

    async def test_with_public_entity(self) -> None:
        event = Event(id="E1", date=Date(1970, 1, 1))

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Event.plugin_id()}/index.html",
                "entity_type": Event,
                "entities": [event],
            },
        ) as (actual, _):
            assert event.id in actual

    async def test_with_private_entity(self) -> None:
        event = Event(id="E1", date=Date(1970, 1, 1), private=True)

        async with self.assert_template_file(
            data={
                "page_resource": f"/{Event.plugin_id()}/index.html",
                "entity_type": Event,
                "entities": [event],
            },
        ) as (actual, _):
            assert event.id not in actual
