from betty.ancestry.person import Person
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_entities() -> None:
    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Person.plugin_id()}/index.html",
            "entity_type": Person,
            "entities": [],
        },
        extensions={CottonCandy},
        template="entity/page-list--person.html.j2",
    ) as (actual, _):
        assert "I'm sorry" in actual


async def test_with_public_entity() -> None:
    person = Person(id="P1")

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Person.plugin_id()}/index.html",
            "entity_type": Person,
            "entities": [person],
        },
        extensions={CottonCandy},
        template="entity/page-list--person.html.j2",
    ) as (actual, _):
        assert person.id in actual


async def test_with_private_entity() -> None:
    person = Person(id="P1", private=True)

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Person.plugin_id()}/index.html",
            "entity_type": Person,
            "entities": [person],
        },
        extensions={CottonCandy},
        template="entity/page-list--person.html.j2",
    ) as (actual, _):
        assert person.id not in actual
