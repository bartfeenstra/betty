from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.plugins.entity.event import Event
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    expected = ""
    async with assert_template_file(
        data={
            "entities": [],
        },
        service_plugins={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_without_public_entities(
    assert_template_file: AssertTemplateFile,
) -> None:
    entity = Event(privacy=Privacy.PRIVATE)
    expected = ""
    async with assert_template_file(
        data={
            "entities": [entity],
        },
        service_plugins={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_public_entities(assert_template_file: AssertTemplateFile) -> None:
    entity = Event(id="E0")
    async with assert_template_file(
        data={
            "entities": [entity],
        },
        service_plugins={RaspberryMint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert f"/event/{entity.public_id}/index.html" in actual
