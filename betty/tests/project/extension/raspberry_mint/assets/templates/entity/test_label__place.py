from __future__ import annotations


from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.date import DateRange, Date
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label--place.html.j2"

    async def test_minimal(self) -> None:
        place = Place()
        expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_persistent_id(self) -> None:
        place = Place(id="P0")
        expected = '<a href="/place/P0/index.html"><span lang="und" dir="auto">Place P0</span></a>'
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_name(self) -> None:
        place = Place(names=[Name("The Place")])
        expected = '<span lang="und" dir="auto">The Place</span>'
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        expected = '<span lang="und" dir="auto">The Place</span>'
        async with self.assert_template_file(
            data={
                "entity": place,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_place_context(self) -> None:
        place = Place(id="P0")

        expected = '<span lang="und" dir="auto">Place P0</span>'
        async with self.assert_template_file(
            data={
                "entity": place,
                "entity_contexts": await EntityContexts.new(place),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_date_context(self) -> None:
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
        async with self.assert_template_file(
            data={
                "entity": place,
                "date_context": Date(1970, 1, 1),
            }
        ) as (actual, _):
            assert actual == expected
