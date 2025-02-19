from betty.ancestry.event import Event
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/summary--event.html.j2"

    async def test_minimal(self) -> None:
        event = Event()
        async with self.assert_template_file(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert actual
