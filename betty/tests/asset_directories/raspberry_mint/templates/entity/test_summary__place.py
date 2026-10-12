from betty.entities.enclosure import Enclosure
from betty.entities.place import Place
from betty.localizer import default_localizer
from betty.place_types.country import Country
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place()
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--place.html.j2", data={"entity": place}
    ) as rendered:
        assert rendered == '<div class="small"></div>'


async def test_with_non_unknown_place_type(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    place = Place(place_type=Country())
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--place.html.j2", data={"entity": place}
    ) as rendered:
        assert Country.definition.label.localize(default_localizer) in rendered


async def test_with_enclosed_by(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    enclosed_by = Place()
    encloses = Place()
    Enclosure(enclosed_by=enclosed_by, encloses=encloses)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--place.html.j2", data={"entity": encloses}
    ) as rendered:
        assert enclosed_by.id in rendered
