from betty.ancestry.event import Event
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/list.html.j2"

    async def test_minimal(self) -> None:
        expected = ""
        async with self.assert_template_file(
            data={
                "entities": [],
            }
        ) as (actual, _):
            assert actual == expected

    async def test_without_public_entities(self) -> None:
        entity = Event(private=True)
        expected = ""
        async with self.assert_template_file(
            data={
                "entities": [entity],
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_public_entities(self) -> None:
        entity = Event(id="E0")
        async with self.assert_template_file(
            data={
                "entities": [entity],
            }
        ) as (actual, _):
            assert "/event/E0/index.html" in actual
