from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date, DateRange
from betty.document import Document, EntityContexts
from betty.entities.place import Place
from betty.entities.place_name import PlaceName

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2", data={"entity": place}
    ) as rendered:
        assert rendered == expected


async def test_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    place = Place(id="my-first-place")
    expected = f'<a href="/place/{place.id}/index.html"><span lang="und" dir="auto">Place my-first-place</span></a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2", data={"entity": place}
    ) as rendered:
        assert rendered == expected


async def test_with_name(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place(names=[PlaceName("The Place")])
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2", data={"entity": place}
    ) as rendered:
        assert rendered == expected


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place(
        id="my-first-place",
        names=[PlaceName("The Place")],
    )
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2", data={"entity": place, "embedded": True}
    ) as rendered:
        assert rendered == expected


async def test_with_place_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    place = Place(id="my-first-place")

    expected = '<span lang="und" dir="auto">Place my-first-place</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2",
        data={
            "entity": place,
            "document": Document(entity_contexts=EntityContexts(place)),
        },
    ) as rendered:
        assert rendered == expected


async def test_with_date_context(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    place = Place(
        names=[
            PlaceName(
                "The Old Place",
                date=DateRange(None, Date(1969, 12, 31)),
            ),
            PlaceName(
                "The New Place",
                date=DateRange(Date(1970, 1, 1)),
            ),
        ],
    )

    expected = '<span lang="und" dir="auto">The New Place</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--place.html.j2",
        data={"entity": place, "date_context": Date(1970, 1, 1)},
    ) as rendered:
        assert rendered == expected
