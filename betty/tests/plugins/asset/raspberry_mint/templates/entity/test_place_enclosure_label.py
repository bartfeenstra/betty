from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.place import Place
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": place,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected


async def test_with_encloser(assert_template_file: AssertTemplateFile) -> None:
    encloser_encloser_place = Place()
    encloser_place = Place()
    Enclosure(encloser_place, encloser_encloser_place)
    place = Place()
    Enclosure(place, encloser_place)
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>, <span lang="und" dir="auto">Place {encloser_place.id}</span>, <span lang="und" dir="auto">Place {encloser_encloser_place.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": place,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected


async def test_with_place_context(assert_template_file: AssertTemplateFile) -> None:
    encloser_place = Place()
    place = Place()
    Enclosure(place, encloser_place)
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": place,
            "place_context": encloser_place,
        },
        assets={RASPBERRY_MINT},
    ) as (actual, _):
        assert actual == expected
