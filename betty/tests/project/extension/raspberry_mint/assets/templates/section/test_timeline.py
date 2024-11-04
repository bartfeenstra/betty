from betty.ancestry.event import Event
from betty.date import Date
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "section/timeline.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "events": [],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual

    async def test_with_events(self) -> None:
        event = Event(id="E0", date=Date(1970, 1, 1))
        async with self.assert_template_file(
            data={
                "events": [event],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert event.id in actual
