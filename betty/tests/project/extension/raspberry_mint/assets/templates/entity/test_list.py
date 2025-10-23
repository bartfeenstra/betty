from betty.ancestry.event import Event
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    expected = ""
    async with assert_template_file(
        data={
            "entities": [],
        },
        extensions={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_without_public_entities() -> None:
    entity = Event(private=True)
    expected = ""
    async with assert_template_file(
        data={
            "entities": [entity],
        },
        extensions={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_public_entities() -> None:
    entity = Event(id="E0")
    async with assert_template_file(
        data={
            "entities": [entity],
        },
        extensions={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert f"/event/{entity.public_id}/index.html" in actual
