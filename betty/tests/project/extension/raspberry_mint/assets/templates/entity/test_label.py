from __future__ import annotations

from betty.ancestry.event import Event
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    entity = Event()
    expected = '<span lang="und" dir="auto">Unknown</span>'
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="entity/label.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id() -> None:
    entity = Event(id="E0")
    expected = f'<a href="/event/{entity.public_id}/index.html"><span lang="und" dir="auto">Unknown</span></a>'
    async with assert_template_file(
        data={
            "entity": entity,
        },
        extensions={RaspberryMint},
        template="entity/label.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    entity = Event(id="E0")
    expected = '<span lang="und" dir="auto">Unknown</span>'
    async with assert_template_file(
        data={
            "entity": entity,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label.html.j2",
    ) as (actual, _):
        assert actual == expected
