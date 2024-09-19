from betty.ancestry import Place, Enclosure
from betty.ancestry.name import Name
from betty.extension.cotton_candy import CottonCandy
from betty.jinja2 import EntityContexts
from betty.test_utils.assets.templates import TemplateTestBase


class Test(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/meta--place.html.j2"

    async def test_without_enclosing_places(self) -> None:
        place = Place(
            id="P0",
            names=[Name("The Place")],
        )
        expected = '<div class="meta"></div>'
        async with self._render(
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
        Enclosure(encloses=place, enclosed_by=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(encloses=enclosing_place, enclosed_by=all_enclosing_place)
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und">The Enclosing Place</span></a></span>, <span><a href="/place/P2/index.html"><span lang="und">The All-enclosing Place</span></a></span></div>'
        async with self._render(
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
        Enclosure(encloses=place, enclosed_by=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(encloses=enclosing_place, enclosed_by=all_enclosing_place)
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und">The Enclosing Place</span></a></span></div>'
        async with self._render(
            data={
                "entity": place,
                "entity_contexts": EntityContexts(all_enclosing_place),
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
        Enclosure(encloses=place, enclosed_by=enclosing_place)
        all_enclosing_place = Place(
            id="P2",
            names=[Name("The All-enclosing Place")],
        )
        Enclosure(encloses=enclosing_place, enclosed_by=all_enclosing_place)
        unrelated_place = Place(
            id="P999",
            names=[Name("Far Far Away")],
        )
        expected = '<div class="meta">in <span><a href="/place/P1/index.html"><span lang="und">The Enclosing Place</span></a></span>, <span><a href="/place/P2/index.html"><span lang="und">The All-enclosing Place</span></a></span></div>'
        async with self._render(
            data={
                "entity": place,
                "entity_contexts": EntityContexts(unrelated_place),
            }
        ) as (actual, _):
            assert actual == expected
