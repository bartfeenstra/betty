from betty.ancestry.enclosure import Enclosure
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.jinja2 import EntityContexts
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {CottonCandy}
    template = "entity/meta--place.html.j2"

    async def test_without_enclosing_places(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        expected = '<div class="meta"></div>'
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_enclosing_place_without_place_context(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        enclosing_place = Place(
            id="P1",
            names=[Name("The Enclosing Place")],
        )
        Enclosure(enclosee=place, encloser=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(enclosee=enclosing_place, encloser=all_enclosing_place)
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und" dir="auto">The Enclosing Place</span></a></span>, <span><a href="/place/P2/index.html"><span lang="und" dir="auto">The All-enclosing Place</span></a></span></div>'
        async with self.assert_template_file(
            data={
                "entity": place,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_enclosing_place_with_matching_place_context(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        enclosing_place = Place(
            id="P1",
            names=[Name("The Enclosing Place")],
        )
        Enclosure(enclosee=place, encloser=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(enclosee=enclosing_place, encloser=all_enclosing_place)
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und" dir="auto">The Enclosing Place</span></a></span></div>'
        async with self.assert_template_file(
            data={
                "entity": place,
                "entity_contexts": await EntityContexts.new(all_enclosing_place),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_enclosing_place_with_non_matching_place_context(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        enclosing_place = Place(
            id="P1",
            names=[Name("The Enclosing Place")],
        )
        Enclosure(enclosee=place, encloser=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(enclosee=enclosing_place, encloser=all_enclosing_place)
        unrelated_place = Place(
            id="P999",
            names=[Name("Far Far Away")],
        )
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und" dir="auto">The Enclosing Place</span></a></span>, <span><a href="/place/P2/index.html"><span lang="und" dir="auto">The All-enclosing Place</span></a></span></div>'
        async with self.assert_template_file(
            data={
                "entity": place,
                "entity_contexts": await EntityContexts.new(unrelated_place),
            }
        ) as (actual, _):
            assert actual == expected
