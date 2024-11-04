from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/permalink.html.j2"

    async def test_minimal(self) -> None:
        url = "https://example.com/per/ma.link"
        async with self.assert_template_file(
            data={
                "url": url,
            }
        ) as (actual, _):
            assert "<a " in actual
            assert url in actual
