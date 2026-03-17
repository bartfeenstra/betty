from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.place import Place
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.place_type.country import Country
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    place = Place()
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
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
        extensions={RaspberryMint},
        template="entity/summary--place.html.j2",
    ) as (actual, _):
        assert Country.plugin().label.localize(DEFAULT_LOCALIZER) in actual


async def test_with_encloser(assert_template_file: AssertTemplateFile) -> None:
    encloser_place = Place()
    place = Place()
    Enclosure(place, encloser_place)
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
        template="entity/summary--place.html.j2",
    ) as (actual, _):
        assert encloser_place.public_id in actual
