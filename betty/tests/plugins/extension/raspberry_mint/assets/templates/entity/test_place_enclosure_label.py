from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.place import Place
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_string


async def test_minimal() -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_string(
        "{% include 'entity/place-enclosure-label.html.j2' %}",
        data={
            "place": place,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected


async def test_with_encloser() -> None:
    encloser_encloser_place = Place()
    encloser_place = Place()
    Enclosure(encloser_place, encloser_encloser_place)
    place = Place()
    Enclosure(place, encloser_place)
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>, <span lang="und" dir="auto">Place {encloser_place.id}</span>, <span lang="und" dir="auto">Place {encloser_encloser_place.id}</span>'
    async with assert_template_string(
        "{% include 'entity/place-enclosure-label.html.j2' %}",
        data={
            "place": place,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected


async def test_with_place_context() -> None:
    encloser_place = Place()
    place = Place()
    Enclosure(place, encloser_place)
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_string(
        "{% include 'entity/place-enclosure-label.html.j2' %}",
        data={
            "place": place,
            "place_context": encloser_place,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected
