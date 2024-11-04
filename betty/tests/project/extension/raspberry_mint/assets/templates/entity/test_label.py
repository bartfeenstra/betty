from __future__ import annotations

from betty.ancestry.event import Event
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label.html.j2"

    async def test_minimal(self) -> None:
        entity = Event()
        expected = '<span lang="und" dir="auto">Unknown</span>'
        async with self.assert_template_file(
            data={
                "entity": entity,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_persistent_id(self) -> None:
        entity = Event(id="E0")
        expected = '<a href="/event/E0/index.html"><span lang="und" dir="auto">Unknown</span></a>'
        async with self.assert_template_file(
            data={
                "entity": entity,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        entity = Event(id="E0")
        expected = '<span lang="und" dir="auto">Unknown</span>'
        async with self.assert_template_file(
            data={
                "entity": entity,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected
