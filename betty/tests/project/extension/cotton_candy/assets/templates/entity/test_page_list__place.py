from betty.ancestry.place import Place
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_entities() -> None:
    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Place.plugin_id()}/index.html",
            "entity_type": Place,
            "entities": [],
        },
        extensions={CottonCandy},
        template="entity/page-list--place.html.j2",
    ) as (actual, _):
        assert "I'm sorry" in actual


async def test_with_public_entity() -> None:
    place = Place()

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Place.plugin_id()}/index.html",
            "entity_type": Place,
            "entities": [place],
        },
        extensions={CottonCandy},
        template="entity/page-list--place.html.j2",
    ) as (actual, _):
        assert place.id in actual


async def test_with_private_entity() -> None:
    place = Place(private=True)

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Place.plugin_id()}/index.html",
            "entity_type": Place,
            "entities": [place],
        },
        extensions={CottonCandy},
        template="entity/page-list--place.html.j2",
    ) as (actual, _):
        assert place.id not in actual
