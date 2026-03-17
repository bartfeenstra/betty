from __future__ import annotations

from typing import TYPE_CHECKING

from betty.plugins.entity.event import Event
from betty.plugins.extension.raspberry_mint import RaspberryMint

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
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


async def test_with_persistent_id(assert_template_file: AssertTemplateFile) -> None:
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


async def test_embedded(assert_template_file: AssertTemplateFile) -> None:
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
