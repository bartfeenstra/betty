from betty.document import Document, EntityContexts
from betty.entities.enclosure import Enclosure
from betty.entities.place import Place
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/place-enclosure-label.html.j2", data={"place": place}
    ) as rendered:
        assert rendered == expected


async def test_with_enclosed_by(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    enclosed_by_enclosed_by = Place()
    enclosed_by = Place()
    Enclosure(enclosed_by=enclosed_by_enclosed_by, encloses=enclosed_by)
    encloses = Place()
    Enclosure(encloses=encloses, enclosed_by=enclosed_by)
    expected = f'<span lang="und" dir="auto">Place {encloses.id}</span>, <span lang="und" dir="auto">Place {enclosed_by.id}</span>, <span lang="und" dir="auto">Place {enclosed_by_enclosed_by.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/place-enclosure-label.html.j2", data={"place": encloses}
    ) as rendered:
        assert rendered == expected


async def test_with_place_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    enclosed_by = Place()
    encloses = Place()
    Enclosure(enclosed_by=enclosed_by, encloses=encloses)
    expected = f'<span lang="und" dir="auto">Place {encloses.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": encloses,
            "document": Document(entity_contexts=EntityContexts(enclosed_by)),
        },
    ) as rendered:
        assert rendered == expected
