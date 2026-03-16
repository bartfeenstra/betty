from __future__ import annotations

from betty.ancestry.name import Name
from betty.date import Date, DateRange
from betty.document import Document, EntityContexts
from betty.plugins.entity.place import Place
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id() -> None:
    place = Place(id="P0")
    expected = f'<a href="/place/{place.public_id}/index.html"><span lang="und" dir="auto">Place P0</span></a>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_name() -> None:
    place = Place(names=[Name("The Place")])
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "entity": place,
        },
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    place = Place(
        id="P0",
        names=[Name("The Place")],
    )
    expected = '<span lang="und" dir="auto">The Place</span>'
    async with assert_template_file(
        data={
            "entity": place,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_place_context() -> None:
    place = Place(id="P0")

    expected = '<span lang="und" dir="auto">Place P0</span>'
    async with assert_template_file(
        data={
            "entity": place,
            "document": Document(entity_contexts=EntityContexts(place)),
        },
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_date_context() -> None:
    place = Place(
        names=[
            Name(
                "The Old Place",
                date=DateRange(None, Date(1969, 12, 31)),
            ),
            Name(
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
        extensions={RaspberryMint},
        template="entity/label--place.html.j2",
    ) as (actual, _):
        assert actual == expected
