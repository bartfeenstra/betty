from geopy import Point

from betty.ancestry.place import Place
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "places": [],
        },
        extensions={RaspberryMint, Maps},
        template="section/map.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_places() -> None:
    place = Place(coordinates=Point(1, 1))
    async with assert_template_file(
        data={
            "places": [place],
        },
        extensions={RaspberryMint, Maps},
        template="section/map.html.j2",
    ) as (actual, _):
        assert actual
