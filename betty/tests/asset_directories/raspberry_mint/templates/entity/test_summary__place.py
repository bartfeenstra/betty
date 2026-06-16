from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.enclosure import Enclosure
from betty.entities.place import Place
from betty.locale.localize import default_localizer
from betty.place_types.country import Country
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    place = Place()
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={raspberry_mint},
        template="entity/summary--place.html.j2",
    ) as (actual, _):
        assert actual == '<div class="small"></div>'


async def test_with_non_unknown_place_type(
    assert_template_file: AssertTemplateFile,
) -> None:
    place = Place(place_type=Country())
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={raspberry_mint},
        template="entity/summary--place.html.j2",
    ) as (actual, _):
        assert Country.plugin().label.localize(default_localizer) in actual


async def test_with_encloser(assert_template_file: AssertTemplateFile) -> None:
    encloser_place = Place()
    place = Place()
    Enclosure(place, encloser_place)
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={raspberry_mint},
        template="entity/summary--place.html.j2",
    ) as (actual, _):
        assert encloser_place.id in actual
