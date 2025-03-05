from betty.ancestry.event import Event
from betty.date import Date
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_entities() -> None:
    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Event.plugin_id()}/index.html",
            "entity_type": Event,
            "entities": [],
        },
        extensions={CottonCandy},
        template="entity/page-list--event.html.j2",
    ) as (actual, _):
        assert "I'm sorry" in actual


async def test_with_public_entity() -> None:
    event = Event(id="E1", date=Date(1970, 1, 1))

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Event.plugin_id()}/index.html",
            "entity_type": Event,
            "entities": [event],
        },
        extensions={CottonCandy},
        template="entity/page-list--event.html.j2",
    ) as (actual, _):
        assert event.id in actual


async def test_with_private_entity() -> None:
    event = Event(id="E1", date=Date(1970, 1, 1), private=True)

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Event.plugin_id()}/index.html",
            "entity_type": Event,
            "entities": [event],
        },
        extensions={CottonCandy},
        template="entity/page-list--event.html.j2",
    ) as (actual, _):
        assert event.id not in actual
