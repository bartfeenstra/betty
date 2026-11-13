from betty.entities.event import Event
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    expected = ""
    async with assert_raspberry_mint_jinja_file(
        "entity/list.html.j2", data={"entities": []}
    ) as rendered:
        assert rendered == expected


async def test_without_public_entities(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    entity = Event(privacy=Privacy.PRIVATE)
    expected = ""
    async with assert_raspberry_mint_jinja_file(
        "entity/list.html.j2", data={"entities": [entity]}
    ) as rendered:
        assert rendered == expected


async def test_with_public_entities(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    entity = Event(id="my-first-event")
    async with assert_raspberry_mint_jinja_file(
        "entity/list.html.j2", data={"entities": [entity]}
    ) as rendered:
        assert f"/event/{entity.id}/index.html" in rendered
