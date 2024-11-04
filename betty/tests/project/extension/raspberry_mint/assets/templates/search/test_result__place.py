from betty.ancestry.place import Place
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "search/result--place.html.j2"

    async def test_minimal(self) -> None:
        place = Place()
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert place.label.localize(DEFAULT_LOCALIZER) in actual
            assert place.id in actual
