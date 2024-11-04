from betty.ancestry.enclosure import Enclosure
from betty.ancestry.place import Place
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateStringTestBase


class Test(TemplateStringTestBase):
    extensions = {RaspberryMint}

    async def test_minimal(self) -> None:
        place = Place()
        expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/place-enclosure-label.html.j2' import place_enclosure_label -%}{{ place_enclosure_label(place) }}",
            data={
                "place": place,
            },
        ) as (actual, _):
            assert actual == expected

    async def test_with_encloser(self) -> None:
        encloser_encloser_place = Place()
        encloser_place = Place()
        Enclosure(encloser_place, encloser_encloser_place)
        place = Place()
        Enclosure(place, encloser_place)
        expected = f'<span lang="und" dir="auto">Place {place.id}</span>, <span lang="und" dir="auto">Place {encloser_place.id}</span>, <span lang="und" dir="auto">Place {encloser_encloser_place.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/place-enclosure-label.html.j2' import place_enclosure_label -%}{{ place_enclosure_label(place) }}",
            data={
                "place": place,
            },
        ) as (actual, _):
            assert actual == expected

    async def test_with_place_context(self) -> None:
        encloser_place = Place()
        place = Place()
        Enclosure(place, encloser_place)
        expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/place-enclosure-label.html.j2' import place_enclosure_label -%}{{ place_enclosure_label(place, place_context) }}",
            data={
                "place": place,
                "place_context": encloser_place,
            },
        ) as (actual, _):
            assert actual == expected
