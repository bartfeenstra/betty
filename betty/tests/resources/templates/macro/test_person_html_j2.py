from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import PersonName, Citation, Source
from betty.config import Configuration
from betty.functools import sync
from betty.site import Site


class TestNameLabel(TestCase):
    async def _render(self, **data):
        data.setdefault('embedded', False)
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                return await site.jinja2_environment.from_string('{% import \'macro/person.html.j2\' as personMacros %}{{ personMacros.nameLabel(name, embedded=embedded) }}').render_async(**data)

    @sync
    async def test_with_full_name(self):
        name = PersonName('Jane', 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        actual = await self._render(name=name)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_individual_name(self):
        name = PersonName('Jane')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
        actual = await self._render(name=name)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_affiliation_name(self):
        name = PersonName(None, 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
        actual = await self._render(name=name)
        self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        name = PersonName('Jane', 'Dough')
        source = Source()
        citation = Citation(source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        actual = await self._render(name=name, embedded=True)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_citation(self):
        name = PersonName('Jane')
        source = Source()
        citation = Citation(source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
        actual = await self._render(name=name)
        self.assertEqual(expected, actual)
