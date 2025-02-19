from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase
from betty.test_utils.model import DummyEntity


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "section/facts.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "facts": [],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_fact(self) -> None:
        fact = DummyEntity()
        async with self.assert_template_file(
            data={
                "facts": [fact],
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert fact.label.localize(DEFAULT_LOCALIZER) in actual
