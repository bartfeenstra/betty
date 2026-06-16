from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.event import Event
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    expected = ""
    async with assert_template_file(
        data={
            "entities": [],
        },
        assets={raspberry_mint},
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
        assets={raspberry_mint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_public_entities(assert_template_file: AssertTemplateFile) -> None:
    entity = Event(id="my-first-event")
    async with assert_template_file(
        data={
            "entities": [entity],
        },
        assets={raspberry_mint},
        template="entity/list.html.j2",
    ) as (actual, _):
        assert f"/event/{entity.id}/index.html" in actual
