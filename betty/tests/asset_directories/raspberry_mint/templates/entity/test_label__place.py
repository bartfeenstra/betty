from __future__ import annotations

from typing import TYPE_CHECKING

from betty.date import Date, DateRange
from betty.document import Document, EntityContexts
from betty.entities.place import Place
from betty.entities.place_name import PlaceName

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateFile
from betty.asset_directories.raspberry_mint import RASPBERRY_MINT


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id(assert_template_file: AssertTemplateFile) -> None:
    place = Place(id="P0")
    expected = f'<a href="/place/{place.public_id}/index.html"><span lang="und" dir="auto">Place P0</span></a>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_name(assert_template_file: AssertTemplateFile) -> None:
    place = Place(names=[PlaceName("The Place")])
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded(assert_template_file: AssertTemplateFile) -> None:
    place = Place(
        id="P0",
        names=[PlaceName("The Place")],
    )
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "entity": place,
            "embedded": True,
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place_context(assert_template_file: AssertTemplateFile) -> None:
    place = Place(id="P0")

    expected = '<span lang="und" dir="auto">Place P0</span>'
    async with assert_template_file(
        data={
            "entity": place,
            "document": Document(entity_contexts=EntityContexts(place)),
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_date_context(assert_template_file: AssertTemplateFile) -> None:
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
    async with assert_template_file(
        data={
            "entity": place,
            "date_context": Date(1970, 1, 1),
        },
        assets={RASPBERRY_MINT},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected
