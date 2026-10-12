from __future__ import annotations

from typing import TYPE_CHECKING

from betty.entities.event import Event

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = Event()
    expected = '<span lang="und" dir="auto">Unknown</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label.html.j2", data={"entity": entity}
    ) as rendered:
        assert rendered == expected


async def test_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    entity = Event(id="my-first-event")
    expected = f'<a href="/event/{entity.id}/index.html"><span lang="und" dir="auto">Unknown</span></a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label.html.j2", data={"entity": entity}
    ) as rendered:
        assert rendered == expected


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    entity = Event(id="my-first-event")
    expected = '<span lang="und" dir="auto">Unknown</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label.html.j2", data={"entity": entity, "embedded": True}
    ) as rendered:
        assert rendered == expected
