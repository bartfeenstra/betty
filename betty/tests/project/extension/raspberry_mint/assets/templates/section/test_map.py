from geopy import Point

from betty.ancestry.place import Place
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint, Maps}
    template = "section/map.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "places": [],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_places(self) -> None:
        place = Place(coordinates=Point(1, 1))
        async with self.assert_template_file(
            data={
                "places": [place],
            }
        ) as (actual, _):
            assert actual
